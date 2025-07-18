Software Plan: Wind Tunnel CSV + LLM Explorer (Flask Implementation)
Objective
Create a simple Raspberry Pi app that:

Loads a predefined wind tunnel CSV file from disk (no file upload)

Displays CSV data as a graph

Has a button “Send test data to AI” which sends the CSV and user’s question to the local LLM (Ollama) and shows the response

Core Features
Preloaded CSV

The app automatically loads a specific CSV file from a known location (e.g., /home/pi/wind_tunnel_test_data.csv)

Data Visualization

Display line graphs of main metrics (e.g., air velocity, pressure, force, fan speed) vs time

LLM Chat Interface

Text field for the user to enter a question about the data

Button: “Send test data to AI”

On click: app sends the CSV data and the user’s prompt to the local Ollama API

Display the LLM’s answer in the app

Workflow
On launch, the app loads /home/pi/wind_tunnel_test_data.csv

Displays the data as a table and line graph(s)

User enters a question in a text box

User clicks “Send test data to AI”

App sends CSV + question to Ollama via API

App displays AI’s response below

Tech Stack
Backend: Python + Flask (lightweight web server)

Frontend: HTML/CSS/JavaScript with embedded templates

Plotting: Plotly.js (client-side interactive charts)

Data: pandas

LLM API: requests library to connect to local Ollama (Gemma3 1B model)

CSV file: Assumed present at fixed path

Deliverables
Flask app code (flask_app.py)

Uses predefined CSV file (no uploads)

README for setup

Model-Specific Considerations (Gemma3 1B)
Context Window: Keep CSV data summaries concise to fit within model limits

Prompt Engineering: Use clear, specific prompts for better responses from the smaller model

Response Time: Expect faster inference compared to larger models

Data Preprocessing: Consider summarizing large datasets before sending to the model

Example Prompts: Provide suggested questions that work well with Gemma3 1B's capabilities

