#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to validate the binary protocol implementation.

This script simulates both C++ binary protocol and Python legacy protocol 
to ensure the server handles both correctly.
"""

import socket
import json
import struct
import sys
from typing import Dict, Any


def test_binary_protocol(host: str = 'localhost', port: int = 6004) -> bool:
    """Test the binary protocol (C++ client simulation)."""
    print("\n=== Testing Binary Protocol (C++ Client) ===")
    
    try:
        # Create test request
        test_request = {
            "task": "summarize_handover",
            "input_text": "환자 상태 안정. 수액 투여 중. 다음 근무자는 혈압 체크 필요."
        }
        
        # Encode as JSON
        json_str = json.dumps(test_request, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')
        
        # Create binary header (little-endian)
        total_size = len(json_bytes)
        json_size = len(json_bytes)
        header = struct.pack('<I', total_size) + struct.pack('<I', json_size)
        
        print(f"Sending binary request: totalSize={total_size}, jsonSize={json_size}")
        print(f"Request data: {json_str[:100]}...")
        
        # Connect and send
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            
            # Send header + data
            sock.sendall(header + json_bytes)
            
            # Receive response header
            response_header = recv_exact(sock, 8)
            resp_total_size = struct.unpack('<I', response_header[:4])[0]
            resp_json_size = struct.unpack('<I', response_header[4:8])[0]
            
            print(f"Received response header: totalSize={resp_total_size}, jsonSize={resp_json_size}")
            
            # Receive response data
            response_data = recv_exact(sock, resp_total_size)
            response_json = response_data[:resp_json_size].decode('utf-8')
            
            print(f"Response: {response_json}")
            
            # Parse and validate response
            response = json.loads(response_json)
            if response.get('status') == 'success':
                print("✅ Binary protocol test PASSED")
                return True
            else:
                print(f"❌ Binary protocol test FAILED: {response}")
                return False
                
    except Exception as e:
        print(f"❌ Binary protocol test ERROR: {e}")
        return False


def test_legacy_protocol(host: str = 'localhost', port: int = 6004) -> bool:
    """Test the legacy protocol (Python client simulation)."""
    print("\n=== Testing Legacy Protocol (Python Client) ===")
    
    try:
        # Create test request
        test_request = {
            "staff_data": {
                "staff": [
                    {"name": "김간호사", "staff_id": 1, "grade": 3, "total_hours": 160},
                    {"name": "이간호사", "staff_id": 2, "grade": 4, "total_hours": 180}
                ]
            },
            "position": "간호",
            "target_month": "2025-01"
        }
        
        # Encode as JSON (no headers)
        json_str = json.dumps(test_request, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')
        
        print(f"Sending legacy request (no headers): {len(json_bytes)} bytes")
        print(f"Request data: {json_str[:100]}...")
        
        # Connect and send
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            
            # Send raw JSON (no headers)
            sock.sendall(json_bytes)
            sock.shutdown(socket.SHUT_WR)  # Signal end of data
            
            # Receive response (no headers expected)
            response_data = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            response_json = response_data.decode('utf-8')
            print(f"Response: {response_json[:200]}...")
            
            # Parse and validate response
            response = json.loads(response_json)
            if response.get('resp') == 'success':
                print("✅ Legacy protocol test PASSED")
                return True
            else:
                print(f"❌ Legacy protocol test FAILED: {response}")
                return False
                
    except Exception as e:
        print(f"❌ Legacy protocol test ERROR: {e}")
        return False


def recv_exact(sock: socket.socket, n: int) -> bytes:
    """Receive exactly n bytes from socket."""
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket connection closed")
        buf += chunk
    return buf


def main():
    """Run all protocol tests."""
    print("Protocol Fix Validation Test")
    print("=" * 40)
    
    host = 'localhost'
    port = 6004
    
    # Test if server is running
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
            test_sock.settimeout(3.0)
            test_sock.connect((host, port))
        print(f"✅ Server is running on {host}:{port}")
    except Exception as e:
        print(f"❌ Server not accessible on {host}:{port}: {e}")
        print("Please start the server with: python shift_server_optimized.py")
        return False
    
    # Run tests
    results = []
    results.append(test_binary_protocol(host, port))
    results.append(test_legacy_protocol(host, port))
    
    # Summary
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    
    if all(results):
        print("✅ ALL TESTS PASSED - Protocol fix is working correctly!")
        print("✅ C++ clients should now work properly with the server")
        return True
    else:
        print("❌ Some tests failed - Protocol fix needs debugging")
        print("❌ Check server logs for more details")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)