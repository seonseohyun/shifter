#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for optimized shift scheduler server
"""

import socket
import json
import time

def test_server():
    """Test the optimized shift scheduler server"""
    
    # Test request data
    test_request = {
        "protocol": "py_gen_timetable",
        "data": {
            "staff_data": {
                "staff": [
                    {
                        "name": "김간호사",
                        "staff_id": 1001,
                        "grade": 3,
                        "total_hours": 195
                    },
                    {
                        "name": "이간호사", 
                        "staff_id": 1002,
                        "grade": 2,
                        "total_hours": 200
                    },
                    {
                        "name": "박간호사",
                        "staff_id": 1003,
                        "grade": 3,  # Changed from 5 to avoid newbie restrictions
                        "total_hours": 180
                    },
                    {
                        "name": "최간호사",
                        "staff_id": 1004,
                        "grade": 1,
                        "total_hours": 210
                    },
                    {
                        "name": "정간호사",
                        "staff_id": 1005,
                        "grade": 2,
                        "total_hours": 190
                    },
                    {
                        "name": "한간호사",
                        "staff_id": 1006,
                        "grade": 3,
                        "total_hours": 200
                    }
                ]
            },
            "position": "간호",
            "target_month": "2025-09",
            "custom_rules": {
                "shifts": ["Day", "Evening", "Night", "Off"],
                "shift_hours": {
                    "Day": 8,
                    "Evening": 8, 
                    "Night": 8,
                    "Off": 0
                },
                "night_shifts": ["Night"],
                "off_shifts": ["Off"]
            }
        }
    }
    
    try:
        print("🔄 Connecting to server...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 6004))
        
        print("📤 Sending request...")
        request_json = json.dumps(test_request, ensure_ascii=False)
        sock.sendall(request_json.encode('utf-8'))
        sock.shutdown(socket.SHUT_WR)
        
        print("📥 Receiving response...")
        response_data = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
        
        sock.close()
        
        # Parse response
        response_text = response_data.decode('utf-8')
        response = json.loads(response_text)
        
        print(f"✅ Response received:")
        print(f"   Protocol: {response.get('protocol')}")
        print(f"   Status: {response.get('resp')}")
        print(f"   Data entries: {len(response.get('data', []))}")
        
        if response.get('resp') == 'success':
            print(f"🎉 Schedule generated successfully!")
            
            # Show first few entries
            data = response.get('data', [])
            if data:
                print(f"\n📅 Sample schedule entries (first 5):")
                for i, entry in enumerate(data[:5]):
                    print(f"   {entry['date']} {entry['shift']}: {len(entry['people'])} people")
            
        else:
            print(f"❌ Schedule generation failed")
            if 'error' in response:
                print(f"   Error: {response['error']}")
            if 'reason' in response:
                print(f"   Reason: {response['reason']}")
    
    except ConnectionRefusedError:
        print("❌ Server not running. Start the server first with:")
        print("   python shift_server_optimized.py")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_server()