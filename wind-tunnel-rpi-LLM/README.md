# Wind Tunnel Data Explorer with AI Analysis

A powerful Flask web application for analyzing wind tunnel aerodynamic test data with AI-powered insights. Features interactive visualizations and intelligent chat interface powered by the Gemma3 1B language model running locally via Ollama.

## What This App Does

This Flask application provides a comprehensive platform for aerodynamic data analysis with:

- **Interactive Data Visualization**: Four different chart types showing aerodynamic relationships
- **AI-Powered Analysis**: Ask natural language questions about your wind tunnel data
- **Expert Insights**: Get technical explanations of aerodynamic phenomena
- **Educational Tool**: Perfect for students and engineers learning aerodynamics
- **Privacy-First**: All AI processing happens locally on your device

## Key Features

### Data Visualization
- **Lift vs Angle of Attack**: See how lift force changes with wing angle
- **Drag vs Angle of Attack**: Analyze drag characteristics across angles
- **Lift-Drag Polar Diagram**: Classical aerodynamic performance plot
- **Coefficient Analysis**: Compare lift (Cl) and drag (Cd) coefficients

### AI Chat Interface
- Ask questions in plain English about your data
- Get concise, technical explanations (2-3 sentences)
- Example queries:
  - "What is the optimal angle of attack for maximum lift?"
  - "At what angle does stall occur?"
  - "What's the best lift-to-drag ratio?"
  - "Explain the aerodynamic behavior in this data"

### Technical Specifications
- **Framework**: Flask web application for universal compatibility
- **AI Model**: Gemma3 1B (815MB) - optimized for local deployment
- **Visualizations**: Interactive Plotly.js charts
- **Data Format**: Standard aerodynamic CSV format
- **Deployment**: Raspberry Pi ready with ARM compatibility

## Quick Start

### Prerequisites
- Python 3.8+
- Ollama (for AI functionality)
- 4GB+ RAM recommended (8GB for Raspberry Pi)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/hadefuwa/wind-tunnel-rpi-LLM.git
cd wind-tunnel-rpi-LLM
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Install and setup Ollama**
```bash
# Linux/macOS/Raspberry Pi
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from https://ollama.ai
# Then pull the AI model:
ollama pull gemma3:1b
```

4. **Run the Flask application**
```bash
# Windows
python flask_app.py

# Linux/macOS/Raspberry Pi
python3 flask_app.py
```

5. **Open in browser**: http://localhost:5000

## Easy Startup Scripts

### Windows
```bash
# Double-click or run:
run.bat
```

### Linux/macOS/Raspberry Pi
```bash
# Make executable and run:
chmod +x run.sh
./run.sh
```

## Data Format

Your CSV file should be named `wind_tunnel_test_data.csv` with these columns:

| Column | Description | Units |
|--------|-------------|-------|
| `AoA (deg)` | Angle of Attack | degrees |
| `Lift (mN)` | Lift Force | millinewtons |
| `Cl` | Lift Coefficient | dimensionless |
| `Drag (mN)` | Drag Force | millinewtons |
| `Cd` | Drag Coefficient | dimensionless |

Example data structure:
```csv
AoA (deg),Lift (mN),Cl,Drag (mN),Cd
-10,150.2,0.125,45.1,0.038
-5,280.5,0.234,52.3,0.044
0,420.8,0.351,61.2,0.051
5,580.3,0.484,73.8,0.062
10,720.1,0.601,89.5,0.075
```

## Raspberry Pi Deployment

### SSH Installation
```bash
# Copy files to your Pi
scp -r . pi@192.168.0.115:/home/pi/wind-tunnel-app/

# SSH into Pi
ssh pi@192.168.0.115

# Setup and run
cd wind-tunnel-app
./run.sh
```

### Pi Performance Notes
- **Gemma3 1B**: Optimized for Raspberry Pi 4 (8GB RAM)
- **Response Time**: 10-30 seconds per AI query (normal)
- **Memory Usage**: ~2GB for model + 500MB for Flask
- **Cooling**: Ensure adequate ventilation for sustained use

## How the AI Works

The Flask application uses a sophisticated prompt engineering approach:

1. **Data Context**: Automatically includes your complete dataset in AI prompts
2. **Technical Focus**: Prompts are tuned for aerodynamic analysis
3. **Concise Responses**: Limited to 100 tokens (~75 words) for quick insights
4. **Low Temperature**: Set to 0.1 for focused, technical responses
5. **Local Processing**: No data leaves your device

### Sample AI Conversation
**User**: "What angle gives maximum lift?"  
**AI**: "Maximum lift occurs at 15° angle of attack with 850.7 mN force (Cl = 0.709). Beyond this point, flow separation begins causing stall characteristics."

## Flask Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask App     │    │   Ollama API    │
│   (HTML/JS)     │◄───┤   (Python)      │◄───┤   (Gemma3 1B)   │
│   Plotly Charts │    │   Data Analysis │    │   AI Responses  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Components
- **flask_app.py**: Main Flask server with data processing and API endpoints
- **Templates**: Embedded HTML/CSS/JavaScript for clean interface
- **Static Assets**: Plotly.js for interactive visualizations
- **AI Engine**: Local Ollama instance with Gemma3 1B model

### Key Flask Routes
- **`/`**: Main application interface
- **`/chat`**: POST endpoint for AI queries
- **`/test_ai`**: AI connection testing endpoint

## Educational Use Cases

### For Students
- **Learn Aerodynamics**: Visualize how wing angle affects lift and drag
- **Understand Stall**: See stall characteristics in real data
- **Efficiency Analysis**: Explore lift-to-drag ratios
- **Ask Questions**: Natural language interface for exploration

### For Engineers
- **Design Validation**: Analyze wing section performance
- **Optimization**: Find optimal operating points
- **Documentation**: Generate insights for reports
- **Teaching**: Demonstrate concepts with real data

## Troubleshooting

### Common Issues

**Flask app not starting?**
- Check Python installation: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Ensure port 5000 is available

**Charts not loading?**
- Check browser console for JavaScript errors
- Ensure `wind_tunnel_test_data.csv` exists
- Refresh the page

**AI not responding?**
- Verify Ollama is running: `ollama ps`
- Check model is installed: `ollama list | grep gemma3`
- Test connection: Click "Test AI Connection" button

**Slow on Raspberry Pi?**
- Normal behavior - AI processing takes time
- Close other applications to free memory
- Ensure adequate cooling

**Memory issues?**
- Restart Ollama: `sudo systemctl restart ollama`
- Monitor with `htop`
- Consider adding swap space

## Performance Optimization

### For Raspberry Pi
```bash
# Add swap space if needed
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=2048
sudo dphys-swapfile swapon

# Monitor performance
htop
watch -n 1 'free -h'
```

### For All Systems
- **Close unnecessary applications** before running AI queries
- **Use Chrome/Firefox** for best JavaScript performance
- **Wait for responses** - AI processing takes time

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Commit changes: `git commit -m "Add feature"`
5. Push to branch: `git push origin feature-name`
6. Submit pull request

## License

MIT License - feel free to use for educational and commercial purposes.

## Acknowledgments

- **Ollama Team**: For local AI model deployment
- **Google**: For the Gemma3 language model
- **Plotly**: For interactive visualization library
- **Flask**: For lightweight web framework

---

**Built with care for aerodynamics education and research**

*Transform your wind tunnel data into insights with the power of local AI and Flask*
