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
        
        /* Main Content Styles - Dark Theme */
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px;
            background-color: #0b1220; /* deep slate */
            color: #e5e7eb; /* light text */
        }
        .container { 
            max-width: 900px; 
            margin: 0 auto; 
            background-color: #0f172a; /* card surface */
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(2,6,23,.5);
            border: 1px solid #1f2937;
        }
        .section {
            margin: 20px 0;
            padding: 16px;
            border: 1px solid #1f2937;
            border-radius: 12px;
            background: #0f172a;
            box-shadow: 0 1px 3px rgba(2,6,23,.5);
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
            border: 1px solid #1f2937;
            padding: 12px;
            margin: 10px 0;
            border-radius: 10px;
            background: #0b1220;
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
        .io-description { color: #9ca3af; font-size: 12px; }
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
    
    <div class="container page-grid">
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
    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%231f2937'/%3E%3Cpath d='M14 3l-3 10h5l-2 8 7-11h-5l3-7z' fill='%23ffffff'/%3E%3C/svg%3E">
    <link rel="stylesheet" href="/static/vendor/tablesort.css">
    <style>
        /* Navigation Styles */
        {{ nav_styles|safe }}
        
        /* Main Content Styles - Dark Theme */
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 0;
            background-color: #0b1220;
            color: #e5e7eb;
        }
        .container { 
            max-width: 100%; 
            margin: 0; 
            background-color: #0f172a;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(2,6,23,.5);
            border: 1px solid #1f2937;
        }
        /* Page grid layout */
        .page-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 16px; }
        .section-card { grid-column: 1 / -1; }
        @media (min-width: 1100px) {
            #events { grid-column: 1 / 8; }
            #ai { grid-column: 8 / -1; }
        }

        /* Generic panel/card styling */
        .panel { background: #0f172a; border: 1px solid #1f2937; border-radius: 12px; box-shadow: 0 1px 3px rgba(2,6,23,.5); }
        .panel-header { display:flex; align-items:center; justify-content:space-between; padding: 12px 16px; border-bottom:1px solid #1f2937; }
        .panel-title { font-weight: 800; font-size: 16px; color:#e5e7eb; }
        .panel-subtitle { color:#94a3b8; font-size:12px; margin-left:8px; }
        .panel-body { padding: 12px 16px; }
        .quick-actions { display:flex; gap:10px; align-items:center; }
        .collapse-btn { background:#374151; color:#e5e7eb; border:1px solid #4b5563; padding:6px 10px; border-radius:6px; font-size:12px; cursor:pointer; }
        .collapse-btn:hover { background:#4b5563; }
        .panel.collapsed .panel-body { display:none; }
        .search-input { width: 260px; max-width: 100%; background:#111827; color:#e5e7eb; border:1px solid #253049; border-radius:8px; padding:8px 10px; }
        .search-input:focus { outline:none; border-color:#2563eb; box-shadow:0 0 0 2px rgba(37,99,235,.25); }
        .plot { 
            margin: 20px 0; 
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
        }
        .ai-section {
            background-color: #0f172a;
            padding: 16px;
            border-radius: 12px;
            margin: 20px 0;
            border: 1px solid #1f2937;
            box-shadow: 0 1px 3px rgba(2,6,23,.5);
        }
        .chat-input { width: 100%; padding: 10px; border: 1px solid #253049; border-radius: 8px; margin: 10px 0; font-size: 16px; background: #111827; color: #e5e7eb; }
        .btn { background-color: #2563eb; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; }
        .btn:hover { background-color: #1d4ed8; }
        .example-btn { background-color: #374151; color: #e5e7eb; padding: 6px 10px; border: none; border-radius: 6px; cursor: pointer; margin: 5px; font-size: 12px; }
        .example-btn:hover { background-color: #4b5563; }
        .response { background-color: #0b1220; padding: 15px; border-radius: 10px; margin: 10px 0; border: 1px solid #1f2937; white-space: pre-wrap; color: #e5e7eb; }
        .loading { display: none; color: #60a5fa; font-style: italic; }
        .table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 12px;
            table-layout: fixed;
        }
        /* IO table (dark) */
        .io-table { width: 100%; border-collapse: separate; border-spacing: 0; margin: 12px 0; font-size: 13px; background:#0b1220; }
        .io-table th { text-align: left; background: linear-gradient(180deg, #101827 0%, #0b1220 100%); color:#f3f4f6; border-bottom:1px solid #253049; padding:12px; position: sticky; top:0; z-index:1; vertical-align: middle; font-weight:800; letter-spacing:.03em; text-transform: uppercase; font-size:12px; }
        .io-table td { padding: 12px; border-bottom: 1px solid #1f2937; color:#e5e7eb; vertical-align: middle; }
        .io-table td + td, .io-table th + th { border-left:1px solid #132036; }
        .io-table tbody tr:nth-child(odd) { background:#0f172a; }
        .io-table tbody tr:nth-child(even) { background:#0d1627; }
        .io-table tbody tr:nth-child(odd):hover { background:#1e293b; }
        .io-table tbody tr:nth-child(even):hover { background:#1e293b; }
        .io-table th:nth-child(2), .io-table td:nth-child(2) { text-align: right; }
        .group-row td { background:#0f172a; color:#94a3b8; font-weight:700; padding-top:12px; }
        .value-cell { font-weight:800; text-align: right; }
        .value-cell.on { color:#16a34a; }
        .value-cell.off { color:#dc2626; }
        .value-cell.nonneg { color:#16a34a; }
        .value-cell.neg { color:#ef4444; }
        .value-cell.offline { color:#f59e0b; }
        .value-cell.error { color:#ef4444; }
        .subchips { margin-top:4px; color:#94a3b8; font-size:11px; }
        
        /* Scrollable table containers */
        .table-container { 
            max-height: 400px; 
            overflow-y: auto; 
            border: 1px solid #253049; 
            border-radius: 10px; 
            margin: 12px 0;
            box-shadow: 0 8px 24px rgba(0,0,0,.35);
            overflow: hidden;
        }
        .table-container::-webkit-scrollbar { width: 8px; }
        .table-container::-webkit-scrollbar-track { background: #0f172a; border-radius: 4px; }
        .table-container::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
        .table-container::-webkit-scrollbar-thumb:hover { background: #4b5563; }
        
        /* Show more/less controls */
        .table-controls { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin: 8px 0; 
            padding: 8px 12px; 
            background: #0b1220; 
            border-radius: 6px; 
            border: 1px solid #1f2937;
        }
        .table-count { 
            color: #94a3b8; 
            font-size: 12px; 
        }
        .show-more-btn { 
            background: #3b82f6; 
            color: white; 
            border: none; 
            padding: 4px 12px; 
            border-radius: 4px; 
            font-size: 11px; 
            cursor: pointer; 
            transition: background 0.2s;
        }
        .show-more-btn:hover { background: #2563eb; }
        .show-more-btn.showing-all { background: #6b7280; }
        .show-more-btn.showing-all:hover { background: #4b5563; }
        /* Details dropdown + inline edit */
        .details-toggle-btn { background:#1f2937; color:#93c5fd; border:1px solid #253049; border-radius:6px; padding:4px 8px; font-size:11px; cursor:pointer; margin-left:8px; }
        .details-toggle-btn:hover { background:#253049; }
        .details-row { background:#0b1220; }
        .details-box { display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:10px; padding:10px; }
        .detail-label { color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:.04em; display:block; }
        .detail-value { color:#e5e7eb; font-size:12px; font-weight:600; }
        .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
        .desc-inline { display:flex; align-items:center; gap:8px; }
        .desc-text { cursor:text; padding:4px 6px; border-radius:4px; }
        .desc-text:hover { background:#111827; }
        .subchip { display:inline-block; background:#111827; border:1px solid #1f2937; border-radius:6px; padding:2px 6px; margin-right:6px; }
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
        /* Header metrics - professional look */
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 20px 0; }
        .metric { background: linear-gradient(135deg, #0b1220 0%, #0f172a 100%); border: 1px solid #1f2937; border-radius: 10px; padding: 16px; text-align: left; box-shadow: 0 1px 2px rgba(2,6,23,.5); }
        .metric h3 { margin: 0; font-size: 24px; color: #e5e7eb; }
        .metric p { margin: 4px 0 0; color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: .06em; }
        .io-status-container {
            margin: 20px 0;
        }
        .io-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; margin: 16px 0; }
        .io-card { background: #0b1220; border: 1px solid #1f2937; border-radius: 10px; padding: 10px; box-shadow: 0 1px 3px rgba(2,6,23,.5); transition: box-shadow .2s ease, transform .1s ease; }
        .io-card.io-new { padding: 12px; }
        .io-card:hover { box-shadow: 0 4px 14px rgba(2,6,23,.6); transform: translateY(-1px); }
        .io-card.online {
            border-left: 4px solid #22c55e;
        }
        .io-card.offline {
            border-left: 4px solid #ef4444;
        }
        .io-card.error {
            border-left: 4px solid #f59e0b;
        }
        .io-name { font-weight: 700; font-size: 13px; color: #e5e7eb; margin-bottom: 4px; }
        .io-name-secondary { color: #94a3b8; font-size: 11px; margin-bottom: 6px; }
        .io-description { color: #94a3b8; font-size: 11px; margin-bottom: 8px; min-height: 15px; }
        .io-value { font-size: 16px; font-weight: 800; margin-bottom: 6px; }
        .io-value.on { color: #16a34a; }
        .io-value.off { color: #dc2626; }
        .io-value.number { color: #0ea5e9; }
        .io-address {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            font-size: 11px;
            color: #94a3b8;
            background: #111827;
            border: 1px solid #1f2937;
            padding: 4px 6px;
            border-radius: 6px;
            display: block;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .desc-input { width: 100%; background: #111827; color: #e5e7eb; border: 1px solid #253049; border-radius: 6px; padding: 6px 8px; font-size: 13px; margin-bottom: 6px; }
        .desc-input:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.25); }

        /* New header layout for IO cards */
        .io-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; }
        .io-title-wrap { display:flex; align-items:center; gap:8px; }
        .status-dot-mini { width:8px; height:8px; border-radius:50%; background:#6b7280; }
        .status-dot-mini.on { background:#22c55e; }
        .status-dot-mini.off { background:#ef4444; }
        .status-dot-mini.error { background:#f59e0b; }
        .io-title { font-weight:800; font-size:14px; color:#e5e7eb; }
        .io-tag { color:#94a3b8; font-size:11px; }
        .value-badge { min-width:64px; text-align:right; font-weight:800; padding:6px 8px; border-radius:8px; background:#111827; border:1px solid #1f2937; }
        .value-badge.on { color:#16a34a; }
        .value-badge.off { color:#dc2626; }
        .value-badge.number { color:#0ea5e9; }
        .io-footer { display:flex; justify-content:space-between; align-items:center; margin-top:6px; }
        .type-label { color:#94a3b8; font-size:11px; }
        .refresh-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            padding: 10px;
            background: #0b1220;
            border: 1px solid #1f2937;
            border-radius: 8px;
            color: #94a3b8;
        }
        .refresh-info span { color: #94a3b8; font-size: 12px; }
        .event-log-section { margin: 20px 0; border: 1px solid #1f2937; border-radius: 12px; background: #0f172a; box-shadow: 0 1px 3px rgba(2,6,23,.5); }
        .event-log-header { background: #0b1220; padding: 10px 15px; border-bottom: 1px solid #1f2937; font-weight: 700; color: #e5e7eb; border-top-left-radius: 12px; border-top-right-radius: 12px; }
        .event-log-content {
            max-height: min(40vh, 360px);
            overflow-y: auto;
            overflow-x: hidden;
            padding: 10px 12px 10px 10px;
            scrollbar-gutter: stable both-edges;
            scrollbar-color: #1f2937 #0b1220; /* Firefox */
            scrollbar-width: thin;           /* Firefox */
        }
        .event-log-content::-webkit-scrollbar { width: 8px; }
        .event-log-content::-webkit-scrollbar-track { background: #0b1220; border-radius: 8px; }
        .event-log-content::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 8px; }
        .event-log-content::-webkit-scrollbar-thumb:hover { background: #374151; }
        .event-item {
            padding: 3px 0;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            font-size: 12px;
            border-bottom: 1px solid #1f2937;
            color: #e5e7eb;
        }
        .event-item:last-child {
            border-bottom: none;
        }
        .no-events {
            padding: 20px;
            text-align: center;
            color: #94a3b8;
            font-style: italic;
        }
        /* Grouped IO styles */
        .group-item { margin: 10px 0; }
        .group-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
        .group-title { font-weight: bold; font-size: 16px; }
        .group-children { display: none; margin-left: 10px; }
        .toggle-btn { font-size: 12px; padding: 4px 8px; }
        /* Improved parent-with-children card */
        .group-parent { position: relative; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
        .card-title { font-weight: 700; font-size: 13px; color: #e5e7eb; }
        .details-toggle { background: none; border: none; color: #60a5fa; cursor: pointer; padding: 0; font-size: 12px; }
        .details-toggle:hover { text-decoration: underline; }
        .child-list { display: none; margin-top: 8px; border-top: 1px dashed #e5e7eb; padding-top: 8px; }
        .child-chip { background: #0f172a; border: 1px solid #1f2937; border-radius: 8px; padding: 8px; margin-bottom: 8px; }
        .child-chip .chip-name { font-weight: 700; font-size: 12px; color: #e5e7eb; }
        .child-chip .chip-value { font-weight: 600; margin-left: 6px; }
        .child-chip .chip-address { display: block; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; color: #6b7280; font-size: 11px; }
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
        
        <div class="section-card panel" id="dashboardPanel" style="grid-column: 1 / -1;">
        <div class="panel-header">
            <div>
                <span class="panel-title">Dashboard</span>
                <span class="panel-subtitle">Live view of PLC status and insights</span>
            </div>
            <div class="quick-actions">
                <button class="collapse-btn" onclick="toggleSection('metricsSection', this)">Hide</button>
                <input class="search-input" id="filterInput" placeholder="Filter IO (e.g., A1, Red, PWM)" oninput="applyFilter()">
                <button class="btn" onclick="refreshIOStatus()">Refresh All</button>
            </div>
        </div>
        <div class="panel-body" id="metricsSection">
        <div class="metrics">
            <div class="metric">
                <h3>{{ data_points }}</h3>
                <p>Events Today</p>
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
        </div>
        </div>
        
        <div class="section-card panel" id="liveIoPanel" style="grid-column: 1 / -1;">
        <div class="panel-header">
            <div class="panel-title">Live IO Status</div>
            <div class="quick-actions">
                <button class="collapse-btn" onclick="toggleSection('liveIoSection', this)">Hide</button>
                <button class="btn" onclick="refreshIOStatus()" style="background-color: #28a745;">Refresh</button>
                <span id="lastUpdate" class="panel-subtitle">Last update: Never</span>
            </div>
        </div>
        <div class="panel-body io-status-container" id="liveIoSection">
            <div id="ioGroupsContainer">
                <!-- Grouped IO status will be inserted here -->
            </div>
        </div>
        </div>
        
        <div class="event-log-section section-card panel" id="events">
            <div class="panel-header">
                <div class="panel-title">Recent Events</div>
                <div class="quick-actions">
                    <button class="btn" onclick="refreshEventLog()">Refresh</button>
                    <button class="btn" onclick="clearEventLog()" style="background-color:#dc3545;">Clear</button>
                </div>
            </div>
            <div class="panel-body event-log-content" id="eventLogContent">
                <div class="no-events">Loading events...</div>
            </div>
        </div>
        
        <div class="ai-section section-card panel" id="ai">
            <div class="panel-header">
                <div class="panel-title">AI Analysis with Gemma3 1B</div>
                <div class="panel-subtitle">Ask questions about the PLC system status</div>
                <div class="quick-actions">
                    <button class="collapse-btn" onclick="toggleSection('aiSectionBody', this)">Hide</button>
                </div>
            </div>
            <div class="panel-body" id="aiSectionBody">
            
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
        </div>
        
        <!-- Technical info box removed per request to keep the home page clean -->
    </div>
    
    <script>
        // Simple collapsible sections
        function toggleSection(bodyId, btn){
            const el = document.getElementById(bodyId);
            if(!el) return;
            const isHidden = el.style.display === 'none';
            el.style.display = isHidden ? '' : 'none';
            if(btn){ btn.textContent = isHidden ? 'Hide' : 'Show'; }
        }
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
                 // Use the pre-formatted change description from the event logger
                 // The event logger already handles all the formatting logic correctly
                 let change = event.change_description || 'Unknown change';
                 
                 html += `<div class="event-item">${event.formatted_time} - ${event.io_name}: ${change}</div>`;
             });
             
             if (html === '') {
                 eventLogContent.innerHTML = '<div class="no-events">No events recorded yet</div>';
             } else {
                 eventLogContent.innerHTML = html;
             }
         }
        
        function refreshIOStatus() {
            fetch('/get_io_status')
            .then(response => response.json())
            .then(data => {
                lastIoData = data.io_data || {};
                updateGroupedIO(data.io_data, data.io_groups);
                document.getElementById('lastUpdate').textContent = 'Last update: ' + new Date().toLocaleTimeString();
            })
            .catch(error => {
                console.error('Error refreshing IO status:', error);
                document.getElementById('lastUpdate').textContent = 'Last update: Error - ' + new Date().toLocaleTimeString();
            });
        }

        // Toggle details row by id
        function toggleDetails(id){
            const row = document.getElementById(id);
            if (!row) return;
            const isHidden = row.style.display === 'none' || row.style.display === '';
            row.style.display = isHidden ? 'table-row' : 'none';
        }

        function formatIoValue(info) {
            const v = info.value;
            if (v === null || v === undefined) return 'ERROR';
            if (info.type === 'bit') return v ? 'ON' : 'OFF';
            if (info.type === 'real') {
                const num = typeof v === 'number' ? v : parseFloat(v);
                if (!isNaN(num)) return num.toFixed(2);
            }
            return v.toString();
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
            let valueDisplay = formatIoValue(ioInfo);
            const safeDesc = (ioInfo.description || '').toString();
            const descEditorHtml = `<input class="desc-input" type="text" value="${safeDesc.replace(/"/g,'&quot;')}" placeholder="Edit description and press Enter" onkeydown="if(event.key==='Enter'){updateDesc('${ioName}', this.value)}">`;
            const dotClass = ioInfo.status === 'error' ? 'error' : (ioInfo.type === 'bit' ? (ioInfo.value ? 'on' : 'off') : '');
            const header = `
                <div class="io-header">
                    <div class="io-title-wrap">
                        <span class="status-dot-mini ${dotClass}"></span>
                        <div>
                            <div class="io-title">${safeDesc || ioName}</div>
                            <div class="io-tag">${ioName}</div>
                        </div>
                    </div>
                    <div class="value-badge ${valueClass}">${valueDisplay}</div>
                </div>`;
            const footer = `
                <div class="io-footer">
                    <span class="type-label">${ioInfo.type.toUpperCase()}</span>
                    <span class="io-address">${ioInfo.address}</span>
                </div>`;
            card.innerHTML = `${header}${descEditorHtml}${footer}`;
            return card;
        }

        // Update description mapping (simple client call)
        function updateDesc(ioName, newDesc) {
            fetch('/update_io_mapping', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ io_name: ioName, io_type: getIoType(ioName), io_address: getIoAddress(ioName), io_description: newDesc })
            }).then(r => r.json()).then(data => {
                refreshIOStatus();
            }).catch(e => console.error('Error updating description', e));
        }

        // Helpers to read current type/address from last response cache
        let lastIoData = {};
        function getIoType(name){ return (lastIoData[name] && lastIoData[name].type) || 'bit'; }
        function getIoAddress(name){ return (lastIoData[name] && lastIoData[name].address) || ''; }

        function renderParentWithChildren(parentName, childNames, ioData) {
            const wrapper = document.createElement('div');
            wrapper.className = 'io-card group-parent';

            // Build header with inline toggle link
            const header = document.createElement('div');
            header.className = 'card-header';
            const title = document.createElement('div');
            title.className = 'card-title';
            title.textContent = parentName;
            const toggle = document.createElement('button');
            toggle.className = 'details-toggle';
            toggle.textContent = 'Show details';
            header.appendChild(title);
            header.appendChild(toggle);
            wrapper.appendChild(header);

            // Insert parent main card visuals beneath header
            if (ioData[parentName]) {
                const main = renderCard(parentName, ioData[parentName]);
                main.style.marginTop = '8px';
                wrapper.appendChild(main);
            }

            // Child list as compact chips
            const childList = document.createElement('div');
            childList.className = 'child-list';
            (childNames || []).forEach(n => {
                if (!ioData[n]) return;
                const info = ioData[n];
                const chip = document.createElement('div');
                chip.className = 'child-chip';
                const name = document.createElement('span');
                name.className = 'chip-name';
                name.textContent = n;
                const val = document.createElement('span');
                val.className = 'chip-value ' + (info.type === 'bit' ? (info.value ? 'on' : 'off') : 'number');
                val.textContent = formatIoValue(info);
                const addr = document.createElement('span');
                addr.className = 'chip-address';
                addr.textContent = info.address;
                chip.appendChild(name);
                chip.appendChild(val);
                chip.appendChild(addr);
                childList.appendChild(chip);
            });
            wrapper.appendChild(childList);

            toggle.addEventListener('click', function() {
                const visible = childList.style.display === 'block';
                childList.style.display = visible ? 'none' : 'block';
                toggle.textContent = visible ? 'Show details' : 'Hide details';
            });

            return wrapper;
        }

        function updateGroupedIO(ioData, ioGroups) {
            const groupsContainer = document.getElementById('ioGroupsContainer');
            groupsContainer.innerHTML = '';

            const filter = (document.getElementById('filterInput')?.value || '').toLowerCase();
            const used = new Set();

            function buildTable(title, names) {
                if (!names || names.length === 0) return;
                const section = document.createElement('div');
                section.className = 'section';
                const h3 = document.createElement('h3');
                h3.textContent = title;
                section.appendChild(h3);

                // No table controls; container will scroll showing ~10 rows

                // Create scrollable container
                const tableContainer = document.createElement('div');
                tableContainer.className = 'table-container';

                const table = document.createElement('table');
                table.className = 'io-table';
                table.innerHTML = `<thead><tr>
                    <th style=\"width:70%\">Description</th>
                    <th style=\"width:30%\">Value</th>
                </tr></thead>`;
                const tbody = document.createElement('tbody');

                if (title === 'Analogue Inputs') {
                    const buckets = {};
                    (names||[]).forEach(n=>{ const base=n.split('_')[0]; (buckets[base]=buckets[base]||[]).push(n); });
                    Object.entries(buckets).forEach(([base, list]) => {
                        const scaledName = `${base}_Scaled`;
                        const rawName = `${base}_Raw`;
                        const offsetName = `${base}_Offset`;
                        const scalarName = `${base}_Scalar`;
                        const mainName = list.includes(scaledName) ? scaledName : list[0];
                        const info = ioData[mainName];
                        if (!info) return;
                        used.add(mainName);
                        const desc = (info.description||'').toString();
                        if (filter && !(mainName.toLowerCase().includes(filter) || desc.toLowerCase().includes(filter))) return;
                        const tr = document.createElement('tr');
                        const valueDisplay = formatIoValue(info);
                        let valueClass = info.type === 'bit' ? (info.value ? 'on':'off') : 'number';
                        if (info.type !== 'bit') {
                            const num = parseFloat(valueDisplay);
                            if (!isNaN(num)) valueClass += (num >= 0 ? ' nonneg' : ' neg');
                        }
                        const statusDot = `<span class=\"status-dot-mini ${info.status==='error'?'error':(info.type==='bit'?(info.value?'on':'off'):'')}\"></span>`;
                        // Subchips
                        const rawInfo = ioData[rawName]; if (rawInfo) used.add(rawName);
                        const offInfo = ioData[offsetName]; if (offInfo) used.add(offsetName);
                        const sclInfo = ioData[scalarName]; if (sclInfo) used.add(scalarName);
                        const sub = `
                            <div class=\"subchips\">
                                ${rawInfo?`<span class=\"subchip\">Raw: ${formatIoValue(rawInfo)}</span>`:''}
                                ${offInfo?`<span class=\"subchip\">Offset: ${formatIoValue(offInfo)}</span>`:''}
                                ${sclInfo?`<span class=\"subchip\">Scalar: ${formatIoValue(sclInfo)}</span>`:''}
                            </div>`;
                        const valueStateClass = info.status==='error'?'error':(info.value===null?'offline':'');
                        const detailsId = `details_${mainName.replace(/[^a-zA-Z0-9_]/g,'_')}`;
                        tr.innerHTML = `
                            <td>
                                <div class=\"desc-inline\">
                                    <span class=\"desc-text\" contenteditable=\"true\" onkeydown=\"if(event.key==='Enter'){event.preventDefault();updateDesc('${mainName}', this.innerText.trim())}\">${(desc||'').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</span>
                                    <button class=\"details-toggle-btn\" onclick=\"toggleDetails('${detailsId}')\">Details</button>
                                </div>
                                ${sub}
                            </td>
                            <td class=\"value-cell ${valueClass} ${valueStateClass}\">${info.status==='error'?'error':(info.value===null?'offline':valueDisplay)}</td>
                        `;
                        // Details row
                        const dtr = document.createElement('tr');
                        dtr.className = 'details-row';
                        dtr.id = detailsId;
                        dtr.style.display = 'none';
                        dtr.innerHTML = `
                            <td colspan=\"3\">
                                <div class=\"details-box\">
                                    <div><span class=\"detail-label\">IO Tag</span><span class=\"detail-value mono\">${mainName}</span></div>
                                    <div><span class=\"detail-label\">Type</span><span class=\"detail-value\">${(info.type||'').toUpperCase()}</span></div>
                                    <div><span class=\"detail-label\">Address</span><span class=\"detail-value mono\">${info.address||''}</span></div>
                                </div>
                            </td>`;
                        tbody.appendChild(tr);
                        tbody.appendChild(dtr);
                    });
                } else if (title === 'Digital Inputs' || title === 'Digital Outputs') {
                    const buckets = {};
                    (names||[]).forEach(n=>{
                        const parts=n.split('_');
                        const base = parts[0]==='Out' && parts.length>1 ? `Out_${parts[1]}` : parts[0];
                        (buckets[base]=buckets[base]||[]).push(n);
                    });
                    Object.entries(buckets).forEach(([base, list]) => {
                        const stateName = list.find(n=>/_State$/i.test(n)) || list[0];
                        const info = ioData[stateName];
                        if (!info) return;
                        used.add(stateName);
                        const desc = (info.description||'').toString();
                        if (filter && !(stateName.toLowerCase().includes(filter) || desc.toLowerCase().includes(filter))) return;
                        const tr = document.createElement('tr');
                        const valueDisplay = formatIoValue(info);
                        let valueClass = info.type === 'bit' ? (info.value ? 'on':'off') : 'number';
                        if (info.type !== 'bit') {
                            const num = parseFloat(valueDisplay);
                            if (!isNaN(num)) valueClass += (num >= 0 ? ' nonneg' : ' neg');
                        }
                        const statusDot = `<span class=\"status-dot-mini ${info.status==='error'?'error':(info.type==='bit'?(info.value?'on':'off'):'')}\"></span>`;
                        const forcedState = ioData[`${base}_ForcedState`]; if (forcedState) used.add(`${base}_ForcedState`);
                        const forcedStatus = ioData[`${base}_ForcedStatus`]; if (forcedStatus) used.add(`${base}_ForcedStatus`);
                        const sub = `
                            <div class=\"subchips\">
                                ${forcedState?`<span class=\"subchip\">ForcedState: ${formatIoValue(forcedState)}</span>`:''}
                                ${forcedStatus?`<span class=\"subchip\">ForcedStatus: ${formatIoValue(forcedStatus)}</span>`:''}
                            </div>`;
                        const valueStateClass2 = info.status==='error'?'error':(info.value===null?'offline':'');
                        const detailsId2 = `details_${stateName.replace(/[^a-zA-Z0-9_]/g,'_')}`;
                        tr.innerHTML = `
                            <td>
                                <div class=\"desc-inline\">
                                    <span class=\"desc-text\" contenteditable=\"true\" onkeydown=\"if(event.key==='Enter'){event.preventDefault();updateDesc('${stateName}', this.innerText.trim())}\">${(desc||'').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</span>
                                    <button class=\"details-toggle-btn\" onclick=\"toggleDetails('${detailsId2}')\">Details</button>
                                </div>
                                ${sub}
                            </td>
                            <td class=\"value-cell ${valueClass} ${valueStateClass2}\">${info.status==='error'?'error':(info.value===null?'offline':valueDisplay)}</td>
                        `;
                        const dtr = document.createElement('tr');
                        dtr.className = 'details-row';
                        dtr.id = detailsId2;
                        dtr.style.display = 'none';
                        dtr.innerHTML = `
                            <td colspan=\"3\">
                                <div class=\"details-box\">
                                    <div><span class=\"detail-label\">IO Tag</span><span class=\"detail-value mono\">${stateName}</span></div>
                                    <div><span class=\"detail-label\">Type</span><span class=\"detail-value\">${(info.type||'').toUpperCase()}</span></div>
                                    <div><span class=\"detail-label\">Address</span><span class=\"detail-value mono\">${info.address||''}</span></div>
                                </div>
                            </td>`;
                        tbody.appendChild(tr);
                        tbody.appendChild(dtr);
                    });
                } else {
                    (names||[]).forEach(name => {
                        const info = ioData[name];
                        if (!info) return;
                        used.add(name);
                        const desc = (info.description||'').toString();
                        if (filter && !(name.toLowerCase().includes(filter) || desc.toLowerCase().includes(filter))) return;
                        const tr = document.createElement('tr');
                        const valueDisplay = formatIoValue(info);
                        let valueClass = info.type === 'bit' ? (info.value ? 'on':'off') : 'number';
                        if (info.type !== 'bit') {
                            const num = parseFloat(valueDisplay);
                            if (!isNaN(num)) valueClass += (num >= 0 ? ' nonneg' : ' neg');
                        }
                        const statusDot = `<span class=\"status-dot-mini ${info.status==='error'?'error':(info.type==='bit'?(info.value?'on':'off'):'')}\"></span>`;
                        const valueStateClass3 = info.status==='error'?'error':(info.value===null?'offline':'');
                        const detailsId3 = `details_${name.replace(/[^a-zA-Z0-9_]/g,'_')}`;
                        tr.innerHTML = `
                            <td>
                                <div class=\"desc-inline\">
                                    <span class=\"desc-text\" contenteditable=\"true\" onkeydown=\"if(event.key==='Enter'){event.preventDefault();updateDesc('${name}', this.innerText.trim())}\">${(desc||'').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</span>
                                    <button class=\"details-toggle-btn\" onclick=\"toggleDetails('${detailsId3}')\">Details</button>
                                </div>
                            </td>
                            <td class=\"value-cell ${valueClass} ${valueStateClass3}\">${info.status==='error'?'error':(info.value===null?'offline':valueDisplay)}</td>
                        `;
                        const dtr = document.createElement('tr');
                        dtr.className = 'details-row';
                        dtr.id = detailsId3;
                        dtr.style.display = 'none';
                        dtr.innerHTML = `
                            <td colspan=\"3\">
                                <div class=\"details-box\">
                                    <div><span class=\"detail-label\">IO Tag</span><span class=\"detail-value mono\">${name}</span></div>
                                    <div><span class=\"detail-label\">Type</span><span class=\"detail-value\">${(info.type||'').toUpperCase()}</span></div>
                                    <div><span class=\"detail-label\">Address</span><span class=\"detail-value mono\">${info.address||''}</span></div>
                                </div>
                            </td>`;
                        tbody.appendChild(tr);
                        tbody.appendChild(dtr);
                    });
                }

                table.appendChild(tbody);
                tableContainer.appendChild(table);
                section.appendChild(tableContainer);
                // Append completed section to the main groups container
                groupsContainer.appendChild(section);
                
                // After inserting into DOM, size container to fit ~10 rows + header
                try {
                    const headerEl = table.querySelector('thead');
                    const rowEls = Array.from(tbody.querySelectorAll('tr'));
                    let heightPx = (headerEl ? headerEl.offsetHeight : 0);
                    const visibleCount = Math.min(10, rowEls.length);
                    for (let i = 0; i < visibleCount; i++) {
                        heightPx += rowEls[i].offsetHeight || 0;
                    }
                    tableContainer.style.maxHeight = (heightPx || 400) + 'px';
                    tableContainer.style.overflowY = 'auto';
                } catch (e) { /* fallback to CSS max-height */ }

                // Enable client-side sorting via Tablesort (simple, offline)
                try {
                    table.querySelectorAll('th').forEach(th => th.classList.add('ts-header'));
                    if (window.Tablesort) { new Tablesort(table); }
                } catch (e) { /* optional */ }
            }

            // Priority groups
            const aiNames = (ioGroups && ioGroups['Analogue Inputs']) || [];
            const diNames = (ioGroups && ioGroups['Digital Inputs']) || [];
            const doNames = (ioGroups && ioGroups['Digital Outputs']) || [];

            buildTable('Analogue Inputs', aiNames);
            buildTable('Digital Inputs', diNames);
            buildTable('Digital Outputs', doNames);

            // Others: everything not used
            const otherNames = Object.keys(ioData||{}).filter(n => !used.has(n));
            buildTable('Others', otherNames);
        }

        function applyFilter(){ refreshIOStatus(); }
        
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
            const ioGridExists = document.getElementById('ioGroupsContainer');
            if (ioGridExists) { refreshIOStatus(); }
            const logExists = document.getElementById('eventLogContent');
            if (logExists) { refreshEventLog(); }
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
    <script src="/static/vendor/tablesort.min.js"></script>
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
        
        # On first successful read, log a full system snapshot so the log isn't empty
        if plc_connected and not event_logger.initial_snapshot_logged:
            event_logger.log_system_snapshot(io_data)

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
        # Clear the events by writing an empty array to the actual log file in data/
        import json
        from event_logger import event_logger as _ev
        with open(_ev.log_file, 'w') as f:
            json.dump([], f)
        
        return jsonify({'status': 'success', 'message': 'Event log cleared successfully'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500



if __name__ == '__main__':
    # Ensure folders exist for static assets
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static'), exist_ok=True)
    app.run(host='127.0.0.1', port=5001, debug=True)
