# ETH008-B Configuration

All configuration is done through the board's web pages. **Changes do not
take effect until the module resets** — the forms offer "Save and Exit"
and "Save and Reset".

> Do not change any of this on the lab board unless explicitly asked. The
> address and the disabled authentication are relied on by other tooling,
> and a reset drops every open TCP connection.

## Module settings — `config.htm`

| Field | Purpose | Lab board |
|-------|---------|-----------|
| Hostname | mDNS/DHCP hostname | `ETH008` |
| MAC address | Read-only identifier | `44:b7:d0:a5:79:e2` |
| Enable DHCP | Lease an address instead of using the static fields | enabled |
| IP / Subnet / Gateway / DNS | Static settings, editable only with DHCP off | `192.168.0.200` / `255.255.255.0` / `192.168.0.1` |
| Port | TCP command port | `17494` |
| TCP/IP Password | Require `0x79` before switching commands | disabled |
| HTTP Authentication | Require a username and password for the web pages | disabled |
| Username / Password | Credentials for HTTP authentication | vendor defaults `admin` / `password` |
| Latched Outputs | Save permanent (non-pulsed) output states and restore them after power loss | disabled |

With latched outputs **disabled** — the current setting — every relay
returns to de-energised after a power cycle. Do not assume state survives
a reboot of the board.

Changing the port invalidates the `17494` default used by `relayctl.py`;
pass `--port` if it is ever moved.

## MQTT settings — `mqtt.htm`

The board can connect to an MQTT broker and expose each relay as a topic.
Not in use on the lab board; the fields hold vendor placeholder values
(`mqtt.eclipseprojects.io`, port 1883).

| Setting | Purpose |
|---------|---------|
| IP address / Port | Broker. Port 8883 switches the board to TLS automatically |
| Client ID | Client name presented to the broker |
| Username / Password | Optional broker credentials |
| Enable Power Up Message | Publish MAC, IP and versions at power up |
| Enable LWT | Last will and testament, published by the broker after 5 minutes of silence |
| Enable Heartbeat | Publish an incrementing uptime count once a minute; resets on socket loss |

Per relay:

| Setting | Purpose |
|---------|---------|
| Enable Subscribe / Subscribe State Topic | Topic carrying `1` or `0` to drive the relay |
| Enable Subscribe Pulse Time / Subscribe Pulse Time Topic | Topic carrying `1`–`255` to pulse the relay for that many 100 ms units |
| Enable Publish / Publish Topic | Publish `1` or `0` whenever the relay changes |

## Ping settings — `ping.htm`

A watchdog: if pings to a chosen host are lost for a minute, a chosen
relay is driven to a chosen state, optionally inverting again when the
link returns. Added in firmware v28.

| Setting | Purpose |
|---------|---------|
| Ping target | Domain or IP to ping |
| Choose a relay | Relay to drive |
| Set relay to state on ping loss | Enable the action |
| Choose a state | State to drive on loss |
| Invert relay on ping restored | Flip back when pings return |

Not configured on the lab board. If it ever is, remember that relays can
then change without any command being sent.

## Firmware

Current: v28. Vendor changelog:

- v27 — fixed a memory leak
- v28 — added the ping-loss relay action

Updates use Devantech's software update tool. Do not update without being
asked.
