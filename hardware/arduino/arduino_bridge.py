"""
Arduino-to-Cloud Bridge
Lightweight script that forwards Arduino card scans to PythonAnywhere server
No local Flask server needed - just reads serial and POSTs to cloud
"""

import serial
import serial.tools.list_ports
import requests
import time
from dotenv import load_dotenv
import os

load_dotenv()

# PythonAnywhere server URL
SERVER_URL = "https://bankoseton.pythonanywhere.com"
API_KEY = os.getenv('ARDUINO_API_KEY', 'your-secret-api-key')  # Add this to your .env

def find_arduino():
    """Auto-detect Arduino port"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'Arduino' in port.description or 'CH340' in port.description or 'USB Serial' in port.description:
            return port.device
    return None

def send_card_to_server(card_uid, action='scan'):
    """Send card data to PythonAnywhere server"""
    try:
        response = requests.post(
            f"{SERVER_URL}/api/arduino/card",
            json={
                'card_uid': card_uid,
                'action': action,
                'api_key': API_KEY
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server response: {data.get('message', 'Success')}")
            return data
        else:
            print(f"❌ Server error: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None

def main():
    print("=" * 60)
    print("🌉 Arduino-to-Cloud Bridge")
    print("=" * 60)
    print(f"Server: {SERVER_URL}")
    print("Searching for Arduino...")
    
    # Find Arduino
    arduino_port = find_arduino()
    if not arduino_port:
        print("❌ Arduino not found!")
        print("Available ports:")
        for port in serial.tools.list_ports.comports():
            print(f"  - {port.device}: {port.description}")
        return
    
    print(f"✅ Found Arduino on {arduino_port}")
    
    # Connect to Arduino
    try:
        arduino = serial.Serial(arduino_port, 9600, timeout=1)
        time.sleep(2)  # Wait for Arduino to initialize
        print("✅ Connected to Arduino")
        print("=" * 60)
        print("Waiting for card scans... (Press Ctrl+C to exit)")
        print("=" * 60)
        
        while True:
            if arduino.in_waiting > 0:
                line = arduino.readline().decode('utf-8').strip()
                
                if line:
                    print(f"📡 Arduino: {line}")
                    
                    # Parse Arduino output
                    if line.startswith("UID:"):
                        card_uid = line.replace("UID:", "").strip()
                        print(f"💳 Card detected: {card_uid}")
                        print(f"📤 Sending to server...")
                        
                        result = send_card_to_server(card_uid)
                        
                        if result:
                            # Send feedback back to Arduino (optional)
                            arduino.write(b'OK\n')
                        else:
                            arduino.write(b'ERROR\n')
                        
                        print("-" * 60)
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n👋 Bridge stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'arduino' in locals():
            arduino.close()
            print("✅ Arduino disconnected")

if __name__ == '__main__':
    main()
