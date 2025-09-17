#!/usr/bin/env python3
"""
Smart Home Voice Command Web UI
Modern web interface for voice commands and camera control
"""

from flask import Flask, render_template_string, request, jsonify, send_from_directory, Response
import requests
import json
import os

app = Flask(__name__)

# Configuration
HA_URL = os.getenv('HA_URL', 'http://192.168.0.81:8123')
HA_TOKEN = os.getenv('HA_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIwMjM1N2RjZDBhMTY0NjJmYTBkNTlhMzczMjc2Y2ZhYSIsImlhdCI6MTc1ODA0NjE3MywiZXhwIjoyMDczNDA2MTczfQ.7tYGiaSHeTFsZTZusbSuRiDp_jFJEUyIKbOf3nc4UOw')
CAMERA_BRIDGE_URL = 'http://localhost:5002'
MAIN_BRIDGE_URL = 'http://localhost:5001'

# Camera entity mappings
CAMERA_ENTITIES = {
    'front_door': 'camera.doorbell_main_entrance_camera_high_resolution_channel',
    'garage': 'camera.garage_camera_high_resolution_channel',
    'driveway': 'camera.front_lt_driveway_camera_high_resolution_channel',
    'backyard': 'camera.back_rt_facing_patio_camera_high_resolution_channel',
    'back_road': 'camera.back_lt_facing_road_camera_high_resolution_channel'
}

