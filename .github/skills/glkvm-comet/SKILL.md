---
name: glkvm-comet
description: 'Operate and test a board through the GL.iNet GL-RM1PE Comet PoE KVM at 192.168.0.77. Use when viewing live board video, taking KVM screenshots, clicking or moving the remote mouse, typing text, sending keyboard shortcuts, or visually validating boot and UI behavior.'
argument-hint: 'Describe the board interaction or test to perform'
---

# GLKVM Comet Board Control

Use [`kvmctl.py`](../../../glkvm-comet/kvmctl.py) to observe and control the
board connected to the lab's GL.iNet Comet KVM.

## Credentials

- Never put a password, token, cookie, screenshot containing a secret, or
  credential-bearing command in the repository.
- The controller reads `GLKVM_PASSWORD` or securely prompts on a TTY. Tokens
  live only in the process that uses them.
- If access is not already available, ask the user to enter the password
  directly in their terminal. Do not ask them to send it through chat.
- A convenient terminal-only setup is `read -s GLKVM_PASSWORD; export
  GLKVM_PASSWORD; echo`. The password is not echoed or written to shell
  history. The user must run this themselves.

## Working Directory

```bash
cd "$(git rev-parse --show-toplevel)/glkvm-comet"
```

The default endpoint is `192.168.0.77` and the default user is `admin`.
Override them with `GLKVM_HOST`, `GLKVM_USER`, `--host`, or `--user`.

## Observe First

Capture a fresh frame before acting, and view it with the image-viewing tool:

```bash
python kvmctl.py screenshot /tmp/glkvm.png
```

Screenshots preserve the board's native dimensions. The streamer emits JPEG;
the output file extension selects the saved format, so `.png` is re-encoded to
a real PNG while `.jpg` is stored verbatim. Prefer `.png` when the image will
be passed to an image-viewing tool, since some reject a file whose contents do
not match its extension. Keep routine captures in `/tmp`; do not add them to
git. The command retries transient capture failures three times; use
`--attempts N` to adjust this. Re-capture after each interaction so decisions
are based on visible results rather than assumed state.

## Mouse

Coordinates are pixels from the exact screenshot passed with `--image`.

```bash
python kvmctl.py move 640 360 --image /tmp/glkvm.png
python kvmctl.py click 640 360 --image /tmp/glkvm.png
python kvmctl.py click 640 360 --image /tmp/glkvm.png --button right
python kvmctl.py scroll -5
```

Always use the latest screenshot as the coordinate reference. After a click,
wait briefly when the board is loading, then take another screenshot.

## Keyboard

Use `type` for ordinary text:

```bash
python kvmctl.py type 'console command or text'
python kvmctl.py type 'text for a UK layout' --keymap en-gb
```

Use `key` for special keys and shortcuts. Names are browser
`KeyboardEvent.code` values such as `Enter`, `Escape`, `Tab`, `ArrowDown`,
`ControlLeft`, `AltLeft`, `Delete`, and `KeyA` through `KeyZ`.

```bash
python kvmctl.py key Enter
python kvmctl.py key ControlLeft AltLeft Delete
python kvmctl.py key ControlLeft KeyC
```

The controller presses keys in argument order and releases them in reverse
order, so multiple names form one shortcut.

## Interaction Loop

1. Capture and inspect `/tmp/glkvm.png`.
2. Choose one small mouse or keyboard action based on visible state.
3. Send the action.
4. Capture a new screenshot and verify the result.
5. Continue until the requested board test is complete.

Normal operation of the connected board is allowed. Do not alter the KVM's
own network, TLS, account, firmware, factory-reset, or USB-mode settings unless
the user specifically requests that administrative change; losing the KVM
control path prevents further testing.

## Troubleshooting

- `HTTP 401` or `HTTP 403`: obtain a fresh password entry from the user.
- `HTTP 4xx/5xx` from an HID endpoint: confirm the KVM is reachable and its
  mouse/keyboard USB functions are enabled, then retry once.
- Mouse lands incorrectly: take a fresh screenshot and use coordinates from
  that image; do not reuse coordinates after resolution changes.
- Text uses the wrong symbols: select the board's actual keymap with
  `--keymap`, commonly `en-us` or `en-gb`.
- No HDMI signal or repeated `HTTP 503`: keyboard or mouse input may wake the
  board; send a harmless key and capture again.

Read [`AGENTS.md`](../../../glkvm-comet/AGENTS.md) for implementation and
protocol details when changing the controller itself.