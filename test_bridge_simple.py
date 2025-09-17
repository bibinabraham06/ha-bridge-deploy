#!/usr/bin/env python3
"""
Simple bridge test to debug the issue
"""

import requests
import json
import os

# Set environment variables
os.environ['HA_URL'] = 'http://192.168.0.81:8123'
os.environ['HA_TOKEN'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIwMjM1N2RjZDBhMTY0NjJmYTBkNTlhMzczMjc2Y2ZhYSIsImlhdCI6MTc1ODA0NjE3MywiZXhwIjoyMDczNDA2MTczfQ.7tYGiaSHeTFsZTZusbSuRiDp_jFJEUyIKbOf3nc4UOw'
os.environ['OLLAMA_URL'] = 'http://100.94.114.43:11434'

def test_voice_command_simple():
    """Test voice command processing"""

    # Test data
    command = "Turn on the kitchen lights"

    print(f"🗣️  Testing command: {command}")

    try:
        # Create AI prompt
        prompt = f"""
        You are a smart home assistant. Convert this voice command to Home Assistant API calls.

        Voice Command: "{command}"

        Respond with ONLY a JSON object in this exact format:
        {{
            "actions": [
                {{
                    "domain": "light",
                    "service": "turn_on",
                    "entity_id": "light.kitchen_lights_light_1",
                    "service_data": {{"brightness": 255}}
                }}
            ],
            "response": "I've turned on the kitchen lights to full brightness"
        }}

        Common domains: light, switch, climate, media_player, automation, script
        Common services: turn_on, turn_off, toggle, set_temperature
        Always include a friendly response message.
        """

        print("🤖 Sending to AI...")

        # Ask AI what to do
        ai_response = requests.post(f"{os.environ['OLLAMA_URL']}/api/generate",
                                   json={
                                       "model": "dolphin-llama3:latest",
                                       "prompt": prompt,
                                       "stream": False
                                   }, timeout=30)

        if ai_response.status_code == 200:
            ai_result = ai_response.json().get('response', '')
            print(f"✅ AI responded: {ai_result[:100]}...")

            try:
                # Parse AI response
                action_plan = json.loads(ai_result)
                print(f"✅ Valid JSON received")

                # Test the first action
                if action_plan.get('actions'):
                    action = action_plan['actions'][0]
                    print(f"🎯 Testing action: {action}")

                    # Test HA API call
                    domain = action.get('domain')
                    service = action.get('service')
                    entity_id = action.get('entity_id')
                    service_data = action.get('service_data', {})

                    if entity_id:
                        service_data['entity_id'] = entity_id

                    ha_url = f"{os.environ['HA_URL']}/api/services/{domain}/{service}"
                    headers = {
                        'Authorization': f"Bearer {os.environ['HA_TOKEN']}",
                        'Content-Type': 'application/json'
                    }

                    print(f"🏠 Calling HA API: {ha_url}")
                    print(f"📦 Data: {service_data}")

                    ha_response = requests.post(ha_url, headers=headers, json=service_data, timeout=10)

                    print(f"📊 HA Response: {ha_response.status_code}")
                    if ha_response.status_code == 200:
                        print("✅ SUCCESS! Kitchen lights should be on!")
                    else:
                        print(f"❌ HA API Error: {ha_response.text}")

            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error: {e}")
                print(f"Raw AI response: {ai_result}")

        else:
            print(f"❌ AI Error: {ai_response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🏠🤖 DIRECT BRIDGE TEST")
    print("=" * 30)
    test_voice_command_simple()