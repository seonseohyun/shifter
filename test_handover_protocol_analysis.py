#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Handover Protocol Analysis Test
Tests the current handover response handling to identify endian and protocol issues
"""

import socket
import json
import struct
import time
import sys
from typing import Dict, Any, Optional

def test_handover_binary_protocol():
    """Test handover using binary protocol (C++ style)"""
    print("\n" + "="*60)
    print("HANDOVER BINARY PROTOCOL TEST (C++ Style)")
    print("="*60)
    
    # Create test request
    request_data = {
        "task": "summarize_handover",
        "input_text": "테스트 인수인계 내용: A 환자 수술 예정, B 환자 약물 변경"
    }
    
    json_str = json.dumps(request_data, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    total_size = len(json_bytes)
    json_size = len(json_bytes)
    
    print(f"Request JSON: {json_str}")
    print(f"JSON bytes length: {len(json_bytes)}")
    print(f"Total size: {total_size}, JSON size: {json_size}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 6004))
        
        # Send binary protocol header (little-endian)
        header = struct.pack('<I', total_size) + struct.pack('<I', json_size)
        print(f"Header bytes (little-endian): {header.hex()}")
        
        # Send header + data
        sock.sendall(header + json_bytes)
        
        # Receive response using binary protocol
        print("\nReceiving binary response...")
        
        # Read 8-byte header
        response_header = recv_exact(sock, 8)
        response_total_size = struct.unpack('<I', response_header[:4])[0]
        response_json_size = struct.unpack('<I', response_header[4:8])[0]
        
        print(f"Response header - Total size: {response_total_size}, JSON size: {response_json_size}")
        
        # Read response data
        response_data = recv_exact(sock, response_total_size)
        response_json = response_data[:response_json_size].decode('utf-8')
        
        print(f"Response JSON: {response_json}")
        
        # Parse response
        response_dict = json.loads(response_json)
        print(f"Parsed response: {json.dumps(response_dict, ensure_ascii=False, indent=2)}")
        
        sock.close()
        
        return True, response_dict
        
    except Exception as e:
        print(f"Binary protocol test failed: {e}")
        return False, None

def test_handover_legacy_protocol():
    """Test handover using legacy protocol (Python style)"""
    print("\n" + "="*60)
    print("HANDOVER LEGACY PROTOCOL TEST (Python Style)")
    print("="*60)
    
    request_data = {
        "task": "summarize_handover",
        "input_text": "테스트 인수인계 내용: A 환자 수술 예정, B 환자 약물 변경"
    }
    
    json_str = json.dumps(request_data, ensure_ascii=False)
    print(f"Request JSON: {json_str}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 6004))
        
        # Send raw JSON (no headers)
        sock.sendall(json_str.encode('utf-8'))
        sock.shutdown(socket.SHUT_WR)
        
        # Receive response
        response_data = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
        
        sock.close()
        
        response_str = response_data.decode('utf-8')
        print(f"Response: {response_str}")
        
        # Parse response
        response_dict = json.loads(response_str)
        print(f"Parsed response: {json.dumps(response_dict, ensure_ascii=False, indent=2)}")
        
        return True, response_dict
        
    except Exception as e:
        print(f"Legacy protocol test failed: {e}")
        return False, None

def recv_exact(sock: socket.socket, n: int) -> bytes:
    """Receive exactly n bytes from socket"""
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket connection closed unexpectedly")
        buf += chunk
    return buf

def test_endian_analysis():
    """Analyze endian format differences"""
    print("\n" + "="*60)
    print("ENDIAN FORMAT ANALYSIS")
    print("="*60)
    
    test_value = 0x12345678
    
    # Big-endian (network byte order)
    big_endian = struct.pack('>I', test_value)
    print(f"Big-endian ('>I') format: {big_endian.hex()}")
    
    # Little-endian (x86 native)
    little_endian = struct.pack('<I', test_value)
    print(f"Little-endian ('<I') format: {little_endian.hex()}")
    
    # Test with actual message sizes
    total_size = 150
    json_size = 150
    
    print(f"\nTest sizes - Total: {total_size}, JSON: {json_size}")
    
    # Big-endian format
    big_header = struct.pack('>I', total_size) + struct.pack('>I', json_size)
    print(f"Big-endian header: {big_header.hex()}")
    
    # Little-endian format
    little_header = struct.pack('<I', total_size) + struct.pack('<I', json_size)
    print(f"Little-endian header: {little_header.hex()}")
    
    # Show what happens if server expects little-endian but gets big-endian
    wrong_total = struct.unpack('<I', struct.pack('>I', total_size))[0]
    wrong_json = struct.unpack('<I', struct.pack('>I', json_size))[0]
    print(f"Big-endian interpreted as little-endian - Total: {wrong_total}, JSON: {wrong_json}")
    
def test_protocol_detection():
    """Test protocol detection mechanism"""
    print("\n" + "="*60)
    print("PROTOCOL DETECTION TEST")
    print("="*60)
    
    # Test with valid binary header
    total_size = 100
    json_size = 100
    
    # Create headers in both formats
    little_header = struct.pack('<I', total_size) + struct.pack('<I', json_size)
    big_header = struct.pack('>I', total_size) + struct.pack('>I', json_size)
    
    print("Testing protocol detection logic:")
    
    # Simulate protocol detection for little-endian
    detected_total = struct.unpack('<I', little_header[:4])[0]
    detected_json = struct.unpack('<I', little_header[4:8])[0]
    print(f"Little-endian header: Total={detected_total}, JSON={detected_json}")
    
    # Check if it would be detected as valid binary protocol
    is_valid = (detected_json > 0 and 
                detected_json <= detected_total and 
                detected_total <= 10*1024*1024 and 
                detected_total < 1000000)
    print(f"Would be detected as binary protocol: {is_valid}")
    
    # Simulate protocol detection for big-endian header interpreted as little-endian
    detected_total = struct.unpack('<I', big_header[:4])[0]
    detected_json = struct.unpack('<I', big_header[4:8])[0]
    print(f"Big-endian as little-endian: Total={detected_total}, JSON={detected_json}")
    
    # Check if it would be detected as valid binary protocol
    is_valid = (detected_json > 0 and 
                detected_json <= detected_total and 
                detected_total <= 10*1024*1024 and 
                detected_total < 1000000)
    print(f"Would be detected as binary protocol: {is_valid}")

def main():
    """Run all handover protocol tests"""
    print("HANDOVER PROTOCOL ANALYSIS")
    print("="*60)
    
    # Run endian analysis first
    test_endian_analysis()
    test_protocol_detection()
    
    # Test both protocols
    binary_success, binary_response = test_handover_binary_protocol()
    legacy_success, legacy_response = test_handover_legacy_protocol()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Binary protocol test: {'✅ PASS' if binary_success else '❌ FAIL'}")
    print(f"Legacy protocol test: {'✅ PASS' if legacy_success else '❌ FAIL'}")
    
    if binary_success and legacy_success:
        print("\n✅ Both protocols working correctly")
        
        # Compare responses
        if binary_response and legacy_response:
            binary_status = binary_response.get('status')
            legacy_status = legacy_response.get('status')
            
            if binary_status == legacy_status == 'success':
                print("✅ Both protocols returned successful handover summaries")
            else:
                print(f"⚠️ Status mismatch - Binary: {binary_status}, Legacy: {legacy_status}")
    else:
        print("\n❌ Protocol issues detected")
        
        if not binary_success:
            print("🔧 Binary protocol needs fixing")
        if not legacy_success:
            print("🔧 Legacy protocol needs fixing")

if __name__ == "__main__":
    main()