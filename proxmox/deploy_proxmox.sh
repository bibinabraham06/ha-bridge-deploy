#!/bin/bash
"""
Proxmox LXC Deployment Script for Home Assistant AI Bridge
Complete automation for LXC container setup and service deployment
"""

# Configuration
CTID="${1:-230}"
HOSTNAME="ha-ai-bridge"
TEMPLATE="local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst"
CORES=4
MEMORY=4096
SWAP=2048
DISK_SIZE=32
NETWORK="name=eth0,bridge=vmbr0,ip=192.168.0.${CTID}/24,gw=192.168.0.1"
STORAGE="local-lvm"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_proxmox() {
    print_status "Checking Proxmox environment..."

    if ! command -v pct &> /dev/null; then
        print_error "This script must be run on a Proxmox host"
        exit 1
    fi

    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root"
        exit 1
    fi

    print_success "Proxmox environment verified"
}

stop_existing_container() {
    print_status "Checking for existing container $CTID..."

    if pct status $CTID &>/dev/null; then
        print_warning "Container $CTID already exists. Stopping and removing..."
        pct stop $CTID 2>/dev/null || true
        sleep 5
        pct destroy $CTID
        print_success "Existing container removed"
    fi
}

create_container() {
    print_status "Creating LXC container $CTID..."

    pct create $CTID $TEMPLATE \
        --hostname $HOSTNAME \
        --cores $CORES \
        --memory $MEMORY \
        --swap $SWAP \
        --net0 $NETWORK \
        --storage $STORAGE \
        --rootfs $STORAGE:$DISK_SIZE \
        --features nesting=1 \
        --unprivileged 1 \
        --onboot 1

    if [ $? -eq 0 ]; then
        print_success "Container $CTID created successfully"
    else
        print_error "Failed to create container"
        exit 1
    fi
}

start_container() {
    print_status "Starting container $CTID..."

    pct start $CTID

    # Wait for container to be ready
    sleep 10

    if pct status $CTID | grep -q "running"; then
        print_success "Container $CTID started successfully"
    else
        print_error "Failed to start container"
        exit 1
    fi
}

