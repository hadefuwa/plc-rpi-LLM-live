Application Plan: E-Stop AI Status Reporter
Purpose
When the E-Stop is pressed on a Siemens S7 PLC, a Python application running on a Raspberry Pi will:

Read all key system IO (inputs/outputs) from the PLC

Pass the IO states to a locally running Large Language Model (LLM)

Generate a human-readable operator report and display it on a simple web page

System Overview
Hardware:

Raspberry Pi (4 or 5 preferred for LLM performance)

Siemens S7 PLC (1200/1500/300/400)

Ethernet connection between Pi and PLC

Software Components:

python-snap7 for S7 PLC communications

Ollama (or similar) to host a local LLM (Phi-3 Mini or other small model)

Python Flask for web-based display of reports

Functional Flow
Monitor E-Stop State

Continuously poll a specific digital input on the S7 PLC (e.g., I 0.0 = E-Stop channel).

Detect a change to “pressed” state.

Read System IO

On E-Stop trigger, read a defined set of digital/analogue IO from the PLC:

Inputs: E-Stop, tank level, pump status, etc.

Outputs: motor, valve, alarm relays, etc.

Format this IO data as a status summary.

Generate AI Report

Compose a natural language prompt including the IO summary, e.g.:

diff
Copy
Edit
"The emergency stop has been pressed. Current IO: 
- Pump Running: OFF
- Tank Low Level: ON
- Valve Open: OFF
Please write a short operator report summarising system status and recommended immediate actions."
Send prompt to the local LLM (served by Ollama) via API.

Display Output

Show the AI-generated report on a local Flask web page accessible from any device on the LAN.

(Optional) Log events and reports to a local file.

Minimum Viable Features
Configurable PLC connection (IP, rack, slot)

Configurable input/output list for monitoring

E-Stop edge detection logic

LLM integration with prompt template

Web interface to view latest report

Stretch Features (Optional for V1)
Log history of E-Stop events and AI reports

Option to email or message the report

Custom prompt or scenario logic based on additional IO states

Mobile-friendly web UI

Tech Stack
Python 3.x

python-snap7

Flask

Local LLM via Ollama (REST API)

(Optional) Docker Compose for easy deployment

Deployment Notes
Pi and PLC must be on the same subnet with direct IP access

Put/Get must be enabled in the PLC project (see TIA Portal > Device > Properties > Protection & Security)

LLM model must be installed and served via Ollama or similar tool

Reference Code Links
python-snap7 Docs
Ollama Docs
Flask Docs