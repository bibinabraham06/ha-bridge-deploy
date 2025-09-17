# 🤖 FRIGATE AI DEPLOYMENT FOR UNIFI CAMERAS

## 📊 Current Setup Analysis
- ✅ 5 Unifi Protect Cameras (all recording)
- ✅ Proxmox infrastructure ready
- ✅ Home Assistant integration active
- ✅ Voice camera control deployed

## 🎯 Frigate Benefits for Your Setup

### What Frigate Adds to Your Unifi Cameras:
- **Person Detection**: "Someone is at the front door"
- **Vehicle Detection**: "Car in driveway"
- **Package Detection**: "Package delivered"
- **Zone-based Alerts**: "Motion in walkway area"
- **Smart Notifications**: Only alert for relevant activity
- **AI-powered Search**: "Show me all people detected today"

## 🚀 DEPLOYMENT PLAN

### Phase 1: Basic Frigate Setup (This Session)
1. Deploy Frigate container on Proxmox
2. Configure your 5 Unifi camera streams
3. Set up basic person/vehicle detection
4. Test AI detection capabilities

### Phase 2: Advanced Configuration (Next)
1. Custom detection zones for each camera
2. Integration with voice commands
3. Smart notifications and automations
4. Mobile alerts for specific events

## 📋 IMPLEMENTATION STEPS

### Step 1: Frigate Docker Configuration

```yaml
# frigate-docker-compose.yml
version: "3.9"
services:
  frigate:
    container_name: frigate
    privileged: true
    restart: unless-stopped
    image: ghcr.io/blakeblackshear/frigate:stable
    shm_size: "256mb"
    devices:
      - /dev/dri/renderD128 # Intel GPU acceleration (if available)
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - ./config:/config
      - ./storage:/media/frigate
      - type: tmpfs
        target: /tmp/cache
        tmpfs:
          size: 1000000000
    ports:
      - "5000:5000"   # Frigate Web UI
      - "8971:8971"   # Go2RTC
      - "8554:8554"   # RTSP
    environment:
      FRIGATE_RTSP_PASSWORD: "YOUR_PROTECT_PASSWORD"
    networks:
      - frigate

networks:
  frigate:
    driver: bridge
```

### Step 2: Frigate Configuration for Your Cameras

```yaml
# config/config.yml
mqtt:
  host: 192.168.0.81  # Your HA IP
  port: 1883
  topic_prefix: frigate
  client_id: frigate

database:
  path: /media/frigate/frigate.db

# AI Detection Models
model:
  width: 320
  height: 320
  input_tensor: nhwc
  input_pixel_format: rgb
  path: /openvino-model/ssdlite_mobilenet_v2.xml
  labelmap_path: /openvino-model/coco_91cl_bkgr.txt

detectors:
  ov:
    type: openvino
    device: AUTO

# Your 5 Unifi Protect Cameras
cameras:
  front_door:
    ffmpeg:
      inputs:
        - path: rtsp://192.168.0.XXX:7447/YOUR_DOORBELL_STREAM_ID
          roles:
            - detect
            - record
    detect:
      width: 1920
      height: 1080
      fps: 5
    record:
      enabled: true
      retain:
        days: 7
        mode: motion
    snapshots:
      enabled: true
      timestamp: false
      bounding_box: true
    zones:
      entrance:
        coordinates: 400,0,1520,0,1520,400,400,400
      walkway:
        coordinates: 0,400,1920,400,1920,800,0,800

  driveway:
    ffmpeg:
      inputs:
        - path: rtsp://192.168.0.XXX:7447/YOUR_DRIVEWAY_STREAM_ID
          roles:
            - detect
            - record
    detect:
      width: 1920
      height: 1080
      fps: 5
    zones:
      car_area:
        coordinates: 200,200,1720,200,1720,880,200,880
      street:
        coordinates: 0,0,1920,200,1920,1080,0,1080

  garage:
    ffmpeg:
      inputs:
        - path: rtsp://192.168.0.XXX:7447/YOUR_GARAGE_STREAM_ID
          roles:
            - detect
            - record
    detect:
      width: 1920
      height: 1080
      fps: 5
    zones:
      garage_door:
        coordinates: 600,300,1320,300,1320,780,600,780

  backyard_patio:
    ffmpeg:
      inputs:
        - path: rtsp://192.168.0.XXX:7447/YOUR_PATIO_STREAM_ID
          roles:
            - detect
            - record
    detect:
      width: 1920
      height: 1080
      fps: 5
    zones:
      patio_area:
        coordinates: 400,400,1520,400,1520,680,400,680

  back_road:
    ffmpeg:
      inputs:
        - path: rtsp://192.168.0.XXX:7447/YOUR_ROAD_STREAM_ID
          roles:
            - detect
            - record
    detect:
      width: 1920
      height: 1080
      fps: 5

# Object Detection Configuration
objects:
  track:
    - person
    - car
    - truck
    - bicycle
    - motorcycle
    - dog
    - cat
    - package  # Custom detection for deliveries
  filters:
    person:
      min_area: 2500
      max_area: 100000
      threshold: 0.75
      min_score: 0.60
    car:
      min_area: 15000
      max_area: 200000
      threshold: 0.70
    package:
      min_area: 1000
      max_area: 50000
      threshold: 0.65

# Recording Configuration
record:
  enabled: true
  retain:
    days: 7
    mode: active_objects
  events:
    retain:
      default: 7
      mode: motion
```

