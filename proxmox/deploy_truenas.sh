#!/bin/bash
"""
TrueNAS SCALE Deployment Script for Proxmox
Automated deployment of TrueNAS SCALE VM with optimal settings for home lab
"""

# Default configuration
VMID="${1:-300}"
VM_NAME="truenas-scale"
CORES="${2:-4}"
MEMORY="${3:-16384}"  # 16GB
DISK_SIZE="${4:-32}"  # GB for OS disk
NETWORK="vmbrо0"
ISO_PATH="local:iso/TrueNAS-SCALE-24.04.0.iso"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

check_requirements() {
    print_status "Checking Proxmox environment..."

    if ! command -v qm &> /dev/null; then
        print_error "This script must be run on a Proxmox host"
        exit 1
    fi

    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root"
        exit 1
    fi

    # Check if ISO exists
    if ! pvesm list local | grep -q "TrueNAS-SCALE"; then
        print_warning "TrueNAS SCALE ISO not found. Please upload it to Proxmox first."
        print_status "Download from: https://www.truenas.com/download-truenas-scale/"
        print_status "Upload to: Datacenter > local > ISO Images"
        exit 1
    fi

    print_success "Proxmox environment verified"
}

detect_storage_devices() {
    print_status "Detecting available storage devices..."

    # Find available drives (excluding boot drive)
    AVAILABLE_DRIVES=$(lsblk -dpno NAME,SIZE,TYPE | grep disk | grep -v "$(lsblk -no PKNAME $(df / | tail -1 | awk '{print $1}') | head -1)" | awk '{print $1}')

    if [ -z "$AVAILABLE_DRIVES" ]; then
        print_warning "No additional storage drives detected"
        print_status "TrueNAS will be deployed with VM storage only"
        USE_PASSTHROUGH=false
    else
        print_success "Available drives for passthrough:"
        echo "$AVAILABLE_DRIVES" | while read drive; do
            SIZE=$(lsblk -dno SIZE "$drive")
            MODEL=$(lsblk -dno MODEL "$drive" 2>/dev/null || echo "Unknown")
            echo "  - $drive ($SIZE) - $MODEL"
        done
        USE_PASSTHROUGH=true
    fi
}

stop_existing_vm() {
    print_status "Checking for existing VM $VMID..."

    if qm status $VMID &>/dev/null; then
        print_warning "VM $VMID already exists. Stopping and removing..."
        qm stop $VMID 2>/dev/null || true
        sleep 5
        qm destroy $VMID
        print_success "Existing VM removed"
    fi
}

create_vm() {
    print_status "Creating TrueNAS SCALE VM ($VMID)..."

    # Create VM with optimal settings for TrueNAS
    qm create $VMID \
        --name $VM_NAME \
        --cores $CORES \
        --memory $MEMORY \
        --sockets 1 \
        --numa 1 \
        --cpu cputype=host \
        --machine q35 \
        --bios ovmf \
        --efidisk0 local-lvm:1,format=raw,efitype=4m,pre-enrolled-keys=1 \
        --net0 virtio,bridge=$NETWORK \
        --ostype l26 \
        --tablet 0 \
        --boot order=ide2 \
        --onboot 1

    if [ $? -eq 0 ]; then
        print_success "VM $VMID created successfully"
    else
        print_error "Failed to create VM"
        exit 1
    fi
}

add_storage() {
    print_status "Configuring VM storage..."

    # Add OS disk
    qm set $VMID --scsi0 local-lvm:${DISK_SIZE},format=raw,iothread=1

    # Add CD-ROM with TrueNAS ISO
    qm set $VMID --ide2 $ISO_PATH,media=cdrom

    # Add additional SCSI controller for better performance
    qm set $VMID --scsihw virtio-scsi-pci

    print_success "Storage configuration completed"
}