install_dependencies() {
    print_status "Installing system dependencies..."

    pct exec $CTID -- bash -c "
        apt update && apt upgrade -y
        apt install -y \\
            python3 \\
            python3-pip \\
            python3-venv \\
            git \\
            curl \\
            wget \\
            nano \\
            htop \\
            net-tools \\
            software-properties-common \\
            ca-certificates \\
            gnupg \\
            lsb-release
    "

    if [ $? -eq 0 ]; then
        print_success "System dependencies installed"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

setup_docker() {
    print_status "Setting up Docker..."

    pct exec $CTID -- bash -c "
        # Add Docker's official GPG key
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

        # Add Docker repository
        echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable\" | tee /etc/apt/sources.list.d/docker.list > /dev/null

        # Install Docker
        apt update
        apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

        # Enable and start Docker
        systemctl enable docker
        systemctl start docker

        # Add user to docker group
        usermod -aG docker root
    "

    if [ $? -eq 0 ]; then
        print_success "Docker installed and configured"
    else
        print_error "Failed to install Docker"
        exit 1
    fi
}

clone_repository() {
    print_status "Cloning HA AI Bridge repository..."

    pct exec $CTID -- bash -c "
        cd /opt
        git clone https://github.com/bibinabraham06/ha-bridge-deploy.git
        chown -R root:root /opt/ha-bridge-deploy
        chmod +x /opt/ha-bridge-deploy/proxmox/*.sh
    "

    if [ $? -eq 0 ]; then
        print_success "Repository cloned to /opt/ha-bridge-deploy"
    else
        print_error "Failed to clone repository"
        exit 1
    fi
}

setup_python_environment() {
    print_status "Setting up Python virtual environment..."

    pct exec $CTID -- bash -c "
        cd /opt/ha-bridge-deploy
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install flask flask-cors requests
    "

    if [ $? -eq 0 ]; then
        print_success "Python environment configured"
    else
        print_error "Failed to setup Python environment"
        exit 1
    fi
}

create_systemd_services() {
    print_status "Creating systemd services..."

    # Main AI Bridge service
    pct exec $CTID -- bash -c "cat > /etc/systemd/system/ha-bridge.service << 'EOF'
[Unit]
Description=Home Assistant AI Bridge
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ha-bridge-deploy
Environment=HA_URL=http://192.168.0.81:8123
Environment=HA_TOKEN=your_token_here
Environment=OLLAMA_URL=http://100.94.114.43:11434
ExecStart=/opt/ha-bridge-deploy/venv/bin/python /opt/ha-bridge-deploy/ha_bridge.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

    # Camera Bridge service
    pct exec $CTID -- bash -c "cat > /etc/systemd/system/ha-bridge-camera.service << 'EOF'
[Unit]
Description=Home Assistant Camera Bridge
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ha-bridge-deploy
Environment=HA_URL=http://192.168.0.81:8123
Environment=HA_TOKEN=your_token_here
Environment=OLLAMA_URL=http://100.94.114.43:11434
ExecStart=/opt/ha-bridge-deploy/venv/bin/python /opt/ha-bridge-deploy/ha_bridge_camera.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

    # Enhanced Web UI service
    pct exec $CTID -- bash -c "cat > /etc/systemd/system/ha-web-ui.service << 'EOF'
[Unit]
Description=Home Assistant Enhanced Web UI
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ha-bridge-deploy
Environment=HA_URL=http://192.168.0.81:8123
Environment=HA_TOKEN=your_token_here
Environment=OLLAMA_URL=http://100.94.114.43:11434
ExecStart=/opt/ha-bridge-deploy/venv/bin/python /opt/ha-bridge-deploy/web_ui_enhanced.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

    # Reload systemd
    pct exec $CTID -- systemctl daemon-reload

    print_success "Systemd services created"
}

configure_firewall() {
    print_status "Configuring firewall rules..."

    pct exec $CTID -- bash -c "
        # Install ufw if not present
        apt install -y ufw

        # Configure firewall
        ufw --force reset
        ufw default deny incoming
        ufw default allow outgoing

        # Allow SSH
        ufw allow ssh

        # Allow our services
        ufw allow 5001/tcp comment 'HA AI Bridge'
        ufw allow 5002/tcp comment 'HA Camera Bridge'
        ufw allow 8081/tcp comment 'Enhanced Web UI'

        # Enable firewall
        ufw --force enable
    "

    print_success "Firewall configured"
}

create_startup_script() {
    print_status "Creating startup and management scripts..."

    pct exec $CTID -- bash -c "cat > /opt/ha-bridge-deploy/start_services.sh << 'EOF'
#!/bin/bash
# Start all HA AI Bridge services

echo \"Starting Home Assistant AI Bridge services...\"

# Start services
systemctl start ha-bridge
systemctl start ha-bridge-camera
systemctl start ha-web-ui

# Enable services for auto-start
systemctl enable ha-bridge
systemctl enable ha-bridge-camera
systemctl enable ha-web-ui

echo \"Services started and enabled for auto-start\"
echo \"\"
echo \"Access points:\"
echo \"  - Main AI Bridge:    http://192.168.0.${CTID}:5001\"
echo \"  - Camera Bridge:     http://192.168.0.${CTID}:5002\"
echo \"  - Enhanced Web UI:   http://192.168.0.${CTID}:8081\"
EOF"

    pct exec $CTID -- bash -c "cat > /opt/ha-bridge-deploy/stop_services.sh << 'EOF'
#!/bin/bash
# Stop all HA AI Bridge services

echo \"Stopping Home Assistant AI Bridge services...\"

systemctl stop ha-bridge
systemctl stop ha-bridge-camera
systemctl stop ha-web-ui

echo \"All services stopped\"
EOF"

    pct exec $CTID -- bash -c "cat > /opt/ha-bridge-deploy/status_services.sh << 'EOF'
#!/bin/bash
# Check status of all HA AI Bridge services

echo \"HA AI Bridge Service Status:\"
echo \"=============================\"

echo \"\"
echo \"Main AI Bridge:\"
systemctl status ha-bridge --no-pager -l

echo \"\"
echo \"Camera Bridge:\"
systemctl status ha-bridge-camera --no-pager -l

echo \"\"
echo \"Enhanced Web UI:\"
systemctl status ha-web-ui --no-pager -l

echo \"\"
echo \"Access points:\"
echo \"  - Main AI Bridge:    http://192.168.0.${CTID}:5001\"
echo \"  - Camera Bridge:     http://192.168.0.${CTID}:5002\"
echo \"  - Enhanced Web UI:   http://192.168.0.${CTID}:8081\"
EOF"

    # Make scripts executable
    pct exec $CTID -- chmod +x /opt/ha-bridge-deploy/*.sh

    print_success "Management scripts created"
}

display_summary() {
    print_success "Proxmox LXC Container Deployment Complete!"
    echo ""
    echo "================================="
    echo "Container Details:"
    echo "  ID: $CTID"
    echo "  Hostname: $HOSTNAME"
    echo "  IP: 192.168.0.$CTID"
    echo "  Resources: ${CORES} cores, ${MEMORY}MB RAM"
    echo ""
    echo "Services Available:"
    echo "  - Main AI Bridge:    http://192.168.0.${CTID}:5001"
    echo "  - Camera Bridge:     http://192.168.0.${CTID}:5002"
    echo "  - Enhanced Web UI:   http://192.168.0.${CTID}:8081"
    echo ""
    echo "Management Commands:"
    echo "  - Start services:    pct exec $CTID /opt/ha-bridge-deploy/start_services.sh"
    echo "  - Stop services:     pct exec $CTID /opt/ha-bridge-deploy/stop_services.sh"
    echo "  - Check status:      pct exec $CTID /opt/ha-bridge-deploy/status_services.sh"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure your HA_TOKEN in the service files"
    echo "  2. Start the services: pct exec $CTID /opt/ha-bridge-deploy/start_services.sh"
    echo "  3. Access the Enhanced Web UI at http://192.168.0.${CTID}:8081"
    echo "================================="
}

main() {
    echo "🏠 Home Assistant AI Bridge - Proxmox LXC Deployment"
    echo "=================================================="

    check_proxmox
    stop_existing_container
    create_container
    start_container
    install_dependencies
    setup_docker
    clone_repository
    setup_python_environment
    create_systemd_services
    configure_firewall
    create_startup_script
    display_summary
}

# Run main function
main "$@"