### Step 3: Getting Camera Stream URLs

You'll need to get the RTSP stream URLs from your Unifi Protect system:

1. **Access Unifi Protect Console**
2. **Go to Camera Settings** for each camera
3. **Find RTSP Stream URLs** (usually in Advanced settings)
4. **Note the stream IDs** for each camera

Typical format: `rtsp://192.168.0.XXX:7447/[STREAM_ID]`

### Step 4: Proxmox Deployment

```bash
# On your Proxmox host
mkdir -p /opt/frigate
cd /opt/frigate

# Create docker-compose.yml with the configuration above
# Create config directory
mkdir -p config storage

# Deploy Frigate
docker-compose up -d
```

## 🎙️ VOICE COMMAND INTEGRATION

Once Frigate is running, we'll enhance your voice system with AI queries:

### New Voice Commands You'll Have:
- **"Any people at the front door?"**
- **"Show me recent motion events"**
- **"Was there a package delivered?"**
- **"Any cars in the driveway today?"**
- **"Show me all person detections"**

### Enhanced Camera Commands:
- **"Show front door with recent alerts"**
- **"Check driveway for vehicles"**
- **"Any motion in the backyard?"**

## 📱 SMART NOTIFICATIONS

Frigate will enable intelligent alerts:

```yaml
# Home Assistant automation examples
- alias: "Package Delivered Alert"
  trigger:
    platform: mqtt
    topic: frigate/events
  condition:
    condition: template
    value_template: "{{ trigger.payload_json.type == 'package' }}"
  action:
    - service: notify.mobile_app
      data:
        title: "📦 Package Delivered"
        message: "Package detected at {{ trigger.payload_json.camera }}"

- alias: "Person at Door"
  trigger:
    platform: mqtt
    topic: frigate/front_door/person
  action:
    - service: tts.speak
      data:
        message: "Someone is at the front door"
```

## 🔧 RESOURCE REQUIREMENTS

For your Proxmox setup:
- **CPU**: 2-4 cores dedicated to Frigate
- **RAM**: 4-8GB (depending on number of cameras)
- **Storage**: 500GB+ for recordings
- **Network**: Good bandwidth to handle 5 camera streams

## 📊 EXPECTED BENEFITS

### Before Frigate:
- Basic camera recording
- Manual review of footage
- Generic motion alerts

### After Frigate:
- **Smart person detection**: "John arrived home"
- **Package alerts**: "Delivery at front door"
- **Vehicle tracking**: "Unknown car in driveway"
- **Zone-based monitoring**: "Motion in restricted area"
- **AI search**: "Show all people from yesterday"

## 🎯 SUCCESS METRICS

You'll know Frigate is working when:
1. ✅ All 5 cameras show detection zones in Frigate UI
2. ✅ Person detection events appear in real-time
3. ✅ Voice commands return AI-powered responses
4. ✅ Smart notifications only for relevant events
5. ✅ Searchable AI event database

Your Unifi cameras will transform from passive recording to intelligent monitoring!