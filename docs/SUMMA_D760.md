# Summa D760 — expected profile (**unverified**)

Placeholder for physical setup. **Do not treat as measured.** Confirm on the machine with a short test cut before relying on these values.

| Setting | Expected (unverified) | Notes |
| --- | --- | --- |
| `origin_corner` | `bottom_right` or `top_right` | Origin on the right when facing the machine |
| `feed_axis` | `y` or `x` | Axis of material unroll |
| `feed_sense` | toward operator → map to `positive`/`negative` after a feed-after test | Vinyl unrolls toward the operator |
| Protocol `swap_xy` / mirrors / scale | Prefer identity; only if dialect requires | Do not fake origin with mirrors |

Once verified, promote values into a named device preset and remove the unverified label.
