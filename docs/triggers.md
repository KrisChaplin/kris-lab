# Triggers

## Edge trigger (SCPI — works)

```bash
python scopectl.py trig --src 3 --lev 0.15 --slope RISE
python scopectl.py trig --coupling AC --nrej on
python scopectl.py trig                                # read state
```

SCPI surface (`Scope.trigger_*`):

| Method | SCPI | Status |
|--------|------|--------|
| `trigger_source(n)` | `:TRIG:EDGE:SOUR C<n>` | ✅ |
| `trigger_level(v)` | `:TRIG:EDGE:LEV <V>` | ✅ |
| `trigger_slope(s)` | `:TRIG:EDGE:SLOP RIS\|FALL\|ALT` | ✅ |
| `trigger_coupling(m)` | `:TRIG:EDGE:COUP AC\|DC` | ✅ |
| `trigger_noise_reject(b)` | `:TRIG:EDGE:NREJ ON\|OFF` | ✏️ write-only |
| `trigger_holdoff()` | `:TRIG:EDGE:HOLDOFF?` | ✅ read; ❌ write (use UI) |

## Advanced trigger types (UI-only)

The `:TRIG:MODE` SCPI sub-tree silently accepts writes but the device
stays in edge mode. Drive the Trigger Type dropdown via touch.

```bash
python scopectl.py trig-ui --type pulse --src 3 --mode auto
python scopectl.py trig-ui --type edge --src 3 --slope rising --mode auto
```

Available types (keys in `trigger.TRIG_TYPES`):

```
edge   slope    pulse
video  window   interval
runt   dropout  pattern
i2c    spi      uart
can    lin
```

Verified: `pulse` changes the top-bar trigger icon. The other 13 will
also select via the same grid coords, but **per-type parameter
sub-panels are not yet mapped**. Open TODO — when adding, screenshot
each type and add per-type touch coords to [trigger.py](../trigger.py).

## Dialog coordinates

See [trigger.py](../trigger.py) for the full coordinate table. Key
entries:

| Element | (x, y) |
|---------|--------|
| Open dialog (top-bar T) | `(453, 30)` |
| Dialog close X | `(755, 68)` |
| Type dropdown | `(183, 108)` |
| Source dropdown | `(183, 154)` |
| Coupling dropdown | `(514, 154)` |
| Level field | `(514, 205)` |
| Holdoff toggle | `(160, 358)` |
| Noise-reject toggle | `(502, 358)` |
| Slope rising / falling / either | `(151\|213\|276, 205)` |
| Mode auto / normal / single | `(481\|543\|605, 110)` |

## Notes

- The `:TRIG:MODE?` query returns the **sweep** mode (`AUTO` / `NORM`),
  not the trigger type. Don't use it to detect "is this still edge?".
- `trigger_ui()` reopens the Trigger dialog every call — cheap, but be
  aware it briefly takes input focus.
