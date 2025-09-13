Application Plan: E-Stop AI Status Reporter

Purpose
- Build a simple local app that reads PLC IO and produces clear operator reports.
- Two report types:
  - Scheduled summary every 30 minutes (regular status report).
  - Event-driven reports (e.g., E‑Stop or other triggers) – optional later.
- All AI runs locally using Gemma3 1B via Ollama.

System Overview
- Hardware
  - Raspberry Pi (4 or 5 preferred)
  - Siemens S7‑1200/1500 (S7‑1214 tested)
  - Ethernet between Pi and PLC
- Software
  - python‑snap7 for PLC comms
  - Flask web UI
  - Ollama serving `gemma3:1b` locally

High‑Level Workflow
1) Read current IO snapshot from PLC (digital inputs/outputs, analogue values).
2) Build a short, structured summary of key signals.
3) Generate a natural‑language report using Gemma3 1B (local Ollama API).
4) Save the report and snapshot to `data/reports/` with timestamp.
5) Show the latest report and history in the web UI.

Reporting Cadence
- Scheduled: every 30 minutes (configurable later).
- If PLC is offline, produce a brief “offline” report and log the failure.

Report Contents (simple)
- Header: timestamp, connection status.
- Digital inputs/outputs: show parent (e.g., A0_State) and collapse sub‑items.
- Analogue inputs: show Scaled as primary; list Offset/Scalar as details.
- Short AI summary: 2–3 sentences (status, risks, recommended actions).

Storage & Access
- Files: `data/reports/YYYY‑MM‑DD/HHMM.json` and `HHMM.md` (readable text).
- UI: “Reports” page shows latest report and daily history.

Scheduler Approach (simple)
- Background loop in Flask process that sleeps until the next 30‑minute boundary.
- On wake: snapshot IO → call Ollama → save → update UI cache.

Acceptance Criteria
- A new report file is created every 30 minutes even if no events occur.
- The web UI shows the latest report and a list of today’s reports.
- Works fully offline once dependencies are installed.

Milestones
M1: PLC read + grouping solid (DONE)
M2: Real (float) support (DONE)
M3: Persistent PLC connection (DONE)
M4: Report generator (format + prompt + save) (NEXT)
M5: Scheduler (every 30 minutes) (NEXT)
M6: Reports page (list + view + download) (NEXT)
M7: Simple config for schedule interval (FUTURE)

Deployment Notes
- PLC Put/Get enabled in TIA Portal.
- Ollama running locally with `gemma3:1b` pulled.
- App writes to `data/` folder only (safe for services/permissions).

References
- python‑snap7
- Ollama
- Flask