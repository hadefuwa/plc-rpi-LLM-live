from flask import Flask, render_template_string, request, jsonify
import pandas as pd
import json
import requests

app = Flask(__name__)

# Load data
data = pd.read_csv('plc_io_data.csv')

def query_ollama(prompt, data_summary):
    """Send query to local Ollama API with Gemma3B 1B model"""
    try:
        # Prepare the full prompt with data context
        full_prompt = f"""You are analyzing PLC system data for an industrial E-Stop monitoring system. Here is the dataset summary:

{data_summary}

User question: {prompt}

Please provide a clear, CONCISE technical analysis based on this PLC data. Keep your response brief (2-3 sentences max). Focus on system status, safety conditions, and operational insights. Be direct and specific about E-Stop events and system health."""

        # Ollama API call
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3b:1b",  # Using Gemma3B 1B model for Pi compatibility
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": 100,  # Limit response to ~100 tokens
                    "temperature": 0.1   # Lower temperature for more focused responses
                }
            }
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            # Get more detailed error information
            try:
                error_detail = response.json()
                return f"Error: API returned status code {response.status_code}. Details: {error_detail}"
            except:
                return f"Error: API returned status code {response.status_code}. Response: {response.text[:200]}"
    
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama. Make sure Ollama is running locally on port 11434."
    except requests.exceptions.Timeout:
        return "Error: Request timed out after 2 minutes. The Raspberry Pi might need more time to process your request. Try a simpler question or wait for the model to fully load."
    except Exception as e:
        return f"Error: {str(e)}"