# Headers for HA API
HA_HEADERS = {
    'Authorization': f'Bearer {HA_TOKEN}',
    'Content-Type': 'application/json'
}

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏠 Smart Home Voice Command Center</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .status-bar {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            justify-content: center;
        }

        .status-item {
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            backdrop-filter: blur(10px);
        }

        .status-item.healthy { background: rgba(46, 204, 113, 0.3); }
        .status-item.error { background: rgba(231, 76, 60, 0.3); }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        @media (max-width: 768px) {
            .main-content { grid-template-columns: 1fr; }
        }

        .card {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
        }

        .card h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.4em;
        }

        .voice-input {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        #commandInput {
            flex: 1;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        #commandInput:focus {
            outline: none;
            border-color: #667eea;
        }

        .btn {
            padding: 15px 25px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
            font-size: 14px;
        }

        .btn-primary {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .btn-voice {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
            color: white;
            min-width: 120px;
        }

        .btn-voice:hover {
            transform: translateY(-2px);
        }

        .example-commands {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }

        .example-cmd {
            background: #f8f9fa;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            transition: background 0.3s;
            border: 1px solid #e9ecef;
            font-size: 13px;
        }

        .example-cmd:hover {
            background: #e9ecef;
        }

        .camera-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }

        .camera-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            border: 2px solid #e9ecef;
            transition: all 0.3s;
            cursor: pointer;
        }

        .camera-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
        }

        .camera-card.active {
            border-color: #28a745;
            background: #d4edda;
        }

        .camera-preview {
            width: 100%;
            height: 150px;
            background: #dee2e6;
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: #6c757d;
        }

        .response-area {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            min-height: 100px;
        }

        .response-success {
            border-left-color: #28a745;
            background: #d4edda;
        }

        .response-error {
            border-left-color: #dc3545;
            background: #f8d7da;
        }

        .loading {
            display: none;
            text-align: center;
            color: #667eea;
            font-weight: bold;
        }

        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }

        .metric {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }

        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }

        .metric-label {
            font-size: 12px;
            color: #6c757d;
            margin-top: 5px;
        }

        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }

        .quick-action {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            cursor: pointer;
            transition: transform 0.3s;
        }

        .quick-action:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 Smart Home Voice Command Center</h1>
            <p>Control your Unifi cameras and smart home with voice commands</p>
        </div>

        <div class="status-bar" id="statusBar">
            <div class="status-item" id="cameraStatus">📹 Camera Bridge: Checking...</div>
            <div class="status-item" id="mainStatus">🤖 AI Bridge: Checking...</div>
            <div class="status-item" id="haStatus">🏠 Home Assistant: Checking...</div>
        </div>

        <div class="main-content">
            <!-- Voice Command Panel -->
            <div class="card">
                <h2>🎙️ Voice Commands</h2>
                <div class="voice-input">
                    <input type="text" id="commandInput" placeholder="Say something like 'Show me the front door'...">
                    <button class="btn btn-voice" onclick="startVoiceRecognition()">🎤 Voice</button>
                    <button class="btn btn-primary" onclick="sendCommand()">Send</button>
                </div>

                <div class="example-commands">
                    <div class="example-cmd" onclick="setCommand('Show me the front door')">🚪 Front Door</div>
                    <div class="example-cmd" onclick="setCommand('Check the garage camera')">🚗 Garage</div>
                    <div class="example-cmd" onclick="setCommand('Display driveway camera')">🛣️ Driveway</div>
                    <div class="example-cmd" onclick="setCommand('Look at the backyard')">🌿 Backyard</div>
                    <div class="example-cmd" onclick="setCommand('View the road camera')">🛤️ Road</div>
                    <div class="example-cmd" onclick="setCommand('Turn on living room lights')">💡 Lights</div>
                </div>

                <div class="loading" id="loading">🔄 Processing command...</div>
                <div class="response-area" id="responseArea">
                    Ready for voice commands! Try asking to see a camera or control smart home devices.
                </div>
            </div>

            <!-- Camera Dashboard -->
            <div class="card">
                <h2>📹 Camera Dashboard</h2>
                <div class="camera-grid" id="cameraGrid">
                    <!-- Cameras loaded dynamically -->
                </div>

                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value" id="totalCameras">0</div>
                        <div class="metric-label">Total Cameras</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="activeCameras">0</div>
                        <div class="metric-label">Active Cameras</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="commandCount">0</div>
                        <div class="metric-label">Commands Sent</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="card">
            <h2>⚡ Quick Actions</h2>
            <div class="quick-actions">
                <div class="quick-action" onclick="setCommand('Show all cameras')">📹 View All Cameras</div>
                <div class="quick-action" onclick="setCommand('Turn on all lights')">💡 All Lights On</div>
                <div class="quick-action" onclick="setCommand('Check security status')">🔒 Security Check</div>
                <div class="quick-action" onclick="setCommand('Set thermostat to 72')">🌡️ Climate Control</div>
                <div class="quick-action" onclick="refreshStatus()">🔄 Refresh Status</div>
                <div class="quick-action" onclick="window.open('{{ ha_url }}', '_blank')">🏠 Open Home Assistant</div>
            </div>
        </div>
    </div>

    <script>
        // Camera entity mappings from server
        const CAMERA_ENTITIES = {
            'front_door': 'camera.doorbell_main_entrance_camera_high_resolution_channel',
            'garage': 'camera.garage_camera_high_resolution_channel',
            'driveway': 'camera.front_lt_driveway_camera_high_resolution_channel',
            'backyard': 'camera.back_rt_facing_patio_camera_high_resolution_channel',
            'back_road': 'camera.back_lt_facing_road_camera_high_resolution_channel'
        };

        let commandCount = 0;

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            checkSystemStatus();
            loadCameras();

            // Enter key support
            document.getElementById('commandInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendCommand();
                }
            });

            // Auto-refresh status every 30 seconds
            setInterval(checkSystemStatus, 30000);
        });

        function setCommand(command) {
            document.getElementById('commandInput').value = command;
        }

        async function sendCommand() {
            const input = document.getElementById('commandInput');
            const command = input.value.trim();

            if (!command) return;

            const loading = document.getElementById('loading');
            const responseArea = document.getElementById('responseArea');

            loading.style.display = 'block';
            responseArea.className = 'response-area';
            responseArea.innerHTML = '';

            try {
                // Determine which bridge to use (camera commands go to port 5002)
                const isCameraCommand = /show|display|camera|view|check|see|look at|watch/i.test(command);
                const url = isCameraCommand ?
                    'http://localhost:5002/voice_command' :
                    'http://localhost:5001/voice_command';

                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ command: command })
                });

                const result = await response.json();

                if (response.ok) {
                    responseArea.className = 'response-area response-success';

                    if (result.camera_info) {
                        responseArea.innerHTML = `
                            <strong>✅ ${result.response || 'Camera loaded successfully'}</strong><br><br>
                            <strong>Camera:</strong> ${result.camera_info.name}<br>
                            <strong>Status:</strong> ${result.camera_info.status}<br>
                            ${result.camera_info.snapshot_url ?
                                `<img src="${result.camera_info.snapshot_url}" style="max-width: 100%; margin-top: 10px; border-radius: 8px;">` : ''
                            }
                        `;
                    } else {
                        responseArea.innerHTML = `<strong>✅ Success:</strong> ${result.response || JSON.stringify(result, null, 2)}`;
                    }

                    commandCount++;
                    document.getElementById('commandCount').textContent = commandCount;
                } else {
                    responseArea.className = 'response-area response-error';
                    responseArea.innerHTML = `<strong>❌ Error:</strong> ${result.error || 'Unknown error occurred'}`;
                }

            } catch (error) {
                responseArea.className = 'response-area response-error';
                responseArea.innerHTML = `<strong>❌ Connection Error:</strong> ${error.message}`;
            }

            loading.style.display = 'none';
            input.value = '';
        }

        async function loadCameras() {
            try {
                const response = await fetch('http://localhost:5002/list_cameras');
                const data = await response.json();

                const grid = document.getElementById('cameraGrid');
                grid.innerHTML = '';

                let totalCameras = 0;
                let activeCameras = 0;

                if (data.cameras) {
                    for (const [entityId, name] of Object.entries(data.cameras)) {
                        totalCameras++;

                        const card = document.createElement('div');
                        card.className = 'camera-card';

                        // Create camera key for proxy URL
                        const cameraKey = Object.keys(CAMERA_ENTITIES).find(key =>
                            CAMERA_ENTITIES[key] === entityId
                        ) || name.toLowerCase().replace(/\\s+/g, '_');

                        card.innerHTML = `
                            <div class="camera-preview">
                                <img src="/camera_proxy/${cameraKey}"
                                     alt="${name}"
                                     style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;"
                                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                                     onload="this.nextElementSibling.style.display='none';">
                                <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #f8f9fa; border-radius: 8px;">📹</div>
                            </div>
                            <strong>${name}</strong><br>
                            <small>${entityId}</small>
                        `;

                        card.onclick = () => setCommand(`Show me the ${name.toLowerCase()}`);
                        grid.appendChild(card);
                    }
                    activeCameras = totalCameras; // Assume all are active for now
                }

                document.getElementById('totalCameras').textContent = totalCameras;
                document.getElementById('activeCameras').textContent = activeCameras;

            } catch (error) {
                console.error('Failed to load cameras:', error);
            }
        }

        async function checkSystemStatus() {
            // Check Camera Bridge
            try {
                const cameraResponse = await fetch('http://localhost:5002/health');
                const cameraStatus = document.getElementById('cameraStatus');
                if (cameraResponse.ok) {
                    cameraStatus.textContent = '📹 Camera Bridge: Healthy';
                    cameraStatus.className = 'status-item healthy';
                } else {
                    cameraStatus.textContent = '📹 Camera Bridge: Error';
                    cameraStatus.className = 'status-item error';
                }
            } catch {
                document.getElementById('cameraStatus').textContent = '📹 Camera Bridge: Offline';
                document.getElementById('cameraStatus').className = 'status-item error';
            }

            // Check Main Bridge
            try {
                const mainResponse = await fetch('http://localhost:5001/health');
                const mainStatus = document.getElementById('mainStatus');
                if (mainResponse.ok) {
                    mainStatus.textContent = '🤖 AI Bridge: Healthy';
                    mainStatus.className = 'status-item healthy';
                } else {
                    mainStatus.textContent = '🤖 AI Bridge: Error';
                    mainStatus.className = 'status-item error';
                }
            } catch {
                document.getElementById('mainStatus').textContent = '🤖 AI Bridge: Offline';
                document.getElementById('mainStatus').className = 'status-item error';
            }

            // Check connections
            try {
                const testResponse = await fetch('http://localhost:5002/test_connections');
                const testData = await testResponse.json();
                const haStatus = document.getElementById('haStatus');

                if (testData.home_assistant && testData.home_assistant.status === 'connected') {
                    haStatus.textContent = '🏠 Home Assistant: Connected';
                    haStatus.className = 'status-item healthy';
                } else {
                    haStatus.textContent = '🏠 Home Assistant: Error';
                    haStatus.className = 'status-item error';
                }
            } catch {
                document.getElementById('haStatus').textContent = '🏠 Home Assistant: Unknown';
                document.getElementById('haStatus').className = 'status-item error';
            }
        }

        function refreshStatus() {
            checkSystemStatus();
            loadCameras();
        }

        function startVoiceRecognition() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();

                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';

                recognition.onstart = function() {
                    document.querySelector('.btn-voice').textContent = '🎤 Listening...';
                    document.querySelector('.btn-voice').style.background = 'linear-gradient(45deg, #28a745, #20c997)';
                };

                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    document.getElementById('commandInput').value = transcript;
                };

                recognition.onend = function() {
                    document.querySelector('.btn-voice').textContent = '🎤 Voice';
                    document.querySelector('.btn-voice').style.background = 'linear-gradient(45deg, #e74c3c, #c0392b)';
                };

                recognition.onerror = function(event) {
                    alert('Voice recognition error: ' + event.error);
                    recognition.onend();
                };

                recognition.start();
            } else {
                alert('Voice recognition not supported in this browser');
            }
        }
    </script>
