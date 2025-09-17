# 🏠 Home Assistant AI Bridge with Enhanced Voice Camera Control

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

A comprehensive smart home automation platform featuring AI-powered voice commands, camera control, and a beautiful web interface. Designed for Proxmox deployment with production-grade configurations.

## ✨ Key Features

### 🎙️ **Advanced Voice Control**
- **Natural Language Processing** via Ollama Dolphin-Llama3 model
- **Voice Camera Commands** - "Show me the front door camera"
- **Smart Home Device Control** - "Turn on the living room lights"
- **Contextual Responses** based on current home status

### 📹 **Comprehensive Camera System**
- **5 Unifi Protect Cameras** with voice control
  - Front Door Doorbell Camera
  - Garage Camera
  - Front Driveway Camera
  - Backyard Patio Camera
  - Back Road Camera
- **Real-time Status Monitoring** with online/offline detection
- **Camera Proxy Integration** for seamless browser display
- **Automatic Snapshot Refresh** every 10 seconds

### 🎨 **Enhanced Web Interface**
- **Modern Glass Morphism Design** with FontAwesome icons
- **Real-time Analytics Dashboard** with command tracking
- **Voice Recognition** with keyboard shortcuts (Ctrl+Space)
- **Mobile-Responsive Design** with dark/light theme toggle
- **Performance Metrics** and system health monitoring

