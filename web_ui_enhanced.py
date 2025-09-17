#!/usr/bin/env python3
"""
Enhanced Smart Home Voice Command Web UI
Advanced web interface with real-time updates, device control, and analytics
"""

from flask import Flask, render_template_string, request, jsonify, Response
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime
import time

app = Flask(__name__)
CORS(app)

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

# In-memory storage for demo (replace with Redis/DB in production)
command_history = []
device_states = {}

# Enhanced HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏠 Enhanced Smart Home Control Center</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --warning-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            --dark-bg: #1a1a2e;
            --card-bg: rgba(255, 255, 255, 0.95);
            --glass-bg: rgba(255, 255, 255, 0.1);
            --text-primary: #333;
            --text-secondary: #666;
            --border-radius: 15px;
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            --glass-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--primary-gradient);
            min-height: 100vh;
            color: var(--text-primary);
            overflow-x: hidden;
        }

        /* Animated Background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 0.1;
        }

        .bg-animation::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="white"/><circle cx="80" cy="80" r="2" fill="white"/><circle cx="40" cy="60" r="1" fill="white"/></svg>');
            animation: float 20s infinite linear;
        }

        @keyframes float {
            0% { transform: translateY(0) rotate(0deg); }
            100% { transform: translateY(-100vh) rotate(360deg); }
        }

        /* Glass morphism containers */
        .glass-container {
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: var(--border-radius);
            box-shadow: var(--glass-shadow);
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }

        .header h1 {
            font-size: 3rem;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }

        /* Enhanced Status Bar */
        .status-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }

        .status-item {
            padding: 15px 20px;
            border-radius: var(--border-radius);
            text-align: center;
            font-weight: 600;
            color: white;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .status-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }

        .status-item:hover::before {
            left: 100%;
        }

        .status-item.healthy { background: var(--success-gradient); }
        .status-item.error { background: var(--warning-gradient); }
        .status-item.loading { background: var(--secondary-gradient); }

        /* Main layout with sidebar */
        .main-layout {
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 25px;
            height: calc(100vh - 200px);
        }

        @media (max-width: 1200px) {
            .main-layout {
                grid-template-columns: 1fr;
                height: auto;
            }
        }

        /* Sidebar */
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-height: 100%;
            overflow-y: auto;
        }

        /* Enhanced Cards */
        .card {
            background: var(--card-bg);
            border-radius: var(--border-radius);
            padding: 25px;
            box-shadow: var(--shadow);
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
        }

        .card h2 {
            margin-bottom: 20px;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Voice Command Panel */
        .voice-panel {
            position: relative;
        }

        .voice-input {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        .voice-input input {
            flex: 1;
            padding: 15px;
            border: 2px solid #e1e8ed;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s ease;
        }

        .voice-input input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .btn {
            padding: 15px 25px;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }

        .btn-primary { background: var(--primary-gradient); color: white; }
        .btn-voice { background: var(--secondary-gradient); color: white; }
        .btn-success { background: var(--success-gradient); color: white; }
        .btn-warning { background: var(--warning-gradient); color: white; }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }

        .btn:active {
            transform: translateY(0);
        }

        /* Recording indicator */
        .recording {
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        /* Enhanced Camera Grid */
        .camera-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }

        .camera-card {
            background: var(--card-bg);
            border-radius: var(--border-radius);
            padding: 15px;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }

        .camera-card:hover {
            transform: scale(1.02);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        }

        .camera-preview {
            width: 100%;
            height: 180px;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 10px;
            position: relative;
            background: #f8f9fa;
        }

        .camera-preview img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .camera-status {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #28a745;
            box-shadow: 0 0 0 2px white;
        }

        .camera-status.offline {
            background: #dc3545;
        }

        /* Device Control Panel */
        .device-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
        }

        .device-card {
            background: var(--glass-bg);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .device-card:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-3px);
        }

        .device-card.active {
            background: var(--success-gradient);
            color: white;
        }

        .device-icon {
            font-size: 2rem;
            margin-bottom: 10px;
            opacity: 0.8;
        }

        /* Command History */
        .command-history {
            max-height: 300px;
            overflow-y: auto;
        }

        .command-item {
            display: flex;
            justify-content: between;
            align-items: center;
            padding: 10px 15px;
            margin-bottom: 8px;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }

        .command-text {
            flex: 1;
            font-weight: 500;
        }

        .command-time {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        /* Analytics Dashboard */
        .analytics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }

        .metric-card {
            background: var(--glass-bg);
            padding: 20px;
            border-radius: var(--border-radius);
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .metric-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-top: 5px;
        }

        /* Notifications */
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 10px;
            color: white;
            font-weight: 600;
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        }

        .notification.show {
            transform: translateX(0);
        }

        .notification.success { background: var(--success-gradient); }
        .notification.error { background: var(--warning-gradient); }

        /* Loading States */
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .container { padding: 15px; }
            .header h1 { font-size: 2rem; }
            .main-layout { grid-template-columns: 1fr; }
            .camera-grid { grid-template-columns: 1fr; }
            .voice-input { flex-direction: column; }
        }

        /* Dark mode toggle */
        .theme-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.5);
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>

    <div class="theme-toggle">
        <button class="btn btn-primary" onclick="toggleTheme()">
            <i class="fas fa-moon" id="themeIcon"></i>
        </button>
    </div>

    <div class="container">
        <div class="header">
            <h1>🏠 Enhanced Smart Home Control Center</h1>
            <p>Advanced voice control, real-time monitoring, and intelligent automation</p>
        </div>

        <div class="status-bar" id="statusBar">
            <div class="status-item loading" id="cameraStatus">
                <i class="fas fa-video"></i> Camera Bridge: <span class="loading-spinner"></span>
            </div>
            <div class="status-item loading" id="mainStatus">
                <i class="fas fa-robot"></i> AI Bridge: <span class="loading-spinner"></span>
            </div>
            <div class="status-item loading" id="haStatus">
                <i class="fas fa-home"></i> Home Assistant: <span class="loading-spinner"></span>
            </div>
            <div class="status-item loading" id="systemStatus">
                <i class="fas fa-microchip"></i> System: <span class="loading-spinner"></span>
            </div>
        </div>

        <div class="main-layout">
            <!-- Sidebar -->
            <div class="sidebar">
                <!-- Voice Command Panel -->
                <div class="card voice-panel">
                    <h2><i class="fas fa-microphone"></i> Voice Commands</h2>
                    <div class="voice-input">
                        <input type="text" id="commandInput" placeholder="Say something like 'Show me the front door'...">
                        <button class="btn btn-voice" onclick="startVoiceRecognition()" id="voiceBtn">
                            <i class="fas fa-microphone"></i> Voice
                        </button>
                        <button class="btn btn-primary" onclick="sendCommand()">
                            <i class="fas fa-paper-plane"></i> Send
                        </button>
                    </div>

                    <div class="response-area glass-container" id="responseArea" style="padding: 15px; margin-bottom: 20px; min-height: 60px;">
                        Ready for voice commands! Try asking to see a camera or control smart home devices.
                    </div>

                    <div class="analytics-grid">
                        <div class="metric-card">
                            <div class="metric-value" id="commandCount">0</div>
                            <div class="metric-label">Commands Today</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="responseTime">0ms</div>
                            <div class="metric-label">Avg Response</div>
                        </div>
                    </div>
                </div>

                <!-- Quick Device Control -->
                <div class="card">
                    <h2><i class="fas fa-sliders-h"></i> Quick Controls</h2>
                    <div class="device-grid" id="deviceGrid">
                        <!-- Devices loaded dynamically -->
                    </div>
                </div>

                <!-- Command History -->
                <div class="card">
                    <h2><i class="fas fa-history"></i> Recent Commands</h2>
                    <div class="command-history" id="commandHistory">
                        <div style="text-align: center; color: #666; padding: 20px;">
                            No commands yet
                        </div>
                    </div>
                </div>
            </div>

            <!-- Main Content -->
            <div class="main-content">
                <!-- Camera Dashboard -->
                <div class="card">
                    <h2><i class="fas fa-video"></i> Live Camera Feed</h2>
                    <div class="camera-grid" id="cameraGrid">
                        <!-- Cameras loaded dynamically -->
                    </div>

                    <div class="analytics-grid">
                        <div class="metric-card">
                            <div class="metric-value" id="totalCameras">0</div>
                            <div class="metric-label">Total Cameras</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="activeCameras">0</div>
                            <div class="metric-label">Online Cameras</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="cameraUptime">99.9%</div>
                            <div class="metric-label">Uptime</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="lastUpdate">--</div>
                            <div class="metric-label">Last Update</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Notification Container -->
    <div id="notification" class="notification"></div>

    <script>
        // Enhanced JavaScript with real-time features
        let commandCount = 0;
        let responseTimes = [];
        let recognition = null;
        let isRecording = false;

        // Camera entity mappings from server
        const CAMERA_ENTITIES = {
            'front_door': 'camera.doorbell_main_entrance_camera_high_resolution_channel',
            'garage': 'camera.garage_camera_high_resolution_channel',
            'driveway': 'camera.front_lt_driveway_camera_high_resolution_channel',
            'backyard': 'camera.back_rt_facing_patio_camera_high_resolution_channel',
            'back_road': 'camera.back_lt_facing_road_camera_high_resolution_channel'
        };

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            initializeApp();
            setInterval(refreshData, 30000); // Refresh every 30 seconds
            setInterval(updateCameraSnapshots, 10000); // Update camera snapshots every 10 seconds
        });

        function initializeApp() {
            checkSystemStatus();
            loadCameras();
            loadDevices();
            loadCommandHistory();
            updateAnalytics();
        }

        function refreshData() {
            checkSystemStatus();
            updateCameraSnapshots();
            updateAnalytics();
        }

        // Enhanced system status check
        async function checkSystemStatus() {
            const statuses = {
                camera: { element: 'cameraStatus', url: 'http://localhost:5002/health', name: 'Camera Bridge' },
                main: { element: 'mainStatus', url: 'http://localhost:5001/health', name: 'AI Bridge' },
                ha: { element: 'haStatus', url: 'http://localhost:5002/test_connections', name: 'Home Assistant' }
            };

            for (const [key, config] of Object.entries(statuses)) {
                const element = document.getElementById(config.element);
                try {
                    const response = await fetch(config.url);
                    if (response.ok) {
                        element.className = 'status-item healthy';
                        element.innerHTML = `<i class="fas fa-${key === 'camera' ? 'video' : key === 'main' ? 'robot' : 'home'}"></i> ${config.name}: Online`;
                    } else {
                        throw new Error('Service unavailable');
                    }
                } catch (error) {
                    element.className = 'status-item error';
                    element.innerHTML = `<i class="fas fa-${key === 'camera' ? 'video' : key === 'main' ? 'robot' : 'home'}"></i> ${config.name}: Offline`;
                }
            }

            // System status
            const systemElement = document.getElementById('systemStatus');
            systemElement.className = 'status-item healthy';
            systemElement.innerHTML = `<i class="fas fa-microchip"></i> System: Online (${new Date().toLocaleTimeString()})`;
        }

        // Enhanced camera loading with live updates
        async function loadCameras() {
            try {
                const response = await fetch('/list_cameras');
                const data = await response.json();

                const grid = document.getElementById('cameraGrid');
                grid.innerHTML = '';

                let totalCameras = 0;
                let activeCameras = 0;

                if (data.cameras) {
                    for (const [entityId, name] of Object.entries(data.cameras)) {
                        totalCameras++;

                        const cameraKey = Object.keys(CAMERA_ENTITIES).find(key =>
                            CAMERA_ENTITIES[key] === entityId
                        ) || name.toLowerCase().replace(/\\s+/g, '_');

                        const card = document.createElement('div');
                        card.className = 'camera-card';
                        card.innerHTML = `
                            <div class="camera-preview">
                                <img src="/camera_proxy/${cameraKey}?t=${Date.now()}"
                                     alt="${name}"
                                     onload="this.nextElementSibling.style.display='none'; markCameraOnline('${cameraKey}');"
                                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'; markCameraOffline('${cameraKey}');">
                                <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #f8f9fa; flex-direction: column; gap: 10px;">
                                    <i class="fas fa-video-slash" style="font-size: 2rem; opacity: 0.5;"></i>
                                    <span style="opacity: 0.7;">Camera Offline</span>
                                </div>
                                <div class="camera-status" id="status-${cameraKey}"></div>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>${name}</strong><br>
                                    <small style="opacity: 0.7;">${entityId}</small>
                                </div>
                                <button class="btn btn-primary" onclick="viewCamera('${name}')" style="padding: 8px 12px;">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </div>
                        `;

                        card.onclick = () => setCommand(`Show me the ${name.toLowerCase()}`);
                        grid.appendChild(card);
                        activeCameras++; // Will be adjusted by markCameraOffline if needed
                    }
                }

                document.getElementById('totalCameras').textContent = totalCameras;
                document.getElementById('activeCameras').textContent = activeCameras;
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();

            } catch (error) {
                console.error('Failed to load cameras:', error);
                showNotification('Failed to load cameras', 'error');
            }
        }

        function markCameraOnline(cameraKey) {
            const statusElement = document.getElementById(`status-${cameraKey}`);
            if (statusElement) {
                statusElement.className = 'camera-status';
                statusElement.title = 'Camera Online';
            }
        }

        function markCameraOffline(cameraKey) {
            const statusElement = document.getElementById(`status-${cameraKey}`);
            if (statusElement) {
                statusElement.className = 'camera-status offline';
                statusElement.title = 'Camera Offline';
            }
            // Update active camera count
            const currentActive = parseInt(document.getElementById('activeCameras').textContent);
            document.getElementById('activeCameras').textContent = Math.max(0, currentActive - 1);
        }

        function updateCameraSnapshots() {
            const images = document.querySelectorAll('.camera-preview img');
            images.forEach(img => {
                if (img.style.display !== 'none') {
                    const originalSrc = img.src.split('?')[0];
                    img.src = `${originalSrc}?t=${Date.now()}`;
                }
            });
        }

        // Load smart home devices
        async function loadDevices() {
            const deviceGrid = document.getElementById('deviceGrid');

            // Mock devices for demo (replace with real HA API call)
            const devices = [
                { id: 'lights', name: 'Lights', icon: 'lightbulb', state: false },
                { id: 'climate', name: 'AC', icon: 'thermometer-half', state: true },
                { id: 'security', name: 'Security', icon: 'shield-alt', state: true },
                { id: 'music', name: 'Music', icon: 'music', state: false },
                { id: 'garage', name: 'Garage', icon: 'warehouse', state: false },
                { id: 'blinds', name: 'Blinds', icon: 'window-maximize', state: false }
            ];

            deviceGrid.innerHTML = '';
            devices.forEach(device => {
                const deviceCard = document.createElement('div');
                deviceCard.className = `device-card ${device.state ? 'active' : ''}`;
                deviceCard.innerHTML = `
                    <div class="device-icon">
                        <i class="fas fa-${device.icon}"></i>
                    </div>
                    <div>${device.name}</div>
                `;
                deviceCard.onclick = () => toggleDevice(device.id, deviceCard);
                deviceGrid.appendChild(deviceCard);
            });
        }

        function toggleDevice(deviceId, element) {
            element.classList.toggle('active');
            const action = element.classList.contains('active') ? 'on' : 'off';
            setCommand(`Turn ${action} ${deviceId}`);
            showNotification(`${deviceId} turned ${action}`, 'success');
        }

        // Enhanced voice recognition
        function startVoiceRecognition() {
            if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
                showNotification('Voice recognition not supported in this browser', 'error');
                return;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();

            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            const voiceBtn = document.getElementById('voiceBtn');

            recognition.onstart = function() {
                isRecording = true;
                voiceBtn.innerHTML = '<i class="fas fa-stop"></i> Listening...';
                voiceBtn.classList.add('recording');
                voiceBtn.onclick = stopVoiceRecognition;
            };

            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                document.getElementById('commandInput').value = transcript;
                sendCommand();
            };

            recognition.onend = function() {
                stopVoiceRecognition();
            };

            recognition.onerror = function(event) {
                showNotification(`Voice recognition error: ${event.error}`, 'error');
                stopVoiceRecognition();
            };

            recognition.start();
        }

        function stopVoiceRecognition() {
            if (recognition && isRecording) {
                recognition.stop();
            }
            isRecording = false;
            const voiceBtn = document.getElementById('voiceBtn');
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i> Voice';
            voiceBtn.classList.remove('recording');
            voiceBtn.onclick = startVoiceRecognition;
        }

        // Enhanced command sending with analytics
        async function sendCommand() {
            const command = document.getElementById('commandInput').value.trim();
            if (!command) return;

            const startTime = Date.now();

            try {
                const responseArea = document.getElementById('responseArea');
                responseArea.innerHTML = '<div class="loading-spinner"></div> Processing...';

                // Determine if it's a camera command
                const isCameraCommand = ['show', 'display', 'view', 'camera', 'check'].some(keyword =>
                    command.toLowerCase().includes(keyword)
                );

                const url = isCameraCommand ?
                    'http://localhost:5002/voice_command' :
                    'http://localhost:5001/voice_command';

                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command })
                });

                const result = await response.json();
                const endTime = Date.now();
                const responseTime = endTime - startTime;

                // Update analytics
                commandCount++;
                responseTimes.push(responseTime);
                updateAnalytics();

                // Add to history
                addToHistory(command, result.success);

                // Display result
                if (result.success) {
                    responseArea.innerHTML = `
                        <div style="color: #28a745; margin-bottom: 10px;">
                            <i class="fas fa-check-circle"></i> Command executed successfully
                        </div>
                        <div>${result.response || 'Command completed'}</div>
                    `;
                    showNotification('Command executed successfully', 'success');
                } else {
                    responseArea.innerHTML = `
                        <div style="color: #dc3545; margin-bottom: 10px;">
                            <i class="fas fa-exclamation-circle"></i> Command failed
                        </div>
                        <div>${result.error || 'Unknown error'}</div>
                    `;
                    showNotification('Command failed', 'error');
                }

                document.getElementById('commandInput').value = '';

            } catch (error) {
                console.error('Command failed:', error);
                document.getElementById('responseArea').innerHTML = `
                    <div style="color: #dc3545;">
                        <i class="fas fa-exclamation-triangle"></i> Network error: ${error.message}
                    </div>
                `;
                showNotification('Network error', 'error');
            }
        }

        function addToHistory(command, success) {
            const history = document.getElementById('commandHistory');
            const item = document.createElement('div');
            item.className = 'command-item';
            item.innerHTML = `
                <div class="command-text">${command}</div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <i class="fas fa-${success ? 'check' : 'times'}" style="color: ${success ? '#28a745' : '#dc3545'};"></i>
                    <div class="command-time">${new Date().toLocaleTimeString()}</div>
                </div>
            `;

            if (history.firstChild && history.firstChild.style && history.firstChild.style.textAlign) {
                history.innerHTML = '';
            }

            history.insertBefore(item, history.firstChild);

            // Keep only last 10 commands
            while (history.children.length > 10) {
                history.removeChild(history.lastChild);
            }
        }

        function updateAnalytics() {
            document.getElementById('commandCount').textContent = commandCount;

            if (responseTimes.length > 0) {
                const avgTime = Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length);
                document.getElementById('responseTime').textContent = `${avgTime}ms`;
            }
        }

        function loadCommandHistory() {
            // Load from localStorage if available
            const saved = localStorage.getItem('commandHistory');
            if (saved) {
                const history = JSON.parse(saved);
                commandCount = history.length;
                updateAnalytics();
            }
        }

        function setCommand(command) {
            document.getElementById('commandInput').value = command;
        }

        function viewCamera(cameraName) {
            setCommand(`Show me the ${cameraName.toLowerCase()}`);
            sendCommand();
        }

        function showNotification(message, type = 'success') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = `notification ${type} show`;

            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }

        function toggleTheme() {
            // Theme toggle implementation
            document.body.classList.toggle('dark-theme');
            const icon = document.getElementById('themeIcon');
            icon.className = document.body.classList.contains('dark-theme') ? 'fas fa-sun' : 'fas fa-moon';
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'Enter':
                        e.preventDefault();
                        sendCommand();
                        break;
                    case ' ':
                        e.preventDefault();
                        startVoiceRecognition();
                        break;
                }
            }
        });

        // Handle Enter key in command input
        document.getElementById('commandInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendCommand();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/camera_proxy/<camera_name>')
