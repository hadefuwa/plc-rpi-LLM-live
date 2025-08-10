# Changelog (Simple)

## 1.2.0 — 2025-08-10
- What changed: Clean, readable Live IO tables (2 columns, row details hidden under “Details”, alternating row colors, scrollable panes ~10 rows, inline description edit, value colors for ON/≥0 green and OFF/<0 red); removed separate Status column. Events now rotate to daily JSON files; “Events Today” shows today’s count; fixed Clear to wipe the right file; startup logs create one event per IO. UI polish: stronger table styling, local offline table sorting, and collapsible sections (Dashboard, Live IO, AI Analysis).
- Why: To make the dashboard easier to scan, stop the events count from sticking at 1000, and keep everything working offline with a simple, professional feel.
- How: Simplified table markup/CSS and added per‑row detail drawers with scroll containers; added daily log path (`io_events_YYYY-MM-DD.json`) and aggregation; corrected the clear endpoint; bundled a tiny MIT sorter under `static/vendor/`; added show/hide toggles for sections.

## 1.1.0 — 2025-08-10
- What changed: IO is grouped neatly (digital/analogue/custom) with simple “show details” for sub-parts; Real (float) values are supported; the PLC connection stays open; old CSVs were removed; small UI cleanups (favicon, tidy home page).
- Why: To make the dashboard easier to read, reduce noise, and support your analogue scaling values. Cleaning removed files keeps the project simple.
- How: Added grouping rules and a small groups editor in Settings; taught the app to read Real values; reused one PLC connection; moved config/logs under a data folder; removed unused sections and files.

## 1.0.0 — 2024-12-19
- What changed: First stable release with the web app, PLC comms, basic AI, IO mapping, and event log.
- Why: Provide a simple local tool to view PLC status and generate quick operator insights.
- How: Built a small Flask app with local PLC reads, a config file, and a basic UI.
