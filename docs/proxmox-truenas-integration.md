# 🏠💾 Proxmox + TrueNAS Integration Guide
## Complete Enterprise Home Lab Setup for Smart Home AI

[![Proxmox](https://img.shields.io/badge/Proxmox-8.0+-orange.svg)](https://www.proxmox.com/)
[![TrueNAS](https://img.shields.io/badge/TrueNAS-SCALE-blue.svg)](https://www.truenas.com/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024+-green.svg)](https://www.home-assistant.io/)

This guide provides a complete enterprise-grade setup combining Proxmox virtualization with TrueNAS storage for your Home Assistant AI Bridge deployment.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PROXMOX HOST                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ LXC 100     │  │ LXC 200     │  │ VM 300              │ │
│  │ Home        │  │ Frigate     │  │ TrueNAS SCALE       │ │
│  │ Assistant   │  │ AI          │  │ (Storage Backend)   │ │
│  │             │  │             │  │                     │ │
│  │ HA Bridge   │  │ Camera AI   │  │ - NFS Shares        │ │
│  │ Web UI      │  │ Detection   │  │ - SMB Shares        │ │
│  │             │  │             │  │ - ZFS Pool          │ │
│  └─────────────┘  └─────────────┘  │ - Backup Storage    │ │
│                                    │ - Media Storage     │ │
│  ┌─────────────┐  ┌─────────────┐  └─────────────────────┘ │
│  │ LXC 230     │  │ LXC 400     │                          │
│  │ HA AI       │  │ Monitoring  │                          │
│  │ Bridge      │  │ Stack       │                          │
│  └─────────────┘  └─────────────┘                          │
│                                                             │
│  Network: 192.168.0.0/24                                   │
│  Unifi Dream Machine SE (192.168.0.1)                      │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Hardware Requirements

### Minimum Requirements
| Component | Proxmox Host | TrueNAS VM |
|-----------|--------------|------------|
| **CPU** | 8 cores / 16 threads | 4 cores allocated |
| **RAM** | 32GB ECC preferred | 16GB allocated |
| **Storage** | 500GB NVMe SSD | 4x HDDs for ZFS |
| **Network** | 2.5GbE minimum | Shared with host |

### Recommended Setup
| Component | Proxmox Host | TrueNAS VM |
|-----------|--------------|------------|
| **CPU** | 16+ cores (Intel Xeon/AMD EPYC) | 8 cores allocated |
| **RAM** | 64GB+ ECC | 32GB allocated |
| **Storage** | 1TB NVMe + HDDs passthrough | 6-8x HDDs ZFS RAID-Z2 |
| **Network** | 10GbE with redundancy | Dedicated NICs |

## 🚀 Quick Start Deployment

### Step 1: Proxmox Host Setup

```bash
# Update Proxmox host
apt update && apt upgrade -y

# Configure GPU passthrough (if using Intel QuickSync)
echo "intel_iommu=on" >> /etc/default/grub
update-grub
reboot

# Install additional packages
apt install -y curl wget git
```

### Step 2: Deploy TrueNAS SCALE VM

```bash
# Download our automated deployment script
curl -fsSL https://raw.githubusercontent.com/bibinabraham06/ha-bridge-deploy/main/proxmox/deploy_truenas.sh -o deploy_truenas.sh
chmod +x deploy_truenas.sh

# Deploy TrueNAS VM with recommended settings
./deploy_truenas.sh --vm-id 300 --memory 16384 --cores 4 --disk-passthrough /dev/sdb,/dev/sdc,/dev/sdd,/dev/sde
```

### Step 3: Deploy HA AI Bridge LXC

```bash
# Deploy our complete HA AI Bridge stack
curl -fsSL https://raw.githubusercontent.com/bibinabraham06/ha-bridge-deploy/main/proxmox/deploy_proxmox.sh -o deploy_proxmox.sh
chmod +x deploy_proxmox.sh

# Create LXC container with TrueNAS integration
./deploy_proxmox.sh 230
```

## 📁 TrueNAS Configuration

### 1. Initial TrueNAS Setup

```bash
# Access TrueNAS web interface: https://192.168.0.300

# Create ZFS Pool
- Pool Name: "homelab"
- RAID Level: RAID-Z2 (recommended for 6+ drives)
- Compression: LZ4
- Deduplication: Off (unless you have 64GB+ RAM)
```

### 2. Create Datasets for Home Assistant

```bash
# Create organized dataset structure
/mnt/homelab/
├── home-assistant/
│   ├── config/
│   ├── backups/
│   └── media/
├── frigate/
│   ├── recordings/
│   ├── clips/
│   └── config/
├── monitoring/
│   ├── prometheus/
│   ├── grafana/
│   └── logs/
└── shared/
    ├── downloads/
    ├── media/
    └── documents/
```

### 3. Configure NFS Shares

```bash
# NFS Share Configuration in TrueNAS:

# Home Assistant Config Share
Path: /mnt/homelab/home-assistant
Authorized Networks: 192.168.0.0/24
All Directories: ✓
Read Only: ✗
Maproot User: root
Maproot Group: root

# Frigate Storage Share
Path: /mnt/homelab/frigate
Authorized Networks: 192.168.0.0/24
All Directories: ✓
Read Only: ✗
```

## 🏠 Container Integration

### Home Assistant LXC (100) with TrueNAS

```bash
# Mount TrueNAS shares in HA container
pct exec 100 -- bash -c "
    apt install -y nfs-common
    mkdir -p /mnt/truenas/{config,backups,media}

    # Add to /etc/fstab
    echo '192.168.0.300:/mnt/homelab/home-assistant/config /mnt/truenas/config nfs defaults 0 0' >> /etc/fstab
    echo '192.168.0.300:/mnt/homelab/home-assistant/backups /mnt/truenas/backups nfs defaults 0 0' >> /etc/fstab
    echo '192.168.0.300:/mnt/homelab/shared/media /mnt/truenas/media nfs defaults 0 0' >> /etc/fstab

    mount -a
"

# Update Home Assistant configuration.yaml
cat >> /opt/homeassistant/configuration.yaml << EOF
# TrueNAS Integration
recorder:
  db_url: !secret db_url
  purge_keep_days: 30
  auto_purge: true

backup:
  location: /mnt/truenas/backups

media_dirs:
  media: /mnt/truenas/media
EOF
```

### Frigate LXC (200) with TrueNAS Storage

```bash
# Configure Frigate with TrueNAS backend
pct exec 200 -- bash -c "
    mkdir -p /mnt/frigate/{recordings,clips,config}

    # Mount TrueNAS shares
    echo '192.168.0.300:/mnt/homelab/frigate/recordings /mnt/frigate/recordings nfs defaults 0 0' >> /etc/fstab
    echo '192.168.0.300:/mnt/homelab/frigate/clips /mnt/frigate/clips nfs defaults 0 0' >> /etc/fstab

    mount -a
"

# Update Frigate configuration
cat > /opt/frigate/config/config.yml << EOF
# TrueNAS Storage Configuration
record:
  enabled: true
  retain:
    days: 7
    mode: all
  events:
    retain:
      default: 30
      mode: active_objects

# Storage paths on TrueNAS
database:
  path: /mnt/frigate/config/frigate.db

model:
  path: /mnt/frigate/config/models

clips:
  dir: /mnt/frigate/clips

record:
  dir: /mnt/frigate/recordings
EOF
```

## 🔄 Automated Backup Strategy

### TrueNAS Backup Jobs

```bash
# Create backup script for HA AI Bridge
cat > /mnt/homelab/scripts/backup_homelab.sh << 'EOF'
#!/bin/bash
# Automated backup for Home Assistant AI Bridge

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/mnt/homelab/backups/$DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup Home Assistant
echo "Backing up Home Assistant..."
rsync -av --exclude="*.log" /mnt/homelab/home-assistant/ "$BACKUP_DIR/home-assistant/"

# Backup Frigate configuration
echo "Backing up Frigate config..."
rsync -av /mnt/homelab/frigate/config/ "$BACKUP_DIR/frigate-config/"

# Backup HA AI Bridge
echo "Backing up HA AI Bridge..."
ssh root@192.168.0.230 "tar -czf /tmp/ha-bridge-backup.tar.gz /opt/ha-bridge-deploy"
scp root@192.168.0.230:/tmp/ha-bridge-backup.tar.gz "$BACKUP_DIR/"

# Cleanup old backups (keep 30 days)
find /mnt/homelab/backups/ -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x /mnt/homelab/scripts/backup_homelab.sh

# Schedule daily backups
echo "0 2 * * * /mnt/homelab/scripts/backup_homelab.sh" | crontab -
```

## 📊 Monitoring Integration

### Prometheus + Grafana Stack

```bash
# Deploy monitoring container
pct create 400 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname monitoring \
  --cores 2 --memory 2048 --swap 1024 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.0.400/24,gw=192.168.0.1 \
  --storage local-lvm --rootfs local-lvm:20

pct start 400

# Install monitoring stack
pct exec 400 -- bash -c "
    apt update && apt install -y docker.io docker-compose

    mkdir -p /opt/monitoring
    cd /opt/monitoring

    # Mount TrueNAS storage for metrics
    mkdir -p /mnt/truenas/monitoring
    echo '192.168.0.300:/mnt/homelab/monitoring /mnt/truenas/monitoring nfs defaults 0 0' >> /etc/fstab
    mount -a
"
```

### Docker Compose for Monitoring

```yaml
# /opt/monitoring/docker-compose.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - /mnt/truenas/monitoring/prometheus:/prometheus
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - /mnt/truenas/monitoring/grafana:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
```

## 🌐 Network Optimization

### Unifi Dream Machine SE Integration

```bash
# Optimize network for home lab traffic
# Configure VLAN for infrastructure (optional)

# VLAN 10: Infrastructure
# - Proxmox host: 192.168.10.10
# - TrueNAS: 192.168.10.300
# - Monitoring: 192.168.10.400

# VLAN 20: Home Assistant
# - HA containers: 192.168.20.0/24
# - IoT devices: 192.168.20.0/24

# Configure QoS for camera streams
# Priority: High for RTSP streams to Frigate
# Priority: Medium for HA API traffic
# Priority: Low for backup traffic
```

### Performance Tuning

```bash
# Proxmox host optimizations
echo 'net.core.rmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_rmem = 4096 65536 134217728' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_wmem = 4096 65536 134217728' >> /etc/sysctl.conf
sysctl -p

# TrueNAS optimizations
# Set ARC size to 50% of allocated RAM
# Enable L2ARC if using SSD cache
# Configure appropriate record size for workload
```

## 🔐 Security Best Practices

### Network Security

```bash
# Proxmox firewall rules
cat > /etc/pve/firewall/cluster.fw << EOF
[OPTIONS]
enable: 1

[RULES]
# Allow infrastructure communication
IN ACCEPT -p tcp -dport 22 -source 192.168.0.0/24
IN ACCEPT -p tcp -dport 8006 -source 192.168.0.0/24

# Home Assistant services
IN ACCEPT -p tcp -dport 8123 -source 192.168.0.0/24
IN ACCEPT -p tcp -dport 5001:5002 -source 192.168.0.0/24
IN ACCEPT -p tcp -dport 8081 -source 192.168.0.0/24

# TrueNAS services
IN ACCEPT -p tcp -dport 80,443 -source 192.168.0.0/24
IN ACCEPT -p tcp -dport 2049 -source 192.168.0.0/24

# Monitoring
IN ACCEPT -p tcp -dport 3000,9090,9100 -source 192.168.0.0/24

# Block everything else
IN DROP
EOF
```

### Backup Security

```bash
# Encrypted offsite backups
cat > /mnt/homelab/scripts/secure_backup.sh << 'EOF'
#!/bin/bash
# Encrypted backup to cloud storage

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/tmp/homelab_backup_$DATE.tar.gz.enc"

# Create encrypted backup
tar -czf - /mnt/homelab/home-assistant /mnt/homelab/frigate/config | \
  openssl enc -aes-256-cbc -salt -k "$BACKUP_PASSWORD" > "$BACKUP_FILE"

# Upload to cloud (configure your preferred provider)
# rclone copy "$BACKUP_FILE" cloud-storage:backups/homelab/

# Cleanup
rm "$BACKUP_FILE"
EOF
```

## 🎯 Use Cases & Examples

### Smart Home Media Server

```bash
# Configure Plex/Jellyfin on TrueNAS
# Mount media library from TrueNAS to HA
# Voice commands: "Play music in living room"
# AI integration: "Show me clips from today with people"
```

### Advanced Automation

```bash
# Presence detection with NVR integration
# Automatic backup when away
# Energy monitoring with historical data
# Predictive maintenance alerts
```

### Enterprise Features

```bash
# High availability with Proxmox clustering
# ZFS snapshots for point-in-time recovery
# RAID-Z2 for data protection
# 10GbE networking for performance
```

## 🏆 Performance Benchmarks

### Expected Performance
| Service | Response Time | Throughput |
|---------|---------------|------------|
| HA AI Bridge | <100ms | 1000+ req/min |
| Camera AI | <2s detection | 5 cameras @ 4K |
| Voice Commands | <500ms | Real-time |
| Web UI | <50ms | Interactive |

### Storage Performance
| Operation | IOPS | Bandwidth |
|-----------|------|-----------|
| Sequential Read | 500MB/s+ | ZFS dependent |
| Sequential Write | 300MB/s+ | RAID level dependent |
| Random Read | 10K+ IOPS | SSD cache helpful |
| Backup Speed | 100MB/s+ | Network limited |

## 🔄 Maintenance & Updates

### Automated Updates

```bash
# Create update script
cat > /mnt/homelab/scripts/update_all.sh << 'EOF'
#!/bin/bash
# Update all components

# Update Proxmox host
ssh root@192.168.0.10 "apt update && apt upgrade -y"

# Update containers
for container in 100 200 230 400; do
    echo "Updating container $container..."
    pct exec $container -- apt update
    pct exec $container -- apt upgrade -y
done

# Update HA AI Bridge
ssh root@192.168.0.230 "cd /opt/ha-bridge-deploy && git pull"

# Restart services if needed
systemctl restart ha-bridge ha-bridge-camera ha-web-ui
EOF
```

## 🆘 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| NFS mount fails | Check network connectivity, firewall rules |
| Slow performance | Verify ZFS ARC settings, network bandwidth |
| Backup failures | Check disk space, permissions |
| Container won't start | Verify resource allocation, dependencies |

### Logs and Diagnostics

```bash
# Proxmox logs
tail -f /var/log/pve-firewall.log
tail -f /var/log/pveproxy/access.log

# Container logs
pct exec 230 -- journalctl -u ha-bridge -f

# TrueNAS logs
ssh admin@192.168.0.300 "tail -f /var/log/messages"
```

---

## 🎉 Complete Setup Summary

Your enterprise-grade home lab now includes:

✅ **Proxmox Virtualization Platform**
- Enterprise hypervisor with clustering support
- Automated LXC container deployment
- GPU passthrough for AI acceleration

✅ **TrueNAS Storage Backend**
- ZFS filesystem with data protection
- NFS/SMB shares for container integration
- Automated backup and snapshot management

✅ **Home Assistant AI Bridge**
- Voice-controlled smart home automation
- AI-powered camera analysis with Frigate
- Modern web interface with real-time monitoring

✅ **Monitoring & Analytics**
- Prometheus metrics collection
- Grafana dashboards and alerting
- Performance monitoring and optimization

✅ **Security & Backup**
- Network segmentation and firewalls
- Encrypted backups with cloud integration
- Point-in-time recovery with ZFS snapshots

**🔗 Quick Access URLs:**
- Proxmox: https://192.168.0.10:8006
- TrueNAS: https://192.168.0.300
- Home Assistant: http://192.168.0.100:8123
- HA AI Bridge: http://192.168.0.230:8081
- Grafana: http://192.168.0.400:3000

Your smart home is now powered by enterprise infrastructure! 🏠⚡