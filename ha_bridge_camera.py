#!/usr/bin/env python3
"""
Enhanced Home Assistant AI Bridge with Voice Camera Control
Adds camera control capabilities to the existing bridge
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app)

# Configuration
HA_URL = os.getenv('HA_URL', 'http://192.168.0.81:8123')
HA_TOKEN = os.getenv('HA_TOKEN', 'your_token_here')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://100.94.114.43:11434')

# Headers for HA API
HA_HEADERS = {
    'Authorization': f'Bearer {HA_TOKEN}',
    'Content-Type': 'application/json'
}

# Camera mappings for your specific Unifi Protect cameras
CAMERA_MAPPINGS = {
    'front door': 'camera.doorbell_main_entrance_camera_high_resolution_channel',
    'doorbell': 'camera.doorbell_main_entrance_camera_high_resolution_channel',
    'entrance': 'camera.doorbell_main_entrance_camera_high_resolution_channel',
    'main entrance': 'camera.doorbell_main_entrance_camera_high_resolution_channel',

    'driveway': 'camera.front_lt_driveway_camera_high_resolution_channel',
    'front driveway': 'camera.front_lt_driveway_camera_high_resolution_channel',
    'front left': 'camera.front_lt_driveway_camera_high_resolution_channel',

    'backyard': 'camera.back_rt_facing_patio_camera_high_resolution_channel',
    'patio': 'camera.back_rt_facing_patio_camera_high_resolution_channel',
    'back patio': 'camera.back_rt_facing_patio_camera_high_resolution_channel',
    'back right': 'camera.back_rt_facing_patio_camera_high_resolution_channel',

    'back road': 'camera.back_lt_facing_road_camera_high_resolution_channel',
    'road': 'camera.back_lt_facing_road_camera_high_resolution_channel',
    'back left': 'camera.back_lt_facing_road_camera_high_resolution_channel',

    'garage': 'camera.garage_camera_high_resolution_channel',
    'garage door': 'camera.garage_camera_high_resolution_channel'
}

# Camera friendly names for responses
CAMERA_NAMES = {
    'camera.doorbell_main_entrance_camera_high_resolution_channel': 'Front Door Camera',
    'camera.front_lt_driveway_camera_high_resolution_channel': 'Driveway Camera',
    'camera.back_rt_facing_patio_camera_high_resolution_channel': 'Backyard Patio Camera',
    'camera.back_lt_facing_road_camera_high_resolution_channel': 'Back Road Camera',
    'camera.garage_camera_high_resolution_channel': 'Garage Camera'
}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "ha-ai-bridge-camera"})

@app.route('/test_connections', methods=['GET'])
def test_connections():
    """Test all connections"""
    results = {}

    # Test HA connection
    try:
        response = requests.get(f"{HA_URL}/api/", headers=HA_HEADERS, timeout=5)
        results['home_assistant'] = {
            'status': 'connected' if response.status_code == 200 else 'auth_error',
            'code': response.status_code
        }
    except Exception as e:
        results['home_assistant'] = {'status': 'error', 'error': str(e)}

    # Test AI connection
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            results['ai_service'] = {
                'status': 'connected',
                'models_count': len(models),
                'models': [m['name'] for m in models]
            }
        else:
            results['ai_service'] = {'status': 'error', 'code': response.status_code}
    except Exception as e:
        results['ai_service'] = {'status': 'error', 'error': str(e)}

    return jsonify(results)

def detect_camera_command(command):
    """Detect if this is a camera-related command"""
    camera_keywords = ['show', 'display', 'camera', 'view', 'check', 'see', 'look at', 'watch']
    command_lower = command.lower()

    return any(keyword in command_lower for keyword in camera_keywords)

def find_camera_entity(command):
    """Find the camera entity based on voice command"""
    command_lower = command.lower()

    # Check each mapping
    for keyword, entity in CAMERA_MAPPINGS.items():
        if keyword in command_lower:
            return entity, CAMERA_NAMES.get(entity, keyword.title())

    return None, None

@app.route('/voice_command', methods=['POST'])
def voice_command():
    """Process voice commands for smart home with camera support"""
    try:
        data = request.json
        command = data.get('command', '')

        if not command:
            return jsonify({"error": "No command provided"}), 400

        # Check if this is a camera command
        if detect_camera_command(command):
            return handle_camera_command(command)
        else:
            return handle_general_command(command)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def handle_camera_command(command):
    """Handle camera-specific voice commands"""
    try:
        # Find the camera
        camera_entity, camera_name = find_camera_entity(command)

        if not camera_entity:
            return jsonify({
                "success": False,
                "error": "Camera not found",
                "available_cameras": list(CAMERA_NAMES.values()),
                "command": command
            })

        # Get camera snapshot/stream
        snapshot_url = f"{HA_URL}/api/camera_proxy/{camera_entity}"

        # Test if camera is accessible
        try:
            test_response = requests.get(snapshot_url, headers=HA_HEADERS, timeout=5)
            camera_accessible = test_response.status_code == 200
        except:
            camera_accessible = False

        return jsonify({
            "success": True,
            "command": command,
            "camera_entity": camera_entity,
            "camera_name": camera_name,
            "camera_accessible": camera_accessible,
            "snapshot_url": snapshot_url if camera_accessible else None,
            "stream_url": f"{HA_URL}/api/camera_proxy_stream/{camera_entity}",
            "response": f"Displaying {camera_name}. Camera is {'online' if camera_accessible else 'offline'}."
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "command": command
        })

def handle_general_command(command):
    """Handle general smart home commands (original functionality)"""
    try:
        # Simplified AI prompt for faster response
        prompt = f'Convert to JSON: {command}. Use format: {{\"domain\":\"light\",\"service\":\"turn_on\",\"entity_id\":\"light.kitchen_lights_light_1\"}}'

        # Ask AI what to do
        ai_response = requests.post(f"{OLLAMA_URL}/api/generate",
                                   json={
                                       "model": "dolphin-llama3:latest",
                                       "prompt": prompt,
                                       "stream": False
                                   }, timeout=15)

        if ai_response.status_code == 200:
            ai_result = ai_response.json().get('response', '')

            try:
                # Parse AI response
                action = json.loads(ai_result)

                # Execute the action
                result = execute_ha_action(action)

                return jsonify({
                    "success": True,
                    "command": command,
                    "ai_interpretation": action,
                    "execution_result": result,
                    "response": f"Executed {action.get('domain', 'unknown')}.{action.get('service', 'unknown')}"
                })

            except json.JSONDecodeError:
                return jsonify({
                    "success": False,
                    "error": "AI response was not valid JSON",
                    "ai_response": ai_result
                })
        else:
            return jsonify({"error": "AI service unavailable"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/camera_command', methods=['POST'])
def camera_command():
    """Dedicated camera command endpoint"""
    try:
        data = request.json
        command = data.get('command', '')

        if not command:
            return jsonify({"error": "No command provided"}), 400

        return handle_camera_command(command)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list_cameras', methods=['GET'])
def list_cameras():
    """List all available cameras"""
    return jsonify({
        "cameras": CAMERA_NAMES,
        "camera_keywords": list(CAMERA_MAPPINGS.keys()),
        "example_commands": [
            "Show me the front door",
            "Check the driveway camera",
            "Display garage camera",
            "Look at the backyard",
            "View the road camera"
        ]
    })

@app.route('/camera_status', methods=['GET'])
def camera_status():
    """Check status of all cameras"""
    try:
        camera_statuses = {}

        for entity, name in CAMERA_NAMES.items():
            try:
                # Check camera state
                state_response = requests.get(
                    f"{HA_URL}/api/states/{entity}",
                    headers=HA_HEADERS,
                    timeout=5
                )

                if state_response.status_code == 200:
                    state_data = state_response.json()
                    camera_statuses[name] = {
                        "entity_id": entity,
                        "state": state_data.get('state', 'unknown'),
                        "accessible": True,
                        "snapshot_url": f"{HA_URL}/api/camera_proxy/{entity}"
                    }
                else:
                    camera_statuses[name] = {
                        "entity_id": entity,
                        "accessible": False,
                        "error": f"HTTP {state_response.status_code}"
                    }

            except Exception as e:
                camera_statuses[name] = {
                    "entity_id": entity,
                    "accessible": False,
                    "error": str(e)
                }

        return jsonify({
            "camera_statuses": camera_statuses,
            "total_cameras": len(CAMERA_NAMES)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def execute_ha_action(action):
    """Execute a Home Assistant action"""
    try:
        domain = action.get('domain')
        service = action.get('service')
        entity_id = action.get('entity_id')
        service_data = action.get('service_data', {})

        if entity_id:
            service_data['entity_id'] = entity_id

        url = f"{HA_URL}/api/services/{domain}/{service}"
        response = requests.post(url, headers=HA_HEADERS, json=service_data, timeout=10)

        return {
            "success": response.status_code == 200,
            "action": f"{domain}.{service}",
            "entity": entity_id,
            "status_code": response.status_code
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == '__main__':
    print("🏠📹 Home Assistant AI Bridge with Camera Control Starting...")
    print(f"HA URL: {HA_URL}")
    print(f"AI URL: {OLLAMA_URL}")
    print(f"Available Cameras: {len(CAMERA_NAMES)}")
    for name in CAMERA_NAMES.values():
        print(f"   - {name}")
    print("Bridge ready on port 5002!")

    app.run(host='0.0.0.0', port=5002, debug=False)