</body>
</html>
"""

@app.route('/camera_proxy/<camera_name>')
def camera_proxy(camera_name):
    """Proxy camera snapshots from Home Assistant"""
    try:
        # Get camera entity ID
        entity_id = CAMERA_ENTITIES.get(camera_name)
        if not entity_id:
            return Response("Camera not found", status=404, mimetype='text/plain')

        # Fetch camera snapshot from Home Assistant
        snapshot_url = f"{HA_URL}/api/camera_proxy/{entity_id}"
        response = requests.get(snapshot_url, headers=HA_HEADERS, timeout=10)

        if response.status_code == 200:
            return Response(
                response.content,
                mimetype='image/jpeg',
                headers={
                    'Cache-Control': 'no-cache',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        else:
            return Response("Camera unavailable", status=503, mimetype='text/plain')

    except Exception as e:
        return Response(f"Error: {str(e)}", status=500, mimetype='text/plain')

@app.route('/list_cameras')
def list_cameras():
    """List available cameras for the web UI"""
    try:
        # Get camera list from camera bridge
        response = requests.get(f"{CAMERA_BRIDGE_URL}/list_cameras", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to our local camera mapping
            return jsonify({
                "cameras": {entity: name.replace('camera.', '').replace('_', ' ').title()
                           for name, entity in CAMERA_ENTITIES.items()},
                "camera_entities": CAMERA_ENTITIES
            })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, ha_url=HA_URL)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "smart-home-ui"})

if __name__ == '__main__':
    print("🌐 Smart Home Web UI Starting...")
    print("🏠 Home Assistant:", HA_URL)
    print("📹 Camera Bridge:", CAMERA_BRIDGE_URL)
    print("🤖 Main Bridge:", MAIN_BRIDGE_URL)
    print("")
    print("🚀 Web UI ready on http://localhost:8080")
    print("📱 Open in browser to control your smart home!")

    app.run(host='0.0.0.0', port=8080, debug=False)