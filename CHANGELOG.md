# Changelog

All notable changes to the E-Stop AI Status Reporter project will be documented in this file.

## [1.1.0] - 2025-08-10

### Added
- IO grouping on Dashboard with collapsible sub-parts:
  - Digital groups show `<AX_State>` as the parent; `ForcedState`/`ForcedStatus` are hidden under a toggle
  - Analogue groups show `<AIx_Scaled>` as the parent; `Offset`/`Scalar` are hidden under a toggle
- Group management UI on the PLC Configuration page (create, edit, delete groups)
- API endpoints for groups: `GET /get_io_groups`, `POST /update_io_group`, `POST /remove_io_group`
- Support for 32-bit Real (float) values (`type: "real"`) in PLC reads
- Favicon support; pages now link to `/static/favicon.ico`

### Changed
- Persistent PLC connection reused across requests (reduces console spam and overhead)
- Config and logs are now stored under `data/` (`data/plc_config.json`, `data/io_events.json`)
- README updated: Real type documented, file structure and deploy paths clarified

### Removed
- Home page “Data Structure” box for a cleaner UI
- Unused CSV files and leftover scripts no longer used by the app

### Fixed
- Prevented JavaScript errors from null DOM references on pages without certain elements
- Improved IO status rendering robustness and grouping logic

## [1.0.0] - 2024-12-19

### Added
- **Core Application**: Flask-based web application for PLC monitoring
- **PLC Communication**: Full integration with Siemens S7 PLCs using python-snap7
- **AI Integration**: Local AI analysis using Ollama with Gemma3 1B model
- **Real-time Monitoring**: Live IO status updates and system health monitoring
- **E-Stop Detection**: Automatic detection and reporting of emergency stop events
- **Event Logging**: Comprehensive event logging system with JSON storage
- **Web Interface**: Modern, responsive web interface with real-time updates
- **Configuration Management**: Web-based PLC configuration and IO mapping
- **Interactive Visualizations**: Real-time charts and system status displays

### Features
- **PLC Data Types Support**: Bit (DBX), Byte (DBB), Word (DBW), DWord (DBD)
- **Configurable IO Mapping**: Easy web interface to configure PLC addresses
- **Connection Testing**: Built-in PLC connection testing and validation
- **AI-Powered Analysis**: Intelligent operator reports and system insights
- **Event Statistics**: Comprehensive event tracking and statistics
- **Mobile-Responsive Design**: Works on desktop and mobile devices

### Technical Implementation
- **Backend**: Python Flask web server
- **PLC Communication**: python-snap7 library for S7 protocol
- **AI Engine**: Local Ollama server with Gemma3 1B model
- **Data Storage**: JSON-based configuration and event logging
- **Frontend**: HTML/CSS/JavaScript with real-time updates
- **Visualization**: Plotly charts for data visualization

### Configuration
- **PLC Settings**: IP address, rack, slot configuration
- **IO Mapping**: Configurable address mapping for all data types
- **AI Prompts**: Customizable AI analysis prompts
- **Event Logging**: Configurable event tracking and retention

### Deployment
- **Cross-Platform**: Works on Windows, Linux, and Raspberry Pi
- **Service Integration**: Systemd service for Linux/Raspberry Pi
- **Auto-start**: Desktop autostart configuration
- **Dependencies**: Minimal Python dependencies for easy deployment

### Removed
- **Test Scripts**: Cleaned up all development test scripts
- **Development Files**: Removed temporary testing and development files

### Fixed
- **Code Cleanup**: Removed all test scripts and development artifacts
- **Documentation**: Updated README with proper installation and usage instructions
- **Project Structure**: Streamlined project structure for production use

## [0.9.0] - Development Phase

### Development Phases Completed
- **Phase 1**: Foundation with CSV data and basic Flask app ✅
- **Phase 2**: PLC integration with python-snap7 ✅
- **Phase 3**: Real-time monitoring and E-Stop detection ✅
- **Phase 4**: AI integration and event logging ✅

### Next Steps
- **Phase 5**: Production deployment and advanced features
- **Enhancement**: Additional AI models and analysis capabilities
- **Integration**: SCADA system integration
- **Security**: Enhanced security measures and authentication
