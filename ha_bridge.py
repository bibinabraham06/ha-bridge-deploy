#!/usr/bin/env python3
"""
Simple Home Assistant AI Bridge - Ready to Deploy
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

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "ha-ai-bridge"})

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

@app.route('/voice_command', methods=['POST'])
def voice_command():
    """Process voice commands for smart home"""
    try:
        data = request.json
        command = data.get('command', '')

        if not command:
            return jsonify({"error": "No command provided"}), 400

        # Create AI prompt for smart home control
        prompt = f"""
        You are a smart home assistant. Convert this voice command to Home Assistant API calls.

        Voice Command: "{command}"

        Respond with ONLY a JSON object in this exact format:
        {{
            "actions": [
                {{
                    "domain": "light",
                    "service": "turn_on",
                    "entity_id": "light.living_room",
                    "service_data": {{"brightness": 255}}
                }}
            ],
            "response": "I've turned on the living room lights to full brightness"
        }}

        Common domains: light, switch, climate, media_player, automation, script
        Common services: turn_on, turn_off, toggle, set_temperature
        Always include a friendly response message.
        """

        # Ask AI what to do
        ai_response = requests.post(f"{OLLAMA_URL}/api/generate",
                                   json={
                                       "model": "dolphin-llama3:latest",
                                       "prompt": prompt,
                                       "stream": False
                                   }, timeout=30)

        if ai_response.status_code == 200:
            ai_result = ai_response.json().get('response', '')

            try:
                # Parse AI response
                action_plan = json.loads(ai_result)

                # Execute each action
                execution_results = []
                for action in action_plan.get('actions', []):
                    result = execute_ha_action(action)
                    execution_results.append(result)

                return jsonify({
                    "success": True,
                    "command": command,
                    "ai_interpretation": action_plan,
                    "execution_results": execution_results,
                    "response": action_plan.get('response', 'Command executed')
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

@app.route('/smart_query', methods=['POST'])
def smart_query():
    """Answer questions about home status"""
    try:
        data = request.json
        query = data.get('query', '')

        # Get current home state
        states_response = requests.get(f"{HA_URL}/api/states", headers=HA_HEADERS, timeout=10)

        if states_response.status_code != 200:
            return jsonify({"error": "Could not get home status"}), 500

        states = states_response.json()

        # Create context for AI
        context = create_home_context(states)

        ai_prompt = f"""
        Current Smart Home Status: {json.dumps(context, indent=2)}

        User Question: "{query}"

        Based on the current state of the smart home, provide a helpful answer.
        Be conversational and friendly. Include specific device states when relevant.
        """

        ai_response = requests.post(f"{OLLAMA_URL}/api/generate",
                                   json={
                                       "model": "dolphin-llama3:latest",
                                       "prompt": ai_prompt,
                                       "stream": False
                                   }, timeout=30)

        if ai_response.status_code == 200:
            answer = ai_response.json().get('response', '')
            return jsonify({
                "success": True,
                "query": query,
                "answer": answer,
                "context_used": context
            })
        else:
            return jsonify({"error": "AI service unavailable"}), 500

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

def create_home_context(states):
    """Create a simple context from HA states"""
    context = {
        "lights": {"on": [], "off": []},
        "switches": {"on": [], "off": []},
        "sensors": {},
        "climate": {}
    }

    for state in states[:50]:  # Limit for performance
        entity_id = state.get('entity_id', '')
        entity_state = state.get('state', '')
        attributes = state.get('attributes', {})
        friendly_name = attributes.get('friendly_name', entity_id)

        if entity_id.startswith('light.'):
            if entity_state == 'on':
                context["lights"]["on"].append(friendly_name)
            else:
                context["lights"]["off"].append(friendly_name)

        elif entity_id.startswith('switch.'):
            if entity_state == 'on':
                context["switches"]["on"].append(friendly_name)
            else:
                context["switches"]["off"].append(friendly_name)

        elif entity_id.startswith('sensor.') and 'temperature' in entity_id.lower():
            context["sensors"][friendly_name] = f"{entity_state} {attributes.get('unit_of_measurement', '')}"

        elif entity_id.startswith('climate.'):
            context["climate"][friendly_name] = {
                "current_temp": attributes.get('current_temperature'),
                "target_temp": attributes.get('temperature'),
                "mode": entity_state
            }

    return context

@app.route('/demo_commands', methods=['GET'])
def demo_commands():
    """Get example commands to try"""
    examples = [
        "Turn on the living room lights",
        "Set temperature to 72 degrees",
        "Turn off all lights",
        "What's the temperature in the house?",
        "Is everything secure?",
        "Turn on movie mode",
        "Good night - secure the house"
    ]

    return jsonify({
        "example_commands": examples,
        "usage": {
            "voice_command": "POST /voice_command with {'command': 'your command'}",
            "smart_query": "POST /smart_query with {'query': 'your question'}"
        }
    })

if __name__ == '__main__':
    print("🏠 Home Assistant AI Bridge Starting...")
    print(f"HA URL: {HA_URL}")
    print(f"AI URL: {OLLAMA_URL}")
    print("Bridge ready on port 5001!")

    app.run(host='0.0.0.0', port=5001, debug=False)