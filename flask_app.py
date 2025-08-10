from flask import Flask, render_template_string, request, jsonify
import pandas as pd
import json
import requests
import atexit
from config import (
    load_config, save_config, get_config_summary, update_plc_settings,
    update_io_mapping, get_io_mapping, get_io_groups, update_io_group, remove_io_group
)
from plc_communicator import PLCCommunicator
from nav_template import NAV_TEMPLATE, NAV_STYLES
from event_logger import event_logger
import os

app = Flask(__name__)

# No longer loading CSV data - using live PLC data instead

# Create a single PLC communicator instance and clean up on exit
plc = PLCCommunicator()
atexit.register(plc.disconnect)

def query_ollama(prompt, data_summary):
    """Send query to local Ollama API with Gemma3 1B model"""
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
                "model": "gemma3:1b",  # Using Gemma3 1B model for Pi compatibility
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

# Configuration page template
config_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>PLC Configuration - E-Stop AI Status Reporter</title>
    <link rel="icon" href="/static/favicon.ico">
    <style>
        /* Navigation Styles */
        {{ nav_styles|safe }}
        
        /* Main Content Styles */
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .section {
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .form-group {
            margin: 10px 0;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], input[type="number"], select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .btn {
            background-color: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            margin: 5px;
        }
        .btn:hover {
            background-color: #0056b3;
        }
        .btn-success {
            background-color: #28a745;
        }
        .btn-success:hover {
            background-color: #218838;
        }
        .btn-danger {
            background-color: #dc3545;
        }
        .btn-danger:hover {
            background-color: #c82333;
        }
        .status {
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .status.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .io-item {
            border: 1px solid #ddd;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .io-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .io-name {
            font-weight: bold;
            font-size: 16px;
        }
        .io-description {
            color: #666;
            font-size: 12px;
        }
        .test-result {
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
        }
        .test-result.success {
            background-color: #d4edda;
            color: #155724;
        }
        .test-result.error {
            background-color: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    {{ nav_html|safe }}
    
    <div class="container">
        <div class="page-header">
            <h2>PLC Configuration</h2>
            <p>Configure your PLC connection settings and IO mapping.</p>
        </div>
        
        <div class="section">
            <h2>PLC Connection Settings</h2>
            <form id="plcForm">
                <div class="form-group">
                    <label for="plc_ip">PLC IP Address:</label>
                    <input type="text" id="plc_ip" name="plc_ip" value="{{ config.plc_ip }}" required>
                </div>
                <div class="form-group">
                    <label for="plc_rack">Rack Number:</label>
                    <input type="number" id="plc_rack" name="plc_rack" value="{{ config.plc_rack }}" min="0" max="31">
                </div>
                <div class="form-group">
                    <label for="plc_slot">Slot Number:</label>
                    <input type="number" id="plc_slot" name="plc_slot" value="{{ config.plc_slot }}" min="0" max="31">
                </div>
                <button type="submit" class="btn btn-success">Save PLC Settings</button>
                <button type="button" class="btn" onclick="testConnection()">Test Connection</button>
            </form>
            <div id="plcStatus"></div>
        </div>
        
        <div class="section">
            <h2>IO Mapping Configuration</h2>
            <p>Configure your PLC IO addresses. Current mapping has {{ config.io_count }} items.</p>
            
            <div class="section">
                <h3>IO Groups</h3>
                <div id="groupsList"></div>
                <h4>Add / Update Group</h4>
                <form id="groupForm">
                    <div class="form-group">
                        <label for="group_name">Group Name:</label>
                        <input type="text" id="group_name" name="group_name" placeholder="e.g., Digital Inputs" required>
                    </div>
                    <div class="form-group">
                        <label for="group_items">IO Names (comma separated):</label>
                        <input type="text" id="group_items" name="group_items" placeholder="e.g., A0_State, A1_State">
                    </div>
                    <button type="submit" class="btn">Save Group</button>
                    <button type="button" class="btn btn-danger" onclick="deleteGroup()">Delete Group</button>
                </form>
            </div>

            <div id="ioMapping">
                {% for io_name, io_config in config.io_mapping.items() %}
                <div class="io-item">
                    <div class="io-header">
                        <div>
                            <div class="io-name">{{ io_name }}</div>
                            <div class="io-description">{{ io_config.description }}</div>
                        </div>
                        <button class="btn btn-danger" onclick="removeIO('{{ io_name }}')">Remove</button>
                    </div>
                    <form class="io-form" data-io-name="{{ io_name }}">
                        <div class="form-group">
                            <label>Data Type:</label>
                            <select name="io_type" required>
                                <option value="bit" {% if io_config.type == 'bit' %}selected{% endif %}>Bit (DBX)</option>
                                <option value="byte" {% if io_config.type == 'byte' %}selected{% endif %}>Byte (DBB)</option>
                                <option value="word" {% if io_config.type == 'word' %}selected{% endif %}>Word (DBW)</option>
                                <option value="dword" {% if io_config.type == 'dword' %}selected{% endif %}>DWord (DBD)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>PLC Address:</label>
                            <input type="text" name="io_address" value="{{ io_config.address }}" required 
                                   placeholder="e.g., DB1.DBX0.0, DB1.DBW2">
                        </div>
                        <div class="form-group">
                            <label>Description:</label>
                            <input type="text" name="io_description" value="{{ io_config.description }}" 
                                   placeholder="Description of this IO point">
                        </div>
                        <button type="submit" class="btn">Update IO</button>
                        <button type="button" class="btn" onclick="testIO('{{ io_name }}')">Test IO</button>
                    </form>
                    <div id="testResult_{{ io_name }}" class="test-result" style="display: none;"></div>
                </div>
                {% endfor %}
            </div>
            
            <div class="section">
                <h3>Add New IO Point</h3>
                <form id="newIOForm">
                    <div class="form-group">
                        <label for="new_io_name">IO Name:</label>
                        <input type="text" id="new_io_name" name="io_name" required placeholder="e.g., Temperature_Sensor">
                    </div>
                    <div class="form-group">
                        <label for="new_io_type">Data Type:</label>
                        <select id="new_io_type" name="io_type" required>
                            <option value="bit">Bit (DBX)</option>
                            <option value="byte">Byte (DBB)</option>
                            <option value="word">Word (DBW)</option>
                            <option value="dword">DWord (DBD)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="new_io_address">PLC Address:</label>
                        <input type="text" id="new_io_address" name="io_address" required 
                               placeholder="e.g., DB1.DBX0.0, DB1.DBW2">
                    </div>
                    <div class="form-group">
                        <label for="new_io_description">Description:</label>
                        <input type="text" id="new_io_description" name="io_description" 
                               placeholder="Description of this IO point">
                    </div>
                    <button type="submit" class="btn btn-success">Add IO Point</button>
                </form>
            </div>
        </div>
        
        <div style="margin-top: 30px;">
            <a href="/" class="btn">Back to Main Dashboard</a>
        </div>
    </div>
    
    <script>
        // PLC Settings Form
        document.getElementById('plcForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {
                ip: formData.get('plc_ip'),
                rack: parseInt(formData.get('plc_rack')),
                slot: parseInt(formData.get('plc_slot'))
            };
            
            fetch('/update_plc_settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                const statusDiv = document.getElementById('plcStatus');
                if (data.success) {
                    statusDiv.className = 'status success';
                    statusDiv.textContent = 'PLC settings saved successfully!';
                } else {
                    statusDiv.className = 'status error';
                    statusDiv.textContent = 'Error: ' + data.error;
                }
            });
        });
        
        // Test PLC Connection
        function testConnection() {
            fetch('/test_plc_connection')
            .then(response => response.json())
            .then(data => {
                const statusDiv = document.getElementById('plcStatus');
                if (data.success) {
                    statusDiv.className = 'status success';
                    statusDiv.textContent = 'Connection test successful! ' + data.message;
                } else {
                    statusDiv.className = 'status error';
                    statusDiv.textContent = 'Connection test failed: ' + data.error;
                }
            });
        }
        
        // IO Form Submission
        document.addEventListener('submit', function(e) {
            if (e.target.classList.contains('io-form')) {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const ioName = e.target.dataset.ioName;
                const data = {
                    io_name: ioName,
                    io_type: formData.get('io_type'),
                    io_address: formData.get('io_address'),
                    io_description: formData.get('io_description')
                };
                
                fetch('/update_io_mapping', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('IO mapping updated successfully!');
                    } else {
                        alert('Error: ' + data.error);
                    }
                });
            }
        });
        
        // Test IO Reading
        function testIO(ioName) {
            fetch('/test_io_reading', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({io_name: ioName})
            })
            .then(response => response.json())
            .then(data => {
                const resultDiv = document.getElementById('testResult_' + ioName);
                resultDiv.style.display = 'block';
                
                if (data.success) {
                    resultDiv.className = 'test-result success';
                    resultDiv.textContent = 'Test successful! Value: ' + data.value;
                } else {
                    resultDiv.className = 'test-result error';
                    resultDiv.textContent = 'Test failed: ' + data.error;
                }
            });
        }
        
        // Remove IO Point
        function removeIO(ioName) {
            if (confirm('Are you sure you want to remove ' + ioName + '?')) {
                fetch('/remove_io_mapping', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({io_name: ioName})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload(); // Refresh page to show updated mapping
                    } else {
                        alert('Error: ' + data.error);
                    }
                });
            }
        }
        
        // Add New IO Form
        document.getElementById('newIOForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {
                io_name: formData.get('io_name'),
                io_type: formData.get('io_type'),
                io_address: formData.get('io_address'),
                io_description: formData.get('io_description')
            };
            
            fetch('/add_io_mapping', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('IO point added successfully!');
                    location.reload(); // Refresh page to show new IO
                } else {
                    alert('Error: ' + data.error);
                }
            });
        });
    </script>
