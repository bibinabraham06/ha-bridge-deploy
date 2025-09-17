#!/usr/bin/env python3
"""
Frigate AI Deployment Script
Deploys Frigate NVR with AI detection for your Unifi cameras
"""

import requests
import json
import os
import subprocess

def check_current_setup():
    """Check current camera setup"""

    print("🔍 ANALYZING CURRENT CAMERA SETUP")
    print("=" * 50)

    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIwMjM1N2RjZDBhMTY0NjJmYTBkNTlhMzczMjc2Y2ZhYSIsImlhdCI6MTc1ODA0NjE3MywiZXhwIjoyMDczNDA2MTczfQ.7tYGiaSHeTFsZTZusbSuRiDp_jFJEUyIKbOf3nc4UOw'

    try:
        response = requests.get(
            'http://192.168.0.81:8123/api/states',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )

        if response.status_code == 200:
            states = response.json()
            cameras = [s for s in states if s['entity_id'].startswith('camera.')]

            print(f"📹 Found {len(cameras)} cameras in Home Assistant:")
            for cam in cameras:
                name = cam['attributes'].get('friendly_name', cam['entity_id'])
                state = cam.get('state', 'unknown')
                print(f"   • {name} - {state}")

            return cameras
        else:
            print(f"❌ Error accessing HA: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def show_frigate_benefits():
    """Show what Frigate will add"""

    print("\n🤖 FRIGATE AI BENEFITS")
    print("=" * 30)

    benefits = [
        {
            "feature": "🎯 Smart Person Detection",
            "before": "Generic motion alerts",
            "after": "Only alerts when people detected",
            "voice_command": "'Any people at the front door?'"
        },
        {
            "feature": "📦 Package Detection",
            "before": "Miss package deliveries",
            "after": "Instant package delivery alerts",
            "voice_command": "'Was a package delivered today?'"
        },
        {
            "feature": "🚗 Vehicle Intelligence",
            "before": "All movement triggers alerts",
            "after": "Distinguish cars from people",
            "voice_command": "'Any cars in the driveway?'"
        },
        {
            "feature": "📊 AI Search & Analytics",
            "before": "Manual video review",
            "after": "Search by object type and time",
            "voice_command": "'Show all person events today'"
        },
        {
            "feature": "🎭 Custom Detection Zones",
            "before": "Whole camera view alerts",
            "after": "Only alert for specific areas",
            "voice_command": "'Any motion in the walkway?'"
        }
    ]

    for benefit in benefits:
        print(f"\n{benefit['feature']}")
        print(f"   Before: {benefit['before']}")
        print(f"   After:  {benefit['after']}")
        print(f"   Voice:  {benefit['voice_command']}")

def show_deployment_steps():
    """Show step-by-step deployment process"""

    print("\n🚀 FRIGATE DEPLOYMENT STEPS")
    print("=" * 40)

    steps = [
        {
            "step": "1. Get Camera Stream URLs",
            "description": "Extract RTSP URLs from Unifi Protect",
            "action": "Access Unifi Protect Console → Camera Settings → RTSP URLs",
            "time": "5 minutes"
        },
        {
            "step": "2. Deploy on Proxmox",
            "description": "Set up Frigate container with AI detection",
            "action": "Docker compose deployment with optimized settings",
            "time": "10 minutes"
        },
        {
            "step": "3. Configure Camera Streams",
            "description": "Connect Frigate to your 5 cameras",
            "action": "Update config with your specific RTSP URLs",
            "time": "15 minutes"
        },
        {
            "step": "4. Set Detection Zones",
            "description": "Define smart zones for each camera",
            "action": "Use Frigate UI to draw detection areas",
            "time": "20 minutes"
        },
        {
            "step": "5. Integrate with Voice System",
            "description": "Add AI queries to voice commands",
            "action": "Enhance bridge with Frigate API calls",
            "time": "15 minutes"
        },
        {
            "step": "6. Test & Optimize",
            "description": "Verify detection and tune settings",
            "action": "Walk around property to test detection",
            "time": "10 minutes"
        }
    ]

    total_time = sum(int(step['time'].split()[0]) for step in steps)

    for step in steps:
        print(f"\n📋 {step['step']} ({step['time']})")
        print(f"   {step['description']}")
        print(f"   → {step['action']}")

    print(f"\n⏱️  Total deployment time: ~{total_time} minutes")

def generate_stream_url_helper():
    """Help user get camera stream URLs"""

    print("\n🔗 GETTING UNIFI PROTECT STREAM URLS")
    print("=" * 45)

    instructions = [
        "1. Open Unifi Protect in your browser",
        "2. Go to Settings → Cameras",
        "3. Select each camera and click 'Manage'",
        "4. Look for 'RTSP' or 'Streaming' settings",
        "5. Copy the RTSP URL (format: rtsp://IP:PORT/stream_id)",
        "6. Note the stream ID for each camera"
    ]

    for instruction in instructions:
        print(f"   {instruction}")

    print("\n📝 TYPICAL STREAM URL FORMAT:")
    print("   rtsp://192.168.0.XXX:7447/[STREAM_ID]")
    print("   Example: rtsp://192.168.0.100:7447/abc123def456")

    print("\n🎯 YOU'LL NEED URLS FOR:")
    cameras = [
        "Front Door Camera (Doorbell)",
        "Driveway Camera",
        "Garage Camera",
        "Backyard Patio Camera",
        "Back Road Camera"
    ]

    for i, camera in enumerate(cameras, 1):
        print(f"   {i}. {camera}")

def show_resource_requirements():
    """Show Proxmox resource requirements"""

    print("\n💾 PROXMOX RESOURCE REQUIREMENTS")
    print("=" * 40)

    requirements = {
        "CPU": {
            "minimum": "2 cores",
            "recommended": "4 cores",
            "note": "For AI processing of 5 camera streams"
        },
        "RAM": {
            "minimum": "4 GB",
            "recommended": "8 GB",
            "note": "More RAM = better caching and performance"
        },
        "Storage": {
            "minimum": "100 GB",
            "recommended": "500 GB+",
            "note": "For 7 days of smart recordings"
        },
        "Network": {
            "minimum": "100 Mbps",
            "recommended": "1 Gbps",
            "note": "To handle 5 simultaneous camera streams"
        }
    }

    for component, specs in requirements.items():
        print(f"\n{component}:")
        print(f"   Minimum: {specs['minimum']}")
        print(f"   Recommended: {specs['recommended']}")
        print(f"   Note: {specs['note']}")

def show_voice_command_examples():
    """Show new voice commands with Frigate"""

    print("\n🎙️  NEW VOICE COMMANDS WITH FRIGATE AI")
    print("=" * 50)

    command_categories = [
        {
            "category": "🔍 Detection Queries",
            "commands": [
                "'Any people at the front door?'",
                "'Show me recent person detections'",
                "'Was anyone in the driveway today?'",
                "'Any motion in the backyard?'"
            ]
        },
        {
            "category": "📦 Package & Delivery",
            "commands": [
                "'Was a package delivered?'",
                "'Show package detection events'",
                "'Any deliveries at the front door?'",
                "'Check for packages today'"
            ]
        },
        {
            "category": "🚗 Vehicle Detection",
            "commands": [
                "'Any cars in the driveway?'",
                "'Show vehicle detections'",
                "'Was there a truck today?'",
                "'Check driveway for vehicles'"
            ]
        },
        {
            "category": "📊 Smart Analytics",
            "commands": [
                "'How many people visited today?'",
                "'Show all detection events'",
                "'Any activity last hour?'",
                "'Search for motion events'"
            ]
        }
    ]

    for category in command_categories:
        print(f"\n{category['category']}")
        for command in category['commands']:
            print(f"   • {command}")

def show_next_steps():
    """Show immediate next steps"""

    print("\n🎯 IMMEDIATE NEXT STEPS")
    print("=" * 30)

    next_steps = [
        {
            "priority": "HIGH",
            "task": "Get Camera Stream URLs",
            "description": "Essential for Frigate configuration",
            "estimated_time": "10 minutes"
        },
        {
            "priority": "HIGH",
            "task": "Choose Proxmox Container",
            "description": "Decide which container will host Frigate",
            "estimated_time": "5 minutes"
        },
        {
            "priority": "MEDIUM",
            "task": "Deploy Frigate",
            "description": "Run docker-compose with provided configuration",
            "estimated_time": "15 minutes"
        },
        {
            "priority": "MEDIUM",
            "task": "Configure Detection Zones",
            "description": "Set up smart zones for each camera",
            "estimated_time": "20 minutes"
        },
        {
            "priority": "LOW",
            "task": "Integrate with Voice Commands",
            "description": "Add AI queries to existing voice system",
            "estimated_time": "30 minutes"
        }
    ]

    for step in next_steps:
        priority_emoji = "🔴" if step["priority"] == "HIGH" else "🟡" if step["priority"] == "MEDIUM" else "🟢"
        print(f"\n{priority_emoji} {step['priority']}: {step['task']} ({step['estimated_time']})")
        print(f"   {step['description']}")

def main():
    """Main execution"""

    print("🤖🏠 FRIGATE AI DEPLOYMENT FOR UNIFI CAMERAS")
    print("=" * 60)

    # Check current setup
    cameras = check_current_setup()

    if cameras:
        # Show benefits
        show_frigate_benefits()

        # Show deployment process
        show_deployment_steps()

        # Help with stream URLs
        generate_stream_url_helper()

        # Resource requirements
        show_resource_requirements()

        # New voice commands
        show_voice_command_examples()

        # Next steps
        show_next_steps()

        print(f"\n{'='*60}")
        print("🎉 FRIGATE DEPLOYMENT PLAN READY!")
        print()
        print("📁 FILES CREATED:")
        print("   • frigate-docker-compose.yml")
        print("   • frigate-config.yml")
        print("   • frigate_deployment_guide.md")
        print()
        print("🚀 READY TO DEPLOY:")
        print("   1. Get your camera RTSP URLs")
        print("   2. Update frigate-config.yml with URLs")
        print("   3. Deploy on Proxmox with docker-compose")
        print("   4. Configure detection zones")
        print("   5. Test AI detection")
        print()
        print("💡 Your Unifi cameras will become AI-powered!")

    else:
        print("\n❌ Unable to access camera information.")
        print("Please ensure Home Assistant is accessible.")

if __name__ == "__main__":
    main()