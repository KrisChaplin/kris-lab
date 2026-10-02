# Agent Guide - GL.iNet Comet KVM

This folder controls the GL.iNet GL-RM1PE Comet PoE KVM at
`192.168.0.77`. Read the top-level `AGENTS.md` for repository conventions.

## Rules

- Never store a password, auth token, cookie, or captured secret in git.
- Keep screenshots and other transient captures under `/tmp` by default.
- Observe with a fresh screenshot before and after every input action.
- Do not change the KVM appliance's network, TLS, account, firmware,
  factory-reset, or USB-mode settings unless explicitly requested.
- Use `python kvmctl.py --help` as the command reference.

## Protocol Facts

- HTTPS and WSS use the appliance's private certificate; the controller
  intentionally disables certificate verification for this fixed LAN host.
- Login is `POST /api/auth/login` with multipart fields `user` and `passwd`.
- Authenticated HTTP requests carry the transient token in the `token` header.
- Mouse and keyboard input use acknowledged `POST /api/hid/events/*` requests.
- Screenshots use `POST /api/streamer/snapshot`.
- Bulk text uses `POST /api/hid/print?limit=0&keymap=<layout>`.

See `docs/INDEX.md` for focused documentation.