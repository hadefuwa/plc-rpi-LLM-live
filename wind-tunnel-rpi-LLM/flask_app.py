from flask import Flask, render_template_string, request, jsonify
import pandas as pd
import json
import requests

app = Flask(__name__)

# Load data
data = pd.read_csv('wind_tunnel_test_data.csv')

def query_ollama(prompt, data_summary):
    """Send query to local Ollama API with Gemma3 1B model"""
    try:
        # Prepare the full prompt with data context
        full_prompt = f"""You are analyzing wind tunnel test data. Here is the dataset summary:

{data_summary}

User question: {prompt}

Please provide a clear, CONCISE technical analysis based on this aerodynamic data. Keep your response brief (2-3 sentences max). Focus on key relationships between angle of attack (AoA), lift, drag, and aerodynamic coefficients (Cl, Cd). Be direct and specific."""

        # Ollama API call
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3:1b",  # Using Gemma3 1B model
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
    <title>Wind Tunnel Data Explorer</title>
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
        <h1>Wind Tunnel Data Explorer with AI Analysis</h1>
        <p>Analyze wind tunnel test data with interactive visualizations and AI insights using Gemma3 1B</p>
        
        <h2>Dataset Overview</h2>
        <div class="metrics">
            <div class="metric">
                <h3>{{ data_points }}</h3>
                <p>Total Data Points</p>
            </div>
            <div class="metric">
                <h3>{{ aoa_min }}° to {{ aoa_max }}°</h3>
                <p>AoA Range</p>
            </div>
            <div class="metric">
                <h3>{{ max_cl }}</h3>
                <p>Max Lift Coefficient</p>
            </div>
        </div>
        
        <h2>Raw Data</h2>
        {{ data_table|safe }}
        
        <h2>Interactive Visualizations</h2>
        <div id="plot1" class="plot"></div>
        <div id="plot2" class="plot"></div>
        <div id="plot3" class="plot"></div>
        <div id="plot4" class="plot"></div>
        
        <div class="ai-section">
            <h2>AI Analysis with Gemma3</h2>
            <p>Ask questions about the wind tunnel data and get AI-powered insights!</p>
            
            <div>
                <strong>Example Questions:</strong><br>
                <button class="example-btn" onclick="setQuestion('What is the optimal angle of attack for maximum lift?')">Optimal AoA for max lift?</button>
                <button class="example-btn" onclick="setQuestion('At what angle does stall occur?')">Stall angle?</button>
                <button class="example-btn" onclick="setQuestion('What is the lift-to-drag ratio at different angles?')">L/D ratio analysis</button>
                <button class="example-btn" onclick="setQuestion('Explain the aerodynamic behavior shown in this data')">Aerodynamic behavior</button>
                <button class="example-btn" onclick="setQuestion('What angle of attack gives the best efficiency?')">Best efficiency angle</button>
            </div>
            
            <input type="text" id="questionInput" class="chat-input" placeholder="e.g., What is the relationship between angle of attack and lift coefficient?" />
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
                <li>AoA (deg): Angle of Attack in degrees</li>
                <li>Lift (mN): Lift force in millinewtons</li>
                <li>Cl: Lift coefficient (dimensionless)</li>
                <li>Drag (mN): Drag force in millinewtons</li>
                <li>Cd: Drag coefficient (dimensionless)</li>
            </ul>
            <p><strong>AI Model:</strong> Gemma3 1B running locally via Ollama<br>
            <strong>Visualization:</strong> Interactive Plotly charts<br>
            <strong>Framework:</strong> Flask</p>
        </div>
    </div>
    
    <script>
        window.plotData = {
            aoa: {{ aoa_json|safe }},
            lift: {{ lift_json|safe }},
            drag: {{ drag_json|safe }},
            cl: {{ cl_json|safe }},
            cd: {{ cd_json|safe }}
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
            
            // Lift vs AoA
            Plotly.newPlot('plot1', [{
                x: data.aoa, y: data.lift,
                mode: 'lines+markers', name: 'Lift',
                line: {color: '#007bff'}, marker: {color: '#007bff'}
            }], {
                title: 'Lift vs Angle of Attack',
                xaxis: {title: 'Angle of Attack (degrees)'},
                yaxis: {title: 'Lift (mN)'}
            });
            
            // Drag vs AoA
            Plotly.newPlot('plot2', [{
                x: data.aoa, y: data.drag,
                mode: 'lines+markers', name: 'Drag',
                line: {color: '#dc3545'}, marker: {color: '#dc3545'}
            }], {
                title: 'Drag vs Angle of Attack',
                xaxis: {title: 'Angle of Attack (degrees)'},
                yaxis: {title: 'Drag (mN)'}
            });
            
            // Polar diagram
            Plotly.newPlot('plot3', [{
                x: data.cd, y: data.cl,
                mode: 'lines+markers', name: 'Polar',
                line: {color: '#28a745'}, marker: {color: '#28a745'}
            }], {
                title: 'Lift-Drag Polar Diagram',
                xaxis: {title: 'Drag Coefficient (Cd)'},
                yaxis: {title: 'Lift Coefficient (Cl)'}
            });
            
            // Coefficients
            Plotly.newPlot('plot4', [{
                x: data.aoa, y: data.cl,
                mode: 'lines+markers', name: 'Cl',
                line: {color: '#007bff'}, marker: {color: '#007bff'}
            }, {
                x: data.aoa, y: data.cd,
                mode: 'lines+markers', name: 'Cd', yaxis: 'y2',
                line: {color: '#ffc107'}, marker: {color: '#ffc107'}
            }], {
                title: 'Aerodynamic Coefficients vs Angle of Attack',
                xaxis: {title: 'Angle of Attack (degrees)'},
                yaxis: {title: 'Lift Coefficient (Cl)'},
                yaxis2: {title: 'Drag Coefficient (Cd)', overlaying: 'y', side: 'right'}
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
    return render_template_string(template,
        data_points=len(data),
        aoa_min=data['AoA (deg)'].min(),
        aoa_max=data['AoA (deg)'].max(),
        max_cl=f"{data['Cl'].max():.3f}",
        data_table=data.to_html(classes='table', table_id='data-table'),
        aoa_json=json.dumps(data['AoA (deg)'].tolist()),
        lift_json=json.dumps(data['Lift (mN)'].tolist()),
        drag_json=json.dumps(data['Drag (mN)'].tolist()),
        cl_json=json.dumps(data['Cl'].tolist()),
        cd_json=json.dumps(data['Cd'].tolist())
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
    
    # Prepare data summary for AI
    data_summary = f"""
    Wind Tunnel Test Data Summary:
    - Data Points: {len(data)}
    - Angle of Attack Range: {data['AoA (deg)'].min()}° to {data['AoA (deg)'].max()}°
    - Lift Range: {data['Lift (mN)'].min():.1f} to {data['Lift (mN)'].max():.1f} mN
    - Drag Range: {data['Drag (mN)'].min():.1f} to {data['Drag (mN)'].max():.1f} mN
    - Lift Coefficient Range: {data['Cl'].min():.3f} to {data['Cl'].max():.3f}
    - Drag Coefficient Range: {data['Cd'].min():.3f} to {data['Cd'].max():.3f}
    
    Key Data Points:
    {data.to_string(index=False)}
    """
    
    response = query_ollama(question, data_summary)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8501, debug=True)