configure_passthrough() {
    if [ "$USE_PASSTHROUGH" = true ]; then
        print_status "Configuring drive passthrough..."

        DRIVE_COUNT=0
        echo "$AVAILABLE_DRIVES" | while read drive; do
            if [ $DRIVE_COUNT -lt 6 ]; then  # Limit to 6 drives
                DEVICE_ID="/dev/disk/by-id/$(ls -l /dev/disk/by-id/ | grep "$(basename $drive)$" | head -1 | awk '{print $9}')"
                if [ -n "$DEVICE_ID" ] && [ -e "$DEVICE_ID" ]; then
                    SCSI_ID=$((1 + DRIVE_COUNT))
                    qm set $VMID --scsi${SCSI_ID} $DEVICE_ID
                    print_success "Added drive: $drive as scsi${SCSI_ID}"
                    DRIVE_COUNT=$((DRIVE_COUNT + 1))
                fi
            fi
        done

        if [ $DRIVE_COUNT -gt 0 ]; then
            print_success "Configured $DRIVE_COUNT drives for passthrough"
        else
            print_warning "No drives configured for passthrough"
        fi
    else
        print_status "Skipping drive passthrough - no suitable drives found"
    fi
}

optimize_vm_settings() {
    print_status "Applying TrueNAS optimizations..."

    # Optimize for storage workload
    qm set $VMID --args '-cpu host,+aes'

    # Set balloon memory to 0 (TrueNAS manages its own memory)
    qm set $VMID --balloon 0

    # Enable NUMA
    qm set $VMID --numa 1

    # Optimize network
    qm set $VMID --net0 virtio,bridge=$NETWORK,mtu=9000

    print_success "VM optimizations applied"
}

create_backup_storage() {
    print_status "Creating backup storage directory..."

    mkdir -p /opt/truenas-backup
    cat > /opt/truenas-backup/backup_truenas.sh << 'EOF'
#!/bin/bash
# TrueNAS Configuration Backup Script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/truenas-backup/configs"
VM_ID=300

mkdir -p "$BACKUP_DIR"

# Backup VM configuration
qm config $VM_ID > "$BACKUP_DIR/vm_config_$DATE.conf"

# Create VM snapshot
qm snapshot $VM_ID "backup_$DATE"

echo "TrueNAS backup completed: $DATE"
EOF

    chmod +x /opt/truenas-backup/backup_truenas.sh

    # Schedule weekly backups
    echo "0 3 * * 0 /opt/truenas-backup/backup_truenas.sh" | crontab -

    print_success "Backup system configured"
}

display_post_install() {
    print_success "TrueNAS SCALE VM deployment completed!"
    echo ""
    echo "============================================="
    echo "VM Details:"
    echo "  VM ID: $VMID"
    echo "  Name: $VM_NAME"
    echo "  CPU: $CORES cores"
    echo "  Memory: ${MEMORY}MB"
    echo "  Network: Bridge $NETWORK"
    echo ""
    echo "Next Steps:"
    echo "1. Start the VM: qm start $VMID"
    echo "2. Connect via console: qm monitor $VMID"
    echo "3. Complete TrueNAS SCALE installation"
    echo "4. Access web interface after reboot"
    echo ""
    echo "Post-Installation Setup:"
    echo "1. Create ZFS pool with available drives"
    echo "2. Configure network settings"
    echo "3. Set up NFS/SMB shares for Home Assistant"
    echo "4. Configure backup schedules"
    echo ""
    echo "Recommended ZFS Pool Configuration:"
    echo "  - Pool Name: homelab"
    echo "  - RAID Level: RAID-Z2 (6+ drives) or RAID-Z1 (4-5 drives)"
    echo "  - Compression: LZ4"
    echo "  - Deduplication: OFF (unless 64GB+ RAM)"
    echo ""
    echo "Home Assistant Integration:"
    echo "  - Create datasets: /mnt/homelab/home-assistant"
    echo "  - Configure NFS shares for LXC containers"
    echo "  - Set up automated backups"
    echo ""
    echo "Management Commands:"
    echo "  - Start VM: qm start $VMID"
    echo "  - Stop VM: qm stop $VMID"
    echo "  - Console: qm terminal $VMID"
    echo "  - Status: qm status $VMID"
    echo "  - Backup: /opt/truenas-backup/backup_truenas.sh"
    echo "============================================="
}