### 🤖 **AI Integration**
- **Ollama Integration** for local AI processing
- **Smart Command Interpretation** with context awareness
- **Multiple AI Models Support** (Dolphin-Llama3, etc.)
- **Privacy-First Design** - all AI processing stays local

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Home Assistant** instance running
- **Ollama** with Dolphin-Llama3 model
- **Unifi Protect** (optional, for camera features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ha-bridge-deploy
   ```

2. **Set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install flask flask-cors requests
   ```

3. **Configure environment variables**
   ```bash
   export HA_URL="http://your-home-assistant:8123"
   export HA_TOKEN="your_home_assistant_token"
   export OLLAMA_URL="http://your-ollama-server:11434"
   ```

4. **Start the services**
   ```bash
   # Terminal 1: Main AI Bridge
   python3 ha_bridge.py

   # Terminal 2: Camera Bridge
   python3 ha_bridge_camera.py

   # Terminal 3: Enhanced Web UI
   python3 web_ui_enhanced.py
   ```

5. **Access the interfaces**
   - **Enhanced Web UI**: http://localhost:8081
   - **Main Bridge API**: http://localhost:5001
   - **Camera Bridge API**: http://localhost:5002

## 📁 Project Structure

```
ha-bridge-deploy/
├── 🏠 Core Services
│   ├── ha_bridge.py              # Main AI bridge service
│   ├── ha_bridge_camera.py       # Camera control service
│   ├── web_ui.py                 # Basic web interface
│   └── web_ui_enhanced.py        # Enhanced web interface
│
├── 📹 Frigate Integration
│   ├── frigate-best-practices-2024.yml    # Latest Frigate config
│   ├── frigate-config-udm-optimized.yml   # UDM-SE optimized
│   ├── deploy_frigate.py                  # Automated deployment
│   └── deploy_frigate_now.sh              # Quick deploy script
│
├── 🐳 Container Deployment
│   ├── docker-compose.yml                 # Main compose file
│   ├── frigate-docker-compose.yml         # Frigate specific
│   └── mqtt-config/                       # MQTT broker config
│
├── 📚 Documentation
│   ├── README.md                          # This file
│   ├── frigate_deployment_guide.md        # Frigate setup guide
│   └── unifi_integration_guide.md         # Unifi integration
│
└── 🧪 Testing & Utilities
    ├── test_bridge_simple.py              # Basic API tests
    ├── complete_test.py                   # Comprehensive tests
    └── voice_camera_demo.py               # Demo script
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HA_URL` | Home Assistant URL | `http://192.168.0.81:8123` |
| `HA_TOKEN` | Home Assistant Long-Lived Token | Required |
| `OLLAMA_URL` | Ollama Server URL | `http://100.94.114.43:11434` |

### Camera Configuration

Edit `ha_bridge_camera.py` to match your camera entities:

```python
CAMERA_MAPPINGS = {
    'front door': 'camera.your_front_door_camera',
    'garage': 'camera.your_garage_camera',
    # Add your cameras here...
}
```

## 🎯 Usage Examples

### Voice Commands

**Camera Control:**
- "Show me the front door"
- "Display garage camera"
- "Check the driveway"
- "Look at the backyard"

**Smart Home Control:**
- "Turn on the living room lights"
- "Set temperature to 72 degrees"
- "Turn off all lights"
- "Good night - secure the house"

**Status Queries:**
- "What's the temperature in the house?"
- "Is everything secure?"
- "Show me all camera status"

### API Endpoints

**Main Bridge (Port 5001):**
```bash
# Health check
curl http://localhost:5001/health

# Voice command
curl -X POST http://localhost:5001/voice_command \
  -H "Content-Type: application/json" \
  -d '{"command": "turn on the lights"}'

# Smart query
curl -X POST http://localhost:5001/smart_query \
  -H "Content-Type: application/json" \
  -d '{"query": "what is the temperature?"}'
```

**Camera Bridge (Port 5002):**
```bash
# List cameras
curl http://localhost:5002/list_cameras

# Camera status
curl http://localhost:5002/camera_status

# Voice camera command
curl -X POST http://localhost:5002/voice_command \
  -H "Content-Type: application/json" \
  -d '{"command": "show me the front door"}'
```

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Proxmox LXC Deployment

1. **Create LXC Container**
   ```bash
   pct create 230 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
     --cores 4 --memory 4096 --swap 2048 \
     --net0 name=eth0,bridge=vmbr0,ip=192.168.0.230/24,gw=192.168.0.1 \
     --storage local-lvm --rootfs local-lvm:32
   ```

2. **Install Dependencies**
   ```bash
   pct exec 230 -- bash -c "
   apt update && apt install -y python3 python3-pip docker.io docker-compose git
   systemctl enable --now docker
   "
   ```

3. **Deploy Services**
   ```bash
   pct exec 230 -- bash -c "
   cd /opt && git clone <repository-url> ha-bridge
   cd ha-bridge && docker-compose up -d
   "
   ```

## 🎨 Web Interface Features

### Enhanced UI (Port 8081)

**Dashboard Sections:**
- **System Status** - Real-time health monitoring
- **Camera Grid** - Live camera feeds with status indicators
- **Voice Commands** - Interactive voice recognition
- **Device Controls** - Quick smart home device access
- **Analytics** - Performance metrics and command history

**Keyboard Shortcuts:**
- `Ctrl + Space` - Activate voice recognition
- `Ctrl + Enter` - Send typed command
- `Escape` - Cancel voice recording

**Theme Options:**
- Light/Dark mode toggle
- Glass morphism design
- FontAwesome icons
- Responsive mobile layout

## 🔨 Development

### Adding New Features

1. **New Voice Commands**
   - Edit prompt templates in `ha_bridge.py`
   - Add command patterns to AI training

2. **Camera Integration**
   - Update `CAMERA_MAPPINGS` in `ha_bridge_camera.py`
   - Add entity IDs from Home Assistant

3. **Web UI Enhancements**
   - Modify `web_ui_enhanced.py`
   - Add new API endpoints as needed

### Testing

```bash
# Run basic tests
python3 test_bridge_simple.py

# Run comprehensive tests
python3 complete_test.py

# Test camera functionality
python3 voice_camera_demo.py
```

## 📊 Performance & Monitoring

### System Requirements

**Minimum:**
- 2 CPU cores
- 2GB RAM
- 10GB storage

**Recommended:**
- 4+ CPU cores
- 4GB+ RAM
- 20GB+ storage
- SSD storage for better performance

### Monitoring

The enhanced web UI provides:
- **Real-time Metrics** - Response times, command success rates
- **System Health** - Service status, connectivity checks
- **Usage Analytics** - Command history, performance trends
- **Error Tracking** - Failed commands, system issues

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Home Assistant** community for the excellent platform
- **Ollama** team for local AI processing
- **Frigate** project for advanced camera AI
- **Unifi** for robust networking and camera hardware
- **Claude Code** for development assistance

## 📞 Support

For support and questions:

- 📧 **Issues**: Open a GitHub issue
- 📚 **Documentation**: Check the `/docs` folder
- 💬 **Discussions**: Use GitHub Discussions

---

**🤖 Generated with [Claude Code](https://claude.ai/code)**

*Last updated: September 2025*