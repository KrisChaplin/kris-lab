# ETH008-B Control Sets

The board offers three independent ways to switch relays: a binary TCP
command set, an ASCII string command, and HTTP GET requests. All three
act on the same relays and are visible to each other.

Everything below was verified against the lab board (module id 19,
hardware v2, firmware v28) at `192.168.0.200`.

## Relay numbering

Relays are numbered 1–8. The `0x24` status byte uses **bit 0 for relay 1**:

| Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-----|---|---|---|---|---|---|---|---|
| Relay | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 |

`0x0d` = `0b00001101` = relays 1, 3 and 4 energised.

## TCP binary command set (port 17494)

This is the preferred interface: every command is acknowledged. All bytes
of a command must be sent in a single write.

| Cmd | Request | Reply | Meaning |
|-----|---------|-------|---------|
| `0x10` | 1 byte | 3 bytes | Module info: id, hardware version, firmware version |
| `0x20` | `0x20 <relay> <units>` | 1 byte | Digital Active — energise |
| `0x21` | `0x21 <relay> <units>` | 1 byte | Digital Inactive — de-energise |
| `0x23` | `0x23 <mask>` | 1 byte | Set all eight outputs from a bitmask |
| `0x24` | 1 byte | 1 byte | Get outputs bitmask |
| `0x25` | 1 byte | — | Get inputs; **no reply on ETH008-B, it has no inputs** |
| `0x3A` | ASCII string | — | ASCII command, see below |
| `0x77` | 1 byte | 6 bytes | MAC address |
| `0x78` | 1 byte | 1 byte | Supply volts × 10 |
| `0x79` | `0x79 <password>` | 1 byte | TCP/IP password entry: `1` ok, `2` fail |
| `0x7A` | 1 byte | 1 byte | Unlock time: `0` locked, `1`–`30` seconds left, `255` no password set |
| `0x7B` | 1 byte | 1 byte | Log out, re-enabling password protection |

`<units>` is the pulse duration in 100 ms steps, 1–255 (0.1 s to 25.5 s),
or `0` for a permanent change.

`0x20` and `0x21` acknowledge `0` for success and `1` for failure. Relay
numbers `0` and `9` both return `1`.

### Pulse direction

A non-zero `<units>` always means "hold the commanded state for this long,
then return to the opposite state":

- `0x20 08 14` — relay 8 on for 2.0 s, then off.
- `0x21 08 14` — relay 8 off for 2.0 s, then **on**.

So `0x21` with a pulse time is a momentary *break*, useful for power
cycling a load that is normally energised.

### Example session

```
-> 10              <- 13 02 1c      module 19, hw 2, fw 28
-> 24              <- 0d            relays 1, 3, 4 on
-> 20 08 00        <- 00            relay 8 on, permanent
-> 24              <- 8d
-> 21 08 00        <- 00            relay 8 off
-> 23 0d           <- 00            restore the original mask
-> 78              <- 77            11.9 V
```

### Password

If the TCP/IP password is enabled in `config.htm`, send `0x79` followed by
the ASCII password before any switching command:

```
-> 79 61 70 70 6c 65    (0x79 + "apple")    <- 01
```

Authorisation lapses after 30 seconds of idle time, and each authorised
command resets that timer. `0x7B` ends it immediately.

## ASCII command set

Send the string over the same TCP port. The leading `:` is command `0x3A`.

```
:DOA,<relay>,<units>[,<password>]     digital output active
:DOI,<relay>,<units>[,<password>]     digital output inactive
```

```
:DOA,1,50      relay 1 on for 5 seconds
:DOI,2,30      relay 2 off for 3 seconds, then back on
:DOA,1,0       relay 1 on, permanent
```

Trailing whitespace, `\r\n`, a trailing comma, and a password field are
all tolerated when no password is configured.

**There is no acknowledgement.** Re-read `0x24` if you need confirmation.
Prefer the binary set.

## HTTP command set

No authentication is currently required on this board.

| Request | Effect |
|---------|--------|
| `GET /status.xml` | XML with `relay1`…`relay8` and `volts` |
| `GET /io.cgi?relay=<n>` | Toggle relay *n* (what the web page uses) |
| `GET /io.cgi?DOA<n>=<units>` | Energise relay *n*, `units` × 100 ms, `0` = permanent |
| `GET /io.cgi?DOI<n>=<units>` | De-energise relay *n*, `units` × 100 ms, `0` = permanent |

Credentials can be supplied inline if HTTP authentication is enabled:
`http://admin:password@192.168.0.200/io.cgi?DOA1=10`.

### Response format

`io.cgi` replies with a line such as:

```
relays 10110001
```

This is ordered **relay 1 first** (LSB first), so the example means relays
1, 3, 4 and 8 are energised — equivalent to mask `0x8d`. Note this is the
reverse of the `0x24` mask written as a binary literal, and the reverse of
the web page's right-to-left 8…1 bullet layout.

`status.xml` looks like:

```xml
<response>
<relay1>1</relay1>
...
<relay8>0</relay8>
<volts>12.0</volts>
</response>
```

The web page polls `status.xml`, so state changed over TCP appears in the
browser within about half a second.
