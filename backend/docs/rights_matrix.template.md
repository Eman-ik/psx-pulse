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

## Note on Capital Stake

PSX's own public portal (dps.psx.com.pk) states its company-page data — including the
financials, ratios and announcements this pilot scrapes — is "powered by capitalstake.com."
So even data pulled directly from PSX's site is, in part, Capital Stake-licensed data
being redistributed by PSX under whatever terms exist between them. Two separate things to
check before public launch: PSX's own terms of use, **and** Capital Stake's terms of use
(linked from the PSX page footer) for whatever redistribution this project does beyond
personal/educational use. Neither has been reviewed yet.

## How this gets used in the codebase

`app/core/config.py` exposes `public_launch_enabled`, `public_signals_enabled` and
`commercial_data_enabled`, all defaulting to `false`. Do not change those defaults in code —
override via `.env` only, and only after this matrix is actually filled in and approved.
