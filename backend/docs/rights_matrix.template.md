# PSX Data Rights Matrix (TEMPLATE — fill in before any public/commercial launch)

Status: **NOT COMPLETED**. This file is a template with no legal conclusions filled in.
Do not set `PUBLIC_LAUNCH_ENABLED`, `PUBLIC_SIGNALS_ENABLED` or `COMMERCIAL_DATA_ENABLED`
to `true` until the rows below are actually reviewed and signed off by counsel + the data lead.

| Product surface | Data use (real-time / delayed / EOD / historical / index / PUCARS) | User tier | License/authorization held? | Reviewed by | Date | Notes |
|---|---|---|---|---|---|---|
| Company page — price snapshot | EOD | Public |  |  |  |  |
| Company page — historical chart | Historical | Public |  |  |  |  |
| Market overview — index level | Index | Public |  |  |  |  |
| Announcements feed | PUCARS / public notices | Public |  |  |  |  |
| AI signal output | Derived from above | Public |  |  |  |  |

## How this gets used in the codebase

`app/core/config.py` exposes `public_launch_enabled`, `public_signals_enabled` and
`commercial_data_enabled`, all defaulting to `false`. Do not change those defaults in code —
override via `.env` only, and only after this matrix is actually filled in and approved.