</body>
</html>
'''

template = '''
<!DOCTYPE html>
<html>
<head>
    <title>E-Stop AI Status Reporter</title>
    <link rel="icon" href="/static/favicon.ico">
    <style>
        /* Navigation Styles */
        {{ nav_styles|safe }}
        
        /* Main Content Styles */
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 0;
            background-color: #f5f5f5;
        }
        .container { 
            max-width: 100%; 
            margin: 0; 
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
            font-size: 12px;
            table-layout: fixed;
        }
        .table th, .table td {
            border: 1px solid #ddd;
            padding: 6px;
            text-align: left;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .table th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .table-responsive {
            overflow-x: auto;
            margin: 20px 0;
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
        .io-status-container {
            margin: 20px 0;
        }
        .io-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .io-card {
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .io-card.online {
            border-left: 4px solid #28a745;
        }
        .io-card.offline {
            border-left: 4px solid #dc3545;
        }
        .io-card.error {
            border-left: 4px solid #ffc107;
        }
        .io-name {
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 5px;
        }
        .io-description {
            color: #666;
            font-size: 12px;
            margin-bottom: 10px;
        }
        .io-value {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .io-value.on {
            color: #28a745;
        }
        .io-value.off {
            color: #dc3545;
        }
        .io-value.number {
            color: #007bff;
        }
        .io-address {
            font-family: monospace;
            font-size: 11px;
            color: #888;
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
        }
        .refresh-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .refresh-info span {
            color: #666;
            font-size: 12px;
        }
        .event-log-section {
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .event-log-header {
            background: #f8f9fa;
            padding: 10px 15px;
            border-bottom: 1px solid #ddd;
            font-weight: bold;
        }
        .event-log-content {
            max-height: 300px;
            overflow-y: auto;
            padding: 10px;
        }
        .event-item {
            padding: 3px 0;
            font-family: monospace;
            font-size: 12px;
            border-bottom: 1px solid #f0f0f0;
        }
        .event-item:last-child {
            border-bottom: none;
        }
        .no-events {
            padding: 20px;
            text-align: center;
            color: #666;
            font-style: italic;
        }
        /* Grouped IO styles */
        .group-item { margin: 10px 0; }
        .group-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
        .group-title { font-weight: bold; font-size: 16px; }
        .group-children { display: none; margin-left: 10px; }
        .toggle-btn { font-size: 12px; padding: 4px 8px; }
        .page-header {
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        .page-header h2 {
            margin: 0 0 10px 0;
            color: #333;
            font-size: 28px;
        }
        .page-header p {
            margin: 0;
            color: #666;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    {{ nav_html|safe }}
    
    <div class="container">
        <div class="page-header">
            <h2>Dashboard</h2>
            <p>Monitor PLC system status and generate intelligent operator reports using Gemma3 1B AI</p>
        </div>
        
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
        
        <h2>Live IO Status</h2>
        <div class="io-status-container">
            <div id="ioGroupsContainer">
                <!-- Grouped IO status will be inserted here -->
            </div>
            <div class="refresh-info">
                <button class="btn" onclick="refreshIOStatus()" style="background-color: #28a745;">Refresh IO Status</button>
                <span id="lastUpdate">Last update: Never</span>
            </div>
        </div>
        
        <div class="event-log-section">
            <div class="event-log-header">
                Recent Events Log
                <button class="btn" onclick="clearEventLog()" style="float: right; font-size: 12px; padding: 5px 10px; background-color: #dc3545; margin-left: 5px;">Clear Log</button>
                <button class="btn" onclick="refreshEventLog()" style="float: right; font-size: 12px; padding: 5px 10px;">Refresh</button>
            </div>
            <div class="event-log-content" id="eventLogContent">
                <div class="no-events">Loading events...</div>
            </div>
        </div>
        
        <div class="ai-section">
            <h2>AI Analysis with Gemma3 1B</h2>
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
            <p><strong>AI Model:</strong> Gemma3 1B running locally via Ollama<br>
            <strong>Visualization:</strong> Interactive Plotly charts<br>
            <strong>Framework:</strong> Flask</p>
        </div>
    </div>
    
    <script>
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
        
        function refreshEventLog() {
            fetch('/get_event_log')
            .then(response => response.json())
            .then(data => {
                updateEventLog(data.events);
            })
            .catch(error => {
                console.error('Error refreshing event log:', error);
                document.getElementById('eventLogContent').innerHTML = '<div class="no-events">Error loading events</div>';
            });
        }
        
        function clearEventLog() {
            if (confirm('Are you sure you want to clear all event logs? This action cannot be undone.')) {
                fetch('/clear_event_log', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        document.getElementById('eventLogContent').innerHTML = '<div class="no-events">Event log cleared - no events recorded yet</div>';
                        alert('Event log cleared successfully!');
                    } else {
                        alert('Error clearing event log: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error clearing event log:', error);
                    alert('Error clearing event log: ' + error);
                });
            }
        }
        
        function updateEventLog(events) {
            const eventLogContent = document.getElementById('eventLogContent');
            if (!eventLogContent) { return; }
            
            if (!events || events.length === 0) {
                eventLogContent.innerHTML = '<div class="no-events">No events recorded yet</div>';
                return;
            }
            
            let html = '';
            events.forEach(event => {
                // Only show events that represent actual changes (not initialization)
                if (event.event_type === 'initialization') {
                    return; // Skip initialization events
                }
                
                // Use the pre-formatted change description from the event logger
                // The event logger already handles all the formatting logic correctly
                let change = event.change_description || 'Unknown change';
                
                html += `<div class="event-item">${event.formatted_time} - ${event.io_name}: ${change}</div>`;
            });
            
            // Load groups list on config page
            loadGroups();

            // Group form
            document.getElementById('groupForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const name = document.getElementById('group_name').value.trim();
                const items = document.getElementById('group_items').value
                    .split(',')
                    .map(s => s.trim())
                    .filter(Boolean);
                fetch('/update_io_group', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ group_name: name, items: items })
                })
                .then(r => r.json())
                .then(data => { if (data.success) { alert('Group saved'); loadGroups(); } else { alert('Error: ' + data.error); } });
            });

            window.deleteGroup = function() {
                const name = document.getElementById('group_name').value.trim();
                if (!name) { alert('Enter group name'); return; }
                fetch('/remove_io_group', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ group_name: name })
                }).then(r => r.json()).then(data => { if (data.success) { alert('Group deleted'); loadGroups(); } else { alert('Error: ' + data.error); } });
            }

            function loadGroups() {
                fetch('/get_io_groups')
                .then(r => r.json())
                .then(data => {
                    const div = document.getElementById('groupsList');
                    const groups = data.io_groups || {};
                    if (Object.keys(groups).length === 0) { div.innerHTML = '<div class="no-events">No groups defined</div>'; return; }
                    let html = '';
                    Object.entries(groups).forEach(([name, items]) => {
                        html += `<div style="margin:8px 0;"><strong>${name}</strong>: ${items.join(', ')}</div>`;
                    });
                    div.innerHTML = html;
                });
            }

            if (html === '') {
                eventLogContent.innerHTML = '<div class="no-events">No changes recorded yet</div>';
            } else {
                eventLogContent.innerHTML = html;
            }
        }
        
        function refreshIOStatus() {
            fetch('/get_io_status')
            .then(response => response.json())
            .then(data => {
                updateGroupedIO(data.io_data, data.io_groups);
                document.getElementById('lastUpdate').textContent = 'Last update: ' + new Date().toLocaleTimeString();
            })
            .catch(error => {
                console.error('Error refreshing IO status:', error);
                document.getElementById('lastUpdate').textContent = 'Last update: Error - ' + new Date().toLocaleTimeString();
            });
        }

        function renderCard(ioName, ioInfo) {
            const card = document.createElement('div');
            card.className = 'io-card';
            if (ioInfo.status === 'error') {
                card.classList.add('error');
            } else if (ioInfo.value !== null) {
                card.classList.add('online');
            } else {
                card.classList.add('offline');
            }
            let valueClass = 'number';
            if (ioInfo.type === 'bit') {
                valueClass = ioInfo.value ? 'on' : 'off';
            }
            let valueDisplay = 'ERROR';
            if (ioInfo.value !== null) {
                if (ioInfo.type === 'bit') {
                    valueDisplay = ioInfo.value ? 'ON' : 'OFF';
                } else {
                    valueDisplay = ioInfo.value.toString();
                }
            }
            card.innerHTML = `
                <div class="io-name">${ioName}</div>
                <div class="io-description">${ioInfo.description}</div>
                <div class="io-value ${valueClass}">${valueDisplay}</div>
                <div class="io-address">${ioInfo.address}</div>
            `;
            return card;
        }

        function updateGroupedIO(ioData, ioGroups) {
            const container = document.getElementById('ioGroupsContainer');
            container.innerHTML = '';

            // If groups exist, render by group order; otherwise render all flat
            if (ioGroups && Object.keys(ioGroups).length > 0) {
                Object.entries(ioGroups).forEach(([groupName, ioList]) => {
                    const section = document.createElement('div');
                    section.className = 'section';
                    const h3 = document.createElement('h3');
                    h3.textContent = groupName;
                    section.appendChild(h3);

                    // Build hierarchical rows for Digital Inputs/Outputs and Analogue Inputs
                    const grid = document.createElement('div');
                    grid.className = 'io-grid';

                    // Helper to create parent row with collapsible children
                    function addParentWithChildren(parentName, childNames) {
                        const wrapper = document.createElement('div');
                        wrapper.className = 'group-item';
                        const header = document.createElement('div');
                        header.className = 'group-header';
                        const btn = document.createElement('button');
                        btn.className = 'btn toggle-btn';
                        btn.textContent = 'Show details';
                        const title = document.createElement('div');
                        title.className = 'group-title';
                        title.textContent = parentName;
                        header.appendChild(btn);
                        header.appendChild(title);

                        // Main parent card
                        if (ioData[parentName]) {
                            header.appendChild(renderCard(parentName, ioData[parentName]));
                        }
                        wrapper.appendChild(header);

                        const children = document.createElement('div');
                        children.className = 'group-children';
                        (childNames || []).forEach(n => {
                            if (ioData[n]) {
                                children.appendChild(renderCard(n, ioData[n]));
                            }
                        });
                        wrapper.appendChild(children);

                        btn.addEventListener('click', function() {
                            const visible = children.style.display === 'block';
                            children.style.display = visible ? 'none' : 'block';
                            btn.textContent = visible ? 'Show details' : 'Hide details';
                        });

                        grid.appendChild(wrapper);
                    }

                    // Decide how to group based on naming conventions
                    if (groupName === 'Digital Inputs' || groupName === 'Digital Outputs') {
                        const buckets = {};
                        (ioList || []).forEach(name => {
                            const base = name.split('_')[0]; // A0, A1, Out_A0, etc.
                            if (!buckets[base]) buckets[base] = [];
                            buckets[base].push(name);
                        });
                        Object.entries(buckets).forEach(([base, names]) => {
                            // Parent preference: State if present, else first
                            const parent = names.find(n => /_State$/i.test(n)) || names[0];
                            const children = names.filter(n => n !== parent);
                            addParentWithChildren(parent, children);
                        });
                    } else if (groupName === 'Analogue Inputs') {
                        const buckets = {};
                        (ioList || []).forEach(name => {
                            const base = name.split('_')[0]; // AI0, AI1
                            if (!buckets[base]) buckets[base] = [];
                            buckets[base].push(name);
                        });
                        Object.entries(buckets).forEach(([base, names]) => {
                            const parent = names.find(n => /_Scaled$/i.test(n)) || names[0];
                            const children = names.filter(n => n !== parent);
                            addParentWithChildren(parent, children);
                        });
                    } else {
                        // Default: render cards flat
                        (ioList || []).forEach(name => {
                            if (ioData[name]) {
                                grid.appendChild(renderCard(name, ioData[name]));
                            }
                        });
                    }

                    section.appendChild(grid);
                    container.appendChild(section);
                });
            }

            // Show any remaining IOs not listed in groups under "Ungrouped"
            const groupedSet = new Set([].concat(...Object.values(ioGroups || {})));
            const ungrouped = Object.entries(ioData).filter(([n]) => !groupedSet.has(n));
            if (ungrouped.length > 0) {
                const section = document.createElement('div');
                section.className = 'section';
                const h3 = document.createElement('h3');
                h3.textContent = 'Ungrouped';
                section.appendChild(h3);
                const grid = document.createElement('div');
                grid.className = 'io-grid';
                ungrouped.forEach(([name, info]) => grid.appendChild(renderCard(name, info)));
                section.appendChild(grid);
                container.appendChild(section);
            }
        }
        
        // Update connection status in navigation
        function updateConnectionStatus() {
            fetch('/get_io_status')
            .then(response => response.json())
            .then(data => {
                const statusDot = document.querySelector('.status-dot');
                const statusText = document.querySelector('#connectionStatus');
                
                // Check if any IO points are online
                const hasOnlineIO = Object.values(data.io_data).some(io => io.status === 'online');
                
                if (hasOnlineIO) {
                    statusDot.className = 'status-dot connected';
                    statusText.innerHTML = '<span class="status-dot connected"></span>Connected';
                } else {
                    statusDot.className = 'status-dot disconnected';
                    statusText.innerHTML = '<span class="status-dot disconnected"></span>Disconnected';
                }
            })
            .catch(error => {
                const statusDot = document.querySelector('.status-dot');
                const statusText = document.querySelector('#connectionStatus');
                statusDot.className = 'status-dot disconnected';
                statusText.innerHTML = '<span class="status-dot disconnected"></span>Error';
            });
        }
        
        // Auto-refresh every 5 seconds
        setInterval(refreshIOStatus, 5000);
        setInterval(refreshEventLog, 10000); // Refresh events every 10 seconds
        setInterval(updateConnectionStatus, 10000); // Update connection status every 10 seconds
        
        // Load initial data when page loads
            document.addEventListener('DOMContentLoaded', function() {
            refreshIOStatus();
            refreshEventLog();
            updateConnectionStatus();
            
            // Enter key handler (only if input exists on this page)
            const qi = document.getElementById('questionInput');
            if (qi) {
                qi.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') sendQuestion();
                });
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    # Calculate system metrics from live IO data and event statistics
    try:
        plc = PLCCommunicator()
        io_mapping = get_io_mapping()
        
        if plc.connect():
            io_data = {}
            for io_name, io_config in io_mapping.items():
                try:
                    value = plc.read_io(io_name)
                    io_data[io_name] = value
                except:
                    io_data[io_name] = None
            plc.disconnect()
            
            # Count active signals
            active_signals = sum(1 for value in io_data.values() if value is not None and value != 0)
            total_signals = len(io_data)
            system_status = f"{active_signals}/{total_signals} signals active"
        else:
            system_status = "PLC not connected"
            total_signals = len(io_mapping)
            active_signals = 0
    except Exception as e:
        system_status = "Error reading PLC"
        total_signals = 0
        active_signals = 0
    
    # Get event statistics
    try:
        event_stats = event_logger.get_event_statistics()
        emergency_stops = event_stats.get('critical_events', 0)
        data_points = event_stats.get('events_today', 0)
    except:
        emergency_stops = 0
        data_points = 0
    
    return render_template_string(template,
        nav_html=NAV_TEMPLATE,
        nav_styles=NAV_STYLES,
        data_points=data_points,
        emergency_stops=emergency_stops,
        system_status=system_status
    )

@app.route('/test_ollama')
def test_ollama():
    """Simple test endpoint to check if Ollama is working"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3:1b",
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
    
    # Get live IO data for AI analysis
    try:
        plc = PLCCommunicator()
        io_mapping = get_io_mapping()
        io_data = {}
        
        if plc.connect():
            for io_name in io_mapping.keys():
                try:
                    value = plc.read_io(io_name)
                    io_data[io_name] = value
                except:
                    io_data[io_name] = None
            plc.disconnect()
        else:
            # Use configured IO with null values if PLC not connected
            for io_name in io_mapping.keys():
                io_data[io_name] = None
        
        # Prepare data summary for AI
        active_signals = sum(1 for value in io_data.values() if value is not None and value != 0)
        total_signals = len(io_data)
        
        data_summary = f"""
        Live PLC System Data Summary:
        - Total IO Points: {total_signals}
        - Active Signals: {active_signals}
        - Connection Status: {'Connected' if plc.connect() else 'Not Connected'}
        
        Current IO Values:
        {chr(10).join([f"- {name}: {value}" for name, value in io_data.items()])}
        """
        
        if plc.connect():
            plc.disconnect()
        
    except Exception as e:
        data_summary = f"Error reading PLC data: {str(e)}"
    
    response = query_ollama(question, data_summary)
    return jsonify({'response': response})

# Configuration routes
@app.route('/config')
def config():
    """Render the PLC configuration page"""
    config_summary = get_config_summary()
    return render_template_string(config_template, 
        nav_html=NAV_TEMPLATE,
        nav_styles=NAV_STYLES,
        config=config_summary
    )

@app.route('/update_plc_settings', methods=['POST'])
def update_plc_settings_route():
    """Endpoint to update PLC connection settings"""
    try:
        data = request.json
        success = update_plc_settings(data['ip'], data['rack'], data['slot'])
        return jsonify({'success': success, 'message': 'PLC settings updated' if success else 'Failed to update settings'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/test_plc_connection')
def test_plc_connection():
    """Endpoint to test PLC connection"""
    try:
        plc = PLCCommunicator()
        success, message = plc.test_connection()
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update_io_mapping', methods=['POST'])
def update_io_mapping_route():
    """Endpoint to update an existing IO mapping"""
    try:
        data = request.json
        success = update_io_mapping(data['io_name'], data['io_type'], data['io_address'], data['io_description'])
        return jsonify({'success': success, 'message': 'IO mapping updated' if success else 'Failed to update mapping'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/test_io_reading', methods=['POST'])
def test_io_reading():
    """Endpoint to test reading an IO point"""
    try:
        data = request.json
        plc = PLCCommunicator()
        if plc.connect():
            value = plc.read_io(data['io_name'])
            plc.disconnect()
            if value is not None:
                return jsonify({'success': True, 'value': value})
            else:
                return jsonify({'success': False, 'error': plc.last_error})
        else:
            return jsonify({'success': False, 'error': 'Failed to connect to PLC'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/add_io_mapping', methods=['POST'])
def add_io_mapping():
    """Endpoint to add a new IO mapping"""
    try:
        data = request.json
        success = update_io_mapping(data['io_name'], data['io_type'], data['io_address'], data['io_description'])
        return jsonify({'success': success, 'message': 'IO mapping added' if success else 'Failed to add mapping'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/remove_io_mapping', methods=['POST'])
def remove_io_mapping():
    """Endpoint to remove an IO mapping"""
    try:
        data = request.json
        config = load_config()
        if data['io_name'] in config['io_mapping']:
            del config['io_mapping'][data['io_name']]
            success = save_config(config)
            return jsonify({'success': success, 'message': 'IO mapping removed' if success else 'Failed to remove mapping'})
        else:
            return jsonify({'success': False, 'error': 'IO mapping not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_io_groups')
def get_groups():
    try:
        return jsonify({'io_groups': get_io_groups()})
    except Exception as e:
        return jsonify({'io_groups': {}, 'error': str(e)})

@app.route('/update_io_group', methods=['POST'])
def update_group():
    try:
        data = request.json
        name = data.get('group_name', '').strip()
        items = data.get('items', [])
        success = update_io_group(name, items)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/remove_io_group', methods=['POST'])
def remove_group():
    try:
        data = request.json
        name = data.get('group_name', '').strip()
        success = remove_io_group(name)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/status')
def system_status():
    """System status page"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>System Status - E-Stop AI Status Reporter</title>
        <link rel="icon" href="/static/favicon.ico">
        <style>
            {{ nav_styles|safe }}
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .page-header { margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #f0f0f0; }
            .page-header h2 { margin: 0 0 10px 0; color: #333; font-size: 28px; }
            .page-header p { margin: 0; color: #666; font-size: 16px; }
        </style>
    </head>
    <body>
        {{ nav_html|safe }}
        <div class="container">
            <div class="page-header">
                <h2>System Status</h2>
                <p>Detailed system status and performance metrics</p>
            </div>
            <div style="text-align: center; padding: 50px;">
                <h3>🚧 Coming Soon</h3>
                <p>System status page is under development.</p>
            </div>
        </div>
    </body>
    </html>
    ''', nav_html=NAV_TEMPLATE, nav_styles=NAV_STYLES)

@app.route('/logs')
def event_logs():
    """Event logs page"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Event Logs - E-Stop AI Status Reporter</title>
        <link rel="icon" href="/static/favicon.ico">
        <style>
            {{ nav_styles|safe }}
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .page-header { margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #f0f0f0; }
            .page-header h2 { margin: 0 0 10px 0; color: #333; font-size: 28px; }
            .page-header p { margin: 0; color: #666; font-size: 16px; }
        </style>
    </head>
    <body>
        {{ nav_html|safe }}
        <div class="container">
            <div class="page-header">
                <h2>Event Logs</h2>
                <p>Historical event logs and system activity</p>
            </div>
            <div style="text-align: center; padding: 50px;">
                <h3>🚧 Coming Soon</h3>
                <p>Event logs page is under development.</p>
            </div>
        </div>
    </body>
    </html>
    ''', nav_html=NAV_TEMPLATE, nav_styles=NAV_STYLES)

@app.route('/get_io_status')
def get_io_status():
    """Get current IO status from PLC"""
    try:
        io_mapping = get_io_mapping()
        io_groups = get_io_groups()
        io_data = {}
        plc_connected = False

        # Ensure persistent connection
        if not plc.is_connected():
            plc_connected = plc.connect()
        else:
            plc_connected = True

        if plc_connected:
            # Read all configured IO points
            for io_name, io_config in io_mapping.items():
                try:
                    value = plc.read_io(io_name)
                    io_data[io_name] = {
                        'value': value,
                        'type': io_config['type'],
                        'description': io_config['description'],
                        'address': io_config['address'],
                        'status': 'online' if value is not None else 'error'
                    }
                except Exception as e:
                    io_data[io_name] = {
                        'value': None,
                        'type': io_config['type'],
                        'description': io_config['description'],
                        'address': io_config['address'],
                        'status': 'error'
                    }
        else:
            # If PLC not connected, return configured IO with null values
            for io_name, io_config in io_mapping.items():
                io_data[io_name] = {
                    'value': None,
                    'type': io_config['type'],
                    'description': io_config['description'],
                    'address': io_config['address'],
                    'status': 'offline'
                }
        
        # Log PLC communication status changes (separate from IO events)
        comm_event = event_logger.log_communication_event(plc_connected)
        
        # Check for changes and log IO events (only for valid state changes)
        io_events = event_logger.check_and_log_changes(io_data, io_mapping)
        
        total_events = len(io_events) + (1 if comm_event else 0)
        
        return jsonify({'io_data': io_data, 'io_groups': io_groups, 'new_events': total_events})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_event_log')
def get_event_log():
    """Get recent event log entries"""
    try:
        # Get recent events
        recent_events = event_logger.get_recent_events(limit=20)
        
        # Format events for display
        formatted_events = [event_logger.format_event_for_display(event) for event in recent_events]
        
        # Get event statistics
        stats = event_logger.get_event_statistics()
        
        return jsonify({
            'events': formatted_events,
            'statistics': stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear_event_log', methods=['POST'])
def clear_event_log():
    """Clear all event log entries"""
    try:
        # Clear the events by writing an empty array to the file
        import json
        with open('io_events.json', 'w') as f:
            json.dump([], f)
        
        return jsonify({'status': 'success', 'message': 'Event log cleared successfully'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500



if __name__ == '__main__':
    # Ensure folders exist for static assets
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static'), exist_ok=True)
    app.run(host='127.0.0.1', port=5001, debug=True)
