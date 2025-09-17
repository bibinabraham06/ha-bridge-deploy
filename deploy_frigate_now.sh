#!/bin/bash
# Frigate Deployment Script for Your Unifi Cameras
# Ready to deploy with your specific RTSP URLs

echo "🤖 DEPLOYING FRIGATE AI FOR YOUR UNIFI CAMERAS"
echo "=============================================="
echo ""
echo "📹 Your Camera Configuration:"
echo "   • Front Doorbell: TD0n4xjjZyz7098h"
echo "   • Garage: w43nFnaYRCXWS4r7"
echo "   • Front Driveway: tSTGrRA5hL0JDWdq"
echo "   • Back Patio: SLNQWyDL3NmCC29h"
echo "   • Back Left Patio: RK7XFgef0NfKdgUj"
echo ""

# Create deployment directory
echo "📁 Creating Frigate deployment directory..."
mkdir -p /opt/frigate
cd /opt/frigate

# Create required directories
echo "📂 Setting up directory structure..."
mkdir -p config storage mqtt-config mqtt-data mqtt-logs
chmod 777 storage mqtt-data mqtt-logs

# Copy configuration files
echo "📋 Installing configuration files..."
cp ~/ha-bridge-deploy/frigate-docker-compose.yml ./docker-compose.yml
cp ~/ha-bridge-deploy/frigate-config-configured.yml ./config/config.yml

# Create MQTT configuration (if needed)
cat > mqtt-config/mosquitto.conf << EOF
# Mosquitto configuration for Frigate
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information

listener 1883
allow_anonymous true

listener 9001
protocol websockets
allow_anonymous true
EOF

echo ""
echo "🔧 DEPLOYMENT COMMANDS:"
echo "======================"
echo ""
echo "1. Navigate to deployment directory:"
echo "   cd /opt/frigate"
echo ""
echo "2. Start Frigate services:"
echo "   docker-compose up -d"
echo ""
echo "3. Check deployment status:"
echo "   docker-compose logs -f frigate"
echo ""
echo "4. Access Frigate Web UI:"
echo "   http://YOUR_PROXMOX_IP:5000"
echo ""
echo "5. Monitor container health:"
echo "   docker-compose ps"
echo ""

echo "🎯 POST-DEPLOYMENT SETUP:"
echo "========================="
echo ""
echo "1. 🌐 Open Frigate UI (http://IP:5000)"
echo "2. ⚙️  Go to Settings → Cameras"
echo "3. 🎨 Draw detection zones for each camera:"
echo "   • Front Doorbell: entrance, walkway zones"
echo "   • Garage: garage door, interior zones"
echo "   • Driveway: main driveway, street view zones"
echo "   • Back Patios: patio areas, yard zones"
echo ""
echo "4. 🧪 Test detection by walking around"
echo "5. 📱 Check Home Assistant for new camera entities"
echo ""

echo "🎙️  NEW VOICE COMMANDS READY:"
echo "============================"
echo "   • 'Any people at the front door?'"
echo "   • 'Was a package delivered?'"
echo "   • 'Any cars in the driveway?'"
echo "   • 'Show me recent motion events'"
echo ""

echo "📊 EXPECTED RESOURCE USAGE:"
echo "========================="
echo "   • CPU: 2-4 cores active processing"
echo "   • RAM: 4-6 GB for 5 camera streams"
echo "   • Storage: ~50GB per week with smart recording"
echo "   • Network: ~10-15 Mbps for all streams"
echo ""

echo "✅ DEPLOYMENT PACKAGE READY!"
echo ""
echo "🚀 NEXT STEPS:"
echo "   1. Copy files to your Proxmox container"
echo "   2. Run: docker-compose up -d"
echo "   3. Configure detection zones in Frigate UI"
echo "   4. Test AI detection"
echo "   5. Enjoy intelligent camera monitoring!"
echo ""
echo "💡 Your Unifi cameras will now have AI superpowers!"