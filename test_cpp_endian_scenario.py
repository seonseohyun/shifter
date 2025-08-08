#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C++ Endian Scenario Reproduction Test
Reproduces the exact endian mismatch scenario seen in C++ client logs
"""

import socket
import json
import struct
import time
from typing import Dict, Any, Optional

def create_big_endian_packet(request_data: Dict[str, Any]) -> bytes:
    """Create packet using big-endian format (like problematic C++ client)"""
    json_str = json.dumps(request_data, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    total_size = len(json_bytes)
    json_size = len(json_bytes)
    
    # Big-endian header (problematic format)
    header = struct.pack('>I', total_size) + struct.pack('>I', json_size)
    
    return header + json_bytes

def simulate_cpp_client_endian_mismatch():
    """Simulate the exact endian mismatch scenario from C++ client"""
    print("="*70)
    print("SIMULATING C++ CLIENT ENDIAN MISMATCH SCENARIO")
    print("="*70)
    
    # Test request that would cause the exact error seen
    request_data = {
        "task": "summarize_handover",
        "input_text": "긴급상황: C 환자 상태변화 관찰 필요, D 환자 검사결과 확인요망"
    }
    
    print(f"Request: {json.dumps(request_data, ensure_ascii=False)}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 6004))
        
        # Create packet using big-endian (problematic C++ client behavior)
        packet = create_big_endian_packet(request_data)
        
        print(f"Packet size: {len(packet)} bytes")
        print(f"Packet header (hex): {packet[:8].hex()}")
        
        # Parse what server would see when interpreting as little-endian
        wrong_total = struct.unpack('<I', packet[:4])[0]
        wrong_json = struct.unpack('<I', packet[4:8])[0]
        print(f"Server would interpret as: totalSize={wrong_total}, jsonSize={wrong_json}")
        print(f"This matches the error: jsonSize={wrong_total}, totalSize={wrong_json}")
        
        # Send the problematic packet
        sock.sendall(packet)
        
        # Try to receive response
        try:
            response = b''
            sock.settimeout(5.0)  # 5 second timeout
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                # Try to parse as JSON to see if we have complete response
                try:
                    response_str = response.decode('utf-8')
                    json.loads(response_str)
                    break  # Complete JSON received
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
        except socket.timeout:
            print("⚠️ Response timeout - server may have detected endian mismatch")
            
        sock.close()
        
        if response:
            try:
                response_str = response.decode('utf-8')
                response_dict = json.loads(response_str)
                print(f"Server response: {json.dumps(response_dict, ensure_ascii=False, indent=2)}")
                
                if response_dict.get('error_type') == 'endian_mismatch':
                    print("✅ Server correctly detected endian mismatch!")
                    return True
                else:
                    print("⚠️ Server processed request but didn't detect endian issue")
                    return False
            except Exception as e:
                print(f"❌ Failed to parse server response: {e}")
                print(f"Raw response: {response}")
                return False
        else:
            print("❌ No response received from server")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_correct_little_endian():
    """Test with correct little-endian format for comparison"""
    print("\n" + "="*70)
    print("TESTING CORRECT LITTLE-ENDIAN FORMAT")
    print("="*70)
    
    request_data = {
        "task": "summarize_handover", 
        "input_text": "정상요청: E 환자 퇴원준비, F 환자 약물조정"
    }
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 6004))
        
        # Correct little-endian format
        json_str = json.dumps(request_data, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')
        total_size = len(json_bytes)
        json_size = len(json_bytes)
        
        # Little-endian header (correct format)
        header = struct.pack('<I', total_size) + struct.pack('<I', json_size)
        
        sock.sendall(header + json_bytes)
        
        # Receive binary response
        response_header = recv_exact(sock, 8)
        response_total = struct.unpack('<I', response_header[:4])[0]
        response_json = struct.unpack('<I', response_header[4:8])[0]
        
        response_data = recv_exact(sock, response_total)
        response_str = response_data[:response_json].decode('utf-8')
        
        response_dict = json.loads(response_str)
        print(f"✅ Correct format response: {response_dict.get('status')}")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"❌ Correct format test failed: {e}")
        return False

def recv_exact(sock: socket.socket, n: int) -> bytes:
    """Receive exactly n bytes from socket"""
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket connection closed unexpectedly")
        buf += chunk
    return buf

def analyze_endian_mismatch_values():
    """Analyze the specific values that would cause the reported error"""
    print("\n" + "="*70)
    print("ANALYZING ENDIAN MISMATCH ERROR VALUES")
    print("="*70)
    
    # The error shows: jsonSize=3825401856, totalSize=3825401856
    error_value = 3825401856
    
    print(f"Error value: {error_value}")
    print(f"Error value (hex): 0x{error_value:08x}")
    
    # Convert back to what the original little-endian value might have been
    try:
        # Pack as big-endian, then unpack as little-endian (reverse the mismatch)
        original_bytes = struct.pack('>I', error_value)
        original_value = struct.unpack('<I', original_bytes)[0]
        
        print(f"Original value (before mismatch): {original_value}")
        print(f"Original value (hex): 0x{original_value:08x}")
        
        # This represents a reasonable JSON size if interpreted correctly
        if original_value < 10000:
            print(f"✅ Original value {original_value} is reasonable for JSON size")
        else:
            print(f"⚠️ Original value {original_value} seems too large")
            
    except struct.error as e:
        print(f"❌ Could not reverse engineer original value: {e}")
        
    # Let's also check what a 150-byte JSON would look like with endian mismatch
    test_size = 150
    big_endian_bytes = struct.pack('>I', test_size)
    misinterpreted_value = struct.unpack('<I', big_endian_bytes)[0]
    
    print(f"\nExample: {test_size} bytes in big-endian interpreted as little-endian = {misinterpreted_value}")

def main():
    """Run comprehensive endian mismatch scenario tests"""
    print("C++ CLIENT ENDIAN MISMATCH SCENARIO TEST")
    print("="*70)
    
    # Analyze the error values first
    analyze_endian_mismatch_values()
    
    # Test the endian mismatch scenario
    mismatch_detected = simulate_cpp_client_endian_mismatch()
    
    # Test correct format for comparison
    correct_works = test_correct_little_endian()
    
    print("\n" + "="*70)
    print("FINAL ANALYSIS")
    print("="*70)
    
    if mismatch_detected:
        print("✅ Server correctly detects and handles endian mismatch")
    else:
        print("❌ Server does not properly handle endian mismatch")
        
    if correct_works:
        print("✅ Server works correctly with proper little-endian format")
    else:
        print("❌ Server has issues even with correct format")
        
    if mismatch_detected and correct_works:
        print("\n🎯 CONCLUSION: Server endian handling is working correctly")
        print("🔧 C++ client needs to be fixed to use little-endian format")
    else:
        print("\n🚨 CONCLUSION: Server needs endian handling improvements")

if __name__ == "__main__":
    main()