#!/usr/bin/env python3
"""Control a GL.iNet Comet KVM without storing credentials."""

from __future__ import annotations

import argparse
import base64
import getpass
import io
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from PIL import Image


DEFAULT_HOST = "192.168.0.77"
DEFAULT_USER = "admin"


class KVMError(RuntimeError):
    pass


class CometKVM:
    def __init__(self, host: str, user: str, password: str) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.token: str | None = None
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def login(self) -> None:
        boundary = uuid.uuid4().hex
        body = bytearray()
        for name, value in {"user": self.user, "passwd": self.password}.items():
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
            )
            body.extend(value.encode())
            body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode())
        result = self._request(
            "/api/auth/login",
            data=bytes(body),
            content_type=f"multipart/form-data; boundary={boundary}",
            authenticated=False,
        )
        try:
            self.token = result["token"]
        except (KeyError, TypeError) as exc:
            raise KVMError("Login response did not contain a token") from exc

    def request(
        self,
        path: str,
        *,
        data: bytes | None = None,
        params: dict[str, object] | None = None,
        content_type: str | None = None,
    ) -> Any:
        if self.token is None:
            self.login()
        return self._request(
            path, data=data, params=params, content_type=content_type
        )

    def _request(
        self,
        path: str,
        *,
        data: bytes | None = None,
        params: dict[str, object] | None = None,
        content_type: str | None = None,
        authenticated: bool = True,
    ) -> Any:
        url = f"https://{self.host}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {"Accept": "application/json"}
        if authenticated:
            if self.token is None:
                raise KVMError("Authentication token is unavailable")
            headers["token"] = self.token
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(
                request, context=self.ssl_context, timeout=15
            ) as response:
                payload = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise KVMError(f"HTTP {exc.code} from {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise KVMError(f"Cannot reach {url}: {exc.reason}") from exc

        try:
            decoded = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return payload
        if not decoded.get("ok"):
            raise KVMError(f"GLKVM rejected {path}: {decoded.get('result', decoded)}")
        return decoded.get("result")

    def screenshot(self, output: Path, attempts: int = 3) -> None:
        for attempt in range(attempts):
            try:
                result = self.request("/api/streamer/snapshot", data=b"")
                break
            except KVMError as exc:
                if attempt == attempts - 1 or "HTTP 503" not in str(exc):
                    raise
        image_data = self._find_image_data(result)
        output.parent.mkdir(parents=True, exist_ok=True)
        _write_image(image_data, output)

    @staticmethod
    def _find_image_data(result: Any) -> bytes:
        candidates: list[Any] = [result]
        if isinstance(result, dict):
            candidates.extend(result.values())
        for candidate in candidates:
            if isinstance(candidate, bytes):
                return candidate
            if not isinstance(candidate, str):
                continue
            encoded = candidate.split(",", 1)[-1]
            try:
                data = base64.b64decode(encoded, validate=True)
            except ValueError:
                continue
            if data.startswith((b"\x89PNG", b"\xff\xd8\xff")):
                return data
        raise KVMError("Snapshot response did not contain a PNG or JPEG image")

    def type_text(self, text: str, keymap: str) -> None:
        self.request(
            "/api/hid/print",
            data=text.encode(),
            params={"limit": 0, "keymap": keymap},
            content_type="text/plain; charset=utf-8",
        )

    def press_keys(self, keys: list[str]) -> None:
        for key in keys:
            self.request(
                "/api/hid/events/send_key",
                data=b"",
                params={"key": key, "state": "true"},
            )
        for key in reversed(keys):
            self.request(
                "/api/hid/events/send_key",
                data=b"",
                params={"key": key, "state": "false"},
            )

    @staticmethod
    def mouse_coordinates(x: int, y: int, image: Path) -> tuple[int, int]:
        with Image.open(image) as screenshot:
            width, height = screenshot.size
        if not 0 <= x < width or not 0 <= y < height:
            raise KVMError(f"Coordinates must be inside {width}x{height}")
        target_x = round(x / max(width - 1, 1) * 65535 - 32768)
        target_y = round(y / max(height - 1, 1) * 65535 - 32768)
        return target_x, target_y

    def move_mouse(self, x: int, y: int, image: Path) -> None:
        target_x, target_y = self.mouse_coordinates(x, y, image)
        self.request(
            "/api/hid/events/send_mouse_move",
            data=b"",
            params={"to_x": target_x, "to_y": target_y},
        )

    def click_mouse(self, x: int, y: int, image: Path, button: str) -> None:
        self.move_mouse(x, y, image)
        for state in ("true", "false"):
            self.request(
                "/api/hid/events/send_mouse_button",
                data=b"",
                params={"button": button, "state": state},
            )

    def scroll_mouse(self, horizontal: int, vertical: int) -> None:
        self.request(
            "/api/hid/events/send_mouse_wheel",
            data=b"",
            params={"delta_x": horizontal, "delta_y": vertical},
        )


def _write_image(data: bytes, output: Path) -> None:
    """Save a capture, re-encoding when the suffix asks for another format.

    The streamer always returns JPEG, so writing the bytes verbatim to the
    documented ``.png`` path produces a file whose extension contradicts its
    contents, which breaks viewers that trust the extension.
    """
    with Image.open(io.BytesIO(data)) as image:
        source_format = (image.format or "").upper()
        target_format = Image.registered_extensions().get(output.suffix.lower())
        if target_format is None or target_format == source_format:
            output.write_bytes(data)
            return
        if target_format in {"JPEG", "JPEG2000"} and image.mode not in {"RGB", "L"}:
            image = image.convert("RGB")
        image.save(output, target_format)


def password_from_environment() -> str:
    password = os.environ.get("GLKVM_PASSWORD")
    if password is not None:
        return password
    if not sys.stdin.isatty():
        raise KVMError("Set GLKVM_PASSWORD or run from an interactive terminal")
    return getpass.getpass("GLKVM password: ")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("GLKVM_HOST", DEFAULT_HOST))
    parser.add_argument("--user", default=os.environ.get("GLKVM_USER", DEFAULT_USER))
    subparsers = parser.add_subparsers(dest="command", required=True)

    screenshot = subparsers.add_parser("screenshot", help="capture the KVM video")
    screenshot.add_argument("output", type=Path)
    screenshot.add_argument("--attempts", type=int, default=3)

    type_text = subparsers.add_parser("type", help="type text on the board")
    type_text.add_argument("text")
    type_text.add_argument("--keymap", default="en-us")

    key = subparsers.add_parser("key", help="press a named KeyboardEvent.code key")
    key.add_argument("keys", nargs="+", help="for example ControlLeft KeyC")

    move = subparsers.add_parser("move", help="move to screenshot pixel coordinates")
    move.add_argument("x", type=int)
    move.add_argument("y", type=int)
    move.add_argument("--image", type=Path, required=True)

    click = subparsers.add_parser("click", help="click screenshot pixel coordinates")
    click.add_argument("x", type=int)
    click.add_argument("y", type=int)
    click.add_argument("--image", type=Path, required=True)
    click.add_argument("--button", choices=("left", "middle", "right"), default="left")

    scroll = subparsers.add_parser("scroll", help="scroll horizontally and vertically")
    scroll.add_argument("vertical", type=int)
    scroll.add_argument("--horizontal", type=int, default=0)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        client = CometKVM(args.host, args.user, password_from_environment())
        if args.command == "screenshot":
            client.screenshot(args.output, args.attempts)
            print(args.output)
        elif args.command == "type":
            client.type_text(args.text, args.keymap)
        elif args.command == "key":
            client.press_keys(args.keys)
        elif args.command == "move":
            client.move_mouse(args.x, args.y, args.image)
        elif args.command == "click":
            client.click_mouse(args.x, args.y, args.image, args.button)
        elif args.command == "scroll":
            horizontal = max(-127, min(127, args.horizontal))
            vertical = max(-127, min(127, args.vertical))
            client.scroll_mouse(horizontal, vertical)
        return 0
    except (KVMError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())