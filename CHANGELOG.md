# Changelog (Simple)

## 1.1.0 — 2025-08-10
- What changed: IO is grouped neatly (digital/analogue/custom) with simple “show details” for sub-parts; Real (float) values are supported; the PLC connection stays open; old CSVs were removed; small UI cleanups (favicon, tidy home page).
- Why: To make the dashboard easier to read, reduce noise, and support your analogue scaling values. Cleaning removed files keeps the project simple.
- How: Added grouping rules and a small groups editor in Settings; taught the app to read Real values; reused one PLC connection; moved config/logs under a data folder; removed unused sections and files.

## 1.0.0 — 2024-12-19
- What changed: First stable release with the web app, PLC comms, basic AI, IO mapping, and event log.
- Why: Provide a simple local tool to view PLC status and generate quick operator insights.
- How: Built a small Flask app with local PLC reads, a config file, and a basic UI.