template = '''
<!DOCTYPE html>
<html>
<head>
    <title>E-Stop AI Status Reporter</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background-color: #f5f5f5;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .plot { 
            margin: 20px 0; 
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
        }
        .ai-section {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 4px solid #007bff;
        }
        .chat-input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin: 10px 0;
            font-size: 16px;
        }
        .btn {
            background-color: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .btn:hover {
            background-color: #0056b3;
        }
        .example-btn {
            background-color: #6c757d;
            color: white;
            padding: 5px 10px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            margin: 5px;
            font-size: 12px;
        }
        .example-btn:hover {
            background-color: #545b62;
        }
        .response {
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border: 1px solid #ddd;
            white-space: pre-wrap;
        }
        .loading {
            display: none;
            color: #007bff;
            font-style: italic;
        }
        .table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .table th, .table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .table th {
            background-color: #f2f2f2;
        }
        .metrics {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
        }
        .metric {
            text-align: center;
            padding: 10px;
            background-color: #e9ecef;
            border-radius: 5px;
            margin: 0 10px;
        }
        .metric h3 {
            margin: 0;
            color: #007bff;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>E-Stop AI Status Reporter</h1>
        <p>Monitor PLC system status and generate intelligent operator reports using Phi-3 Mini AI</p>
        
        <h2>System Overview</h2>
        <div class="metrics">
            <div class="metric">
                <h3>{{ data_points }}</h3>
                <p>Total Events</p>
            </div>
            <div class="metric">
                <h3>{{ emergency_stops }}</h3>
                <p>E-Stop Events</p>
            </div>
            <div class="metric">
                <h3>{{ system_status }}</h3>
                <p>Current Status</p>
            </div>
        </div>
        
        <h2>System Events</h2>
        {{ data_table|safe }}
        
        <h2>System Monitoring</h2>
        <div id="plot1" class="plot"></div>
        <div id="plot2" class="plot"></div>
        <div id="plot3" class="plot"></div>
        <div id="plot4" class="plot"></div>
        
        <div class="ai-section">
            <h2>AI Analysis with Phi-3 Mini</h2>
            <p>Ask questions about the PLC system status and get AI-powered operator insights!</p>
            
            <div>
                <strong>Example Questions:</strong><br>
                <button class="example-btn" onclick="setQuestion('What caused the most recent emergency stop?')">Latest E-Stop cause?</button>
                <button class="example-btn" onclick="setQuestion('How many emergency stops occurred today?')">E-Stop count today</button>
                <button class="example-btn" onclick="setQuestion('What is the current system status?')">Current status</button>
                <button class="example-btn" onclick="setQuestion('Analyze the system health trends')">System health</button>
                <button class="example-btn" onclick="setQuestion('What are the most common fault conditions?')">Common faults</button>
            </div>
            
            <input type="text" id="questionInput" class="chat-input" placeholder="e.g., What caused the most recent emergency stop?" />
            <br>
            <button class="btn" onclick="sendQuestion()">Send test data to AI</button>
            <button class="btn" onclick="testOllama()" style="background-color: #28a745; margin-left: 10px;">Test AI Connection</button>
            
            <div class="loading" id="loading">AI is analyzing your data...</div>
            <div id="response" class="response" style="display: none;"></div>
        </div>
        
        <div style="margin-top: 40px; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
            <h3>Technical Information</h3>
            <p><strong>Data Structure:</strong></p>
            <ul>
                <li>E_Stop_Status: Emergency stop activation (0=OFF, 1=ON)</li>
                <li>Pump_Running: Pump operational status (0=OFF, 1=ON)</li>
                <li>Tank_Level_Low: Low tank level indicator (0=OK, 1=LOW)</li>
                <li>Valve_Open: Valve position (0=CLOSED, 1=OPEN)</li>
                <li>Motor_Control: Motor control signal (0=OFF, 1=ON)</li>
                <li>Alarm_Relay: Alarm relay status (0=OFF, 1=ON)</li>
                <li>Pressure_High: High pressure indicator (0=OK, 1=HIGH)</li>
                <li>Temperature_High: High temperature indicator (0=OK, 1=HIGH)</li>
                <li>Flow_Rate: System flow rate in L/min</li>
            </ul>
            <p><strong>AI Model:</strong> Phi-3 Mini running locally via Ollama<br>
            <strong>Visualization:</strong> Interactive Plotly charts<br>
            <strong>Framework:</strong> Flask</p>
        </div>
    </div>
    
    <script>
        window.plotData = {
            timestamp: {{ timestamp_json|safe }},
            e_stop: {{ e_stop_json|safe }},
            pump_running: {{ pump_running_json|safe }},
            tank_level: {{ tank_level_json|safe }},
            valve_open: {{ valve_open_json|safe }},
            motor_control: {{ motor_control_json|safe }},
            alarm_relay: {{ alarm_relay_json|safe }},
            pressure_high: {{ pressure_high_json|safe }},
            temperature_high: {{ temperature_high_json|safe }},
            flow_rate: {{ flow_rate_json|safe }}
        };
        
        function setQuestion(question) {
            document.getElementById('questionInput').value = question;
        }
        
        function sendQuestion() {
            var question = document.getElementById('questionInput').value;
            if (!question.trim()) {
                alert('Please enter a question first!');
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('response').style.display = 'none';
            
            fetch('/ask_ai', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question: question})
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('response').style.display = 'block';
                document.getElementById('response').textContent = data.response;
            })
            .catch(error => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('response').style.display = 'block';
                document.getElementById('response').textContent = 'Error: ' + error;
            });
        }
        
        function testOllama() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('response').style.display = 'none';
            
            fetch('/test_ollama')
            .then(response => response.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('response').style.display = 'block';
                if (data.status === 'success') {
                    document.getElementById('response').textContent = 'AI Connection Test: SUCCESS\\n\\nResponse: ' + data.response;
                } else {
                    document.getElementById('response').textContent = 'AI Connection Test: FAILED\\n\\nError: ' + JSON.stringify(data, null, 2);
                }
            })
            .catch(error => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('response').style.display = 'block';
                document.getElementById('response').textContent = 'AI Connection Test: FAILED\\n\\nError: ' + error;
            });
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            var data = window.plotData;
            
            // E-Stop Events Timeline
            Plotly.newPlot('plot1', [{
                x: data.timestamp, y: data.e_stop,
                mode: 'lines+markers', name: 'E-Stop Status',
                line: {color: '#dc3545'}, marker: {color: '#dc3545'}
            }], {
                title: 'Emergency Stop Events Timeline',
                xaxis: {title: 'Time'},
                yaxis: {title: 'E-Stop Status (0=OFF, 1=ON)'}
            });
            
            // System Status Overview
            Plotly.newPlot('plot2', [{
                x: data.timestamp, y: data.pump_running,
                mode: 'lines+markers', name: 'Pump',
                line: {color: '#007bff'}, marker: {color: '#007bff'}
            }, {
                x: data.timestamp, y: data.motor_control,
                mode: 'lines+markers', name: 'Motor',
                line: {color: '#28a745'}, marker: {color: '#28a745'}
            }, {
                x: data.timestamp, y: data.valve_open,
                mode: 'lines+markers', name: 'Valve',
                line: {color: '#ffc107'}, marker: {color: '#ffc107'}
            }], {
                title: 'System Components Status',
                xaxis: {title: 'Time'},
                yaxis: {title: 'Status (0=OFF, 1=ON)'}
            });
            
            // Alarm Conditions
            Plotly.newPlot('plot3', [{
                x: data.timestamp, y: data.alarm_relay,
                mode: 'lines+markers', name: 'Alarm',
                line: {color: '#dc3545'}, marker: {color: '#dc3545'}
            }, {
                x: data.timestamp, y: data.pressure_high,
                mode: 'lines+markers', name: 'High Pressure',
                line: {color: '#fd7e14'}, marker: {color: '#fd7e14'}
            }, {
                x: data.timestamp, y: data.temperature_high,
                mode: 'lines+markers', name: 'High Temperature',
                line: {color: '#e83e8c'}, marker: {color: '#e83e8c'}
            }], {
                title: 'Alarm Conditions and Faults',
                xaxis: {title: 'Time'},
                yaxis: {title: 'Status (0=OK, 1=FAULT)'}
            });
            
            // Flow Rate Analysis
            Plotly.newPlot('plot4', [{
                x: data.timestamp, y: data.flow_rate,
                mode: 'lines+markers', name: 'Flow Rate',
                line: {color: '#6f42c1'}, marker: {color: '#6f42c1'}
            }], {
                title: 'System Flow Rate Over Time',
                xaxis: {title: 'Time'},
                yaxis: {title: 'Flow Rate (L/min)'}
            });
            
            // Enter key handler
            document.getElementById('questionInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendQuestion();
            });
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    # Calculate system metrics
    emergency_stops = len(data[data['E_Stop_Status'] == 1])
    latest_status = data.iloc[-1]['Status_Description'] if len(data) > 0 else "No data"
    
    return render_template_string(template,
        data_points=len(data),
        emergency_stops=emergency_stops,
        system_status=latest_status,
        data_table=data.to_html(classes='table', table_id='data-table'),
        timestamp_json=json.dumps(data['Timestamp'].tolist()),
        e_stop_json=json.dumps(data['E_Stop_Status'].tolist()),
        pump_running_json=json.dumps(data['Pump_Running'].tolist()),
        tank_level_json=json.dumps(data['Tank_Level_Low'].tolist()),
        valve_open_json=json.dumps(data['Valve_Open'].tolist()),
        motor_control_json=json.dumps(data['Motor_Control'].tolist()),
        alarm_relay_json=json.dumps(data['Alarm_Relay'].tolist()),
        pressure_high_json=json.dumps(data['Pressure_High'].tolist()),
        temperature_high_json=json.dumps(data['Temperature_High'].tolist()),
        flow_rate_json=json.dumps(data['Flow_Rate'].tolist())
    )

@app.route('/test_ollama')
def test_ollama():
    """Simple test endpoint to check if Ollama is working"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3b:1b",
                "prompt": "Hello, respond with 'AI is working!'",
                "stream": False
            }
        )
        if response.status_code == 200:
            return jsonify({'status': 'success', 'response': response.json()["response"]})
        else:
            return jsonify({'status': 'error', 'code': response.status_code, 'details': response.text[:200]})
    except Exception as e:
        return jsonify({'status': 'error', 'exception': str(e)})

@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    question = request.json.get('question', '')
    
    # Prepare data summary for AI
    emergency_stops = len(data[data['E_Stop_Status'] == 1])
    latest_status = data.iloc[-1]['Status_Description'] if len(data) > 0 else "No data"
    
    data_summary = f"""
    PLC System Data Summary:
    - Total Events: {len(data)}
    - Emergency Stops: {emergency_stops}
    - Current Status: {latest_status}
    - Flow Rate Range: {data['Flow_Rate'].min():.1f} to {data['Flow_Rate'].max():.1f} L/min
    - Pump Running Events: {len(data[data['Pump_Running'] == 1])}
    - Alarm Events: {len(data[data['Alarm_Relay'] == 1])}
    - High Pressure Events: {len(data[data['Pressure_High'] == 1])}
    - High Temperature Events: {len(data[data['Temperature_High'] == 1])}
    
    Recent Events:
    {data.tail(5).to_string(index=False)}
    """
    
    response = query_ollama(question, data_summary)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