create_integration_scripts() {
    print_status "Creating integration scripts..."

    # Create mount script for containers
    cat > /opt/truenas-backup/mount_truenas_shares.sh << 'EOF'
#!/bin/bash
# Script to mount TrueNAS shares in LXC containers

TRUENAS_IP="192.168.0.300"
CONTAINERS="100 200 230 400"

for container in $CONTAINERS; do
    if pct status $container | grep -q "running"; then
        echo "Configuring TrueNAS mounts for container $container..."

        pct exec $container -- bash -c "
            apt update && apt install -y nfs-common
            mkdir -p /mnt/truenas/{config,data,backups,media}

            # Add NFS mounts to fstab
            grep -q truenas /etc/fstab || {
                echo '$TRUENAS_IP:/mnt/homelab/home-assistant/config /mnt/truenas/config nfs defaults 0 0' >> /etc/fstab
                echo '$TRUENAS_IP:/mnt/homelab/home-assistant/data /mnt/truenas/data nfs defaults 0 0' >> /etc/fstab
                echo '$TRUENAS_IP:/mnt/homelab/backups /mnt/truenas/backups nfs defaults 0 0' >> /etc/fstab
                echo '$TRUENAS_IP:/mnt/homelab/shared/media /mnt/truenas/media nfs defaults 0 0' >> /etc/fstab
            }

            # Mount all shares
            mount -a
        "

        echo "Container $container configured for TrueNAS integration"
    fi
done
EOF

    chmod +x /opt/truenas-backup/mount_truenas_shares.sh

    # Create health check script
    cat > /opt/truenas-backup/check_truenas_health.sh << 'EOF'
#!/bin/bash
# TrueNAS Health Check Script

TRUENAS_IP="192.168.0.300"
VM_ID=300

echo "TrueNAS Health Check - $(date)"
echo "================================"

# Check VM status
VM_STATUS=$(qm status $VM_ID | awk '{print $2}')
echo "VM Status: $VM_STATUS"

# Check network connectivity
if ping -c 1 $TRUENAS_IP >/dev/null 2>&1; then
    echo "Network: OK"

    # Check web interface
    if curl -k -s "https://$TRUENAS_IP" >/dev/null; then
        echo "Web Interface: OK"
    else
        echo "Web Interface: FAILED"
    fi

    # Check NFS service
    if showmount -e $TRUENAS_IP >/dev/null 2>&1; then
        echo "NFS Service: OK"
        echo "Available exports:"
        showmount -e $TRUENAS_IP | tail -n +2
    else
        echo "NFS Service: FAILED"
    fi
else
    echo "Network: FAILED - Cannot reach $TRUENAS_IP"
fi

echo "================================"
EOF

    chmod +x /opt/truenas-backup/check_truenas_health.sh

    print_success "Integration scripts created"
}

main() {
    echo "🗄️ TrueNAS SCALE - Proxmox VM Deployment"
    echo "========================================"
    echo "VM ID: $VMID"
    echo "Cores: $CORES"
    echo "Memory: ${MEMORY}MB"
    echo "OS Disk: ${DISK_SIZE}GB"
    echo ""

    check_requirements
    detect_storage_devices
    stop_existing_vm
    create_vm
    add_storage
    configure_passthrough
    optimize_vm_settings
    create_backup_storage
    create_integration_scripts
    display_post_install
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --vm-id)
            VMID="$2"
            shift 2
            ;;
        --memory)
            MEMORY="$2"
            shift 2
            ;;
        --cores)
            CORES="$2"
            shift 2
            ;;
        --disk-size)
            DISK_SIZE="$2"
            shift 2
            ;;
        --disk-passthrough)
            PASSTHROUGH_DISKS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --vm-id ID          VM ID (default: 300)"
            echo "  --memory MB         Memory in MB (default: 16384)"
            echo "  --cores NUM         Number of CPU cores (default: 4)"
            echo "  --disk-size GB      OS disk size in GB (default: 32)"
            echo "  --disk-passthrough  Comma-separated list of disks to passthrough"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            VMID="$1"
            shift
            ;;
    esac
done

# Run main function
main "$@"