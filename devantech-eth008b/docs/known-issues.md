# ETH008-B Known Issues

Observed on the lab board: module id 19, hardware v2, firmware v28.

## Closing the socket too early silently drops the command

Sending a switching command and closing the socket without reading the
acknowledgement loses the command entirely — no error, no state change.

```
send 0x20 0x08 0x00, close immediately   -> relay unchanged
send 0x20 0x08 0x00, close after 50 ms   -> relay energised
send 0x20 0x08 0x00, read ack, close     -> relay energised
```

**Workaround:** always read the acknowledgement byte. `ETH008B._command`
does this, and keeps the socket open across commands. Never use a
fire-and-forget helper such as `nc -w0` or a bare `socket.sendall` plus
`close()`.

## Only five concurrent TCP connections

The sixth connection is *accepted* at the TCP level but never answered,
so it fails as a read timeout rather than a connection refusal. The error
is easy to misread as "board is down".

**Workaround:** reuse one connection. If you see unexplained read
timeouts, check for leaked sockets from earlier scripts before assuming a
hardware fault.

## ASCII commands return nothing

`:DOA,<n>,<t>` and `:DOI,<n>,<t>` work, but the board sends no reply.
A malformed string is indistinguishable from a successful one.

**Workaround:** use the binary command set, or re-read `0x24` afterwards.

## `0x21` with a pulse time re-energises the relay

`0x21 <relay> <units>` de-energises for `units` × 100 ms and then turns
the relay **back on**. It is not "turn off after a delay". Code that
expects a delayed-off will leave the relay energised.

**Workaround:** for a permanent off, use `units = 0`.

## Relay state is lost on power cycle

"Latched Outputs" is disabled on this board, so all relays come up
de-energised after a power interruption. Anything that needs a known
state must re-apply it at start-up.

## Inputs commands hang

`0x25` (get inputs) and `0x30` (get analogue) return no data on the
ETH008-B — it has no inputs. A client that waits for a reply blocks until
its socket timeout.

## Bit-order confusion between interfaces

Three different orderings are in play:

| Source | Example for relays 1, 3, 4, 8 on |
|--------|----------------------------------|
| `0x24` bitmask | `0x8d` |
| `io.cgi` text reply | `relays 10110001` (relay 1 first) |
| Web page bullets | laid out 8 … 1, left to right |

Reading `io.cgi`'s string as a binary literal gives `0xb1`, not `0x8d`.
Parse it character by character, or just use `0x24`.

## Reported voltage is rounded in the browser

The web page showed `12.0` V while `0x78` returned `119` (11.9 V). Use
`0x78` when the value matters.