def camera_proxy(camera_name):
    """Proxy camera snapshots from Home Assistant"""
    try:
        entity_id = CAMERA_ENTITIES.get(camera_name)
        if not entity_id:
            return Response("Camera not found", status=404, mimetype='text/plain')

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
        response = requests.get(f"{CAMERA_BRIDGE_URL}/list_cameras", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({
                "cameras": {entity: name.replace('camera.', '').replace('_', ' ').title()
                           for name, entity in CAMERA_ENTITIES.items()},
                "camera_entities": CAMERA_ENTITIES
            })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/command_history')
def get_command_history():
    """Get command history"""
    return jsonify(command_history[-50:])  # Last 50 commands

@app.route('/api/device_states')
def get_device_states():
    """Get current device states from Home Assistant"""
    try:
        response = requests.get(f"{HA_URL}/api/states", headers=HA_HEADERS, timeout=10)
        if response.status_code == 200:
            states = response.json()
            # Filter and format device states
            filtered_states = {}
            for state in states:
                entity_id = state.get('entity_id', '')
                if any(domain in entity_id for domain in ['light.', 'switch.', 'climate.', 'media_player.']):
                    filtered_states[entity_id] = {
                        'state': state.get('state'),
                        'friendly_name': state.get('attributes', {}).get('friendly_name', entity_id),
                        'domain': entity_id.split('.')[0]
                    }
            return jsonify(filtered_states)
        else:
            return jsonify({"error": "Failed to fetch device states"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics')
def get_analytics():
    """Get system analytics"""
    return jsonify({
        "total_commands": len(command_history),
        "uptime": time.time() - startup_time if 'startup_time' in globals() else 0,
        "active_cameras": len(CAMERA_ENTITIES),
        "system_health": "optimal"
    })

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "enhanced-smart-home-ui"})

# Record startup time for analytics
startup_time = time.time()

if __name__ == '__main__':
    print("🚀 Enhanced Smart Home Web UI Starting...")
    print("🏠 Home Assistant:", HA_URL)
    print("📹 Camera Bridge:", CAMERA_BRIDGE_URL)
    print("🤖 Main Bridge:", MAIN_BRIDGE_URL)
    print("")
    print("🌟 Enhanced Web UI ready on http://localhost:8081")
    print("📱 Features: Real-time updates, analytics, device control, and more!")

    app.run(host='0.0.0.0', port=8081, debug=False)