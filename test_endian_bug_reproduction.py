#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Endian Bug Reproduction Test
Tries to reproduce the specific error: jsonSize=3825401856, totalSize=3825401856
"""

import socket
import json
import struct
import time

def analyze_error_value():
    """Analyze the specific error value to understand the endian issue"""
    print("="*60)
    print("ERROR VALUE ANALYSIS")
    print("="*60)
    
    error_value = 3825401856
    print(f"Error value (decimal): {error_value}")
    print(f"Error value (hex): {hex(error_value)}")
    print(f"Error value (binary): {bin(error_value)}")
    
    # Convert to bytes and see what the original value might have been
    try:
        # If this came from big-endian interpretation of little-endian data
        big_endian_bytes = struct.pack('>I', error_value)
        print(f"As big-endian bytes: {big_endian_bytes.hex()}")
        
        # Try to interpret as little-endian
        original_little = struct.unpack('<I', big_endian_bytes)[0]
        print(f"Original little-endian value would be: {original_little}")
        
        # Check if this makes sense as a reasonable message size
        if 50 <= original_little <= 5000:
            print(f"✅ {original_little} is a reasonable message size!")
        else:
            print(f"❌ {original_little} is not a reasonable message size")
            
    except:
        pass
    
    # Try the reverse - what little-endian value gives this big-endian interpretation
    try:
        little_endian_bytes = struct.pack('<I', error_value)
        print(f"As little-endian bytes: {little_endian_bytes.hex()}")
        
        # This would overflow uint32, so let's try with smaller values
        # Let's see what value when interpreted backwards gives a reasonable size
        for test_size in [100, 150, 200, 250, 300]:
            big_bytes = struct.pack('>I', test_size)
            wrong_interpretation = struct.unpack('<I', big_bytes)[0]
            if wrong_interpretation == error_value:
                print(f"✅ Original value was {test_size} in big-endian format!")
                break
        
    except Exception as e:
        print(f"Error in reverse analysis: {e}")

def test_big_endian_client():
    """Test sending a request using big-endian format (simulating problematic client)"""
    print("\n" + "="*60)
    print("BIG-ENDIAN CLIENT TEST (Problematic)")
    print("="*60)
    
    request_data = {
        "task": "summarize_handover", 
        "input_text": "Short test"
    }
    
    json_str = json.dumps(request_data, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    total_size = len(json_bytes)
    json_size = len(json_bytes)
    
    print(f"Actual sizes - Total: {total_size}, JSON: {json_size}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 6004))
        
        # Send with BIG-ENDIAN format (this should cause the error)
        header = struct.pack('>I', total_size) + struct.pack('>I', json_size)
        print(f"Big-endian header: {header.hex()}")
        
        # Show what the server will interpret
        server_total = struct.unpack('<I', header[:4])[0]
        server_json = struct.unpack('<I', header[4:8])[0]
        print(f"Server will interpret as - Total: {server_total}, JSON: {server_json}")
        
        if server_total > 10*1024*1024:  # 10MB limit
            print(f"❌ Server will reject this as too large!")
            sock.close()
            return False
        
        # Send header + data
        sock.sendall(header + json_bytes)
        
        # Try to receive response (this should fail)
        print("Attempting to receive response...")
        
        # Set a short timeout
        sock.settimeout(5.0)
        
        try:
            response_header = recv_exact(sock, 8)
            response_total_size = struct.unpack('<I', response_header[:4])[0]
            response_json_size = struct.unpack('<I', response_header[4:8])[0]
            
            print(f"Response header - Total: {response_total_size}, JSON: {response_json_size}")
            
            response_data = recv_exact(sock, response_total_size)
            response_json = response_data[:response_json_size].decode('utf-8')
            
            print(f"Response: {response_json}")
            
        except Exception as e:
            print(f"Failed to receive response: {e}")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"Big-endian client test failed: {e}")
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

def find_original_size():
    """Try to find what original size produces the error value"""
    print("\n" + "="*60)
    print("FINDING ORIGINAL SIZE")
    print("="*60)
    
    target_error = 3825401856
    
    # Try different reasonable message sizes
    for size in range(50, 1000, 10):
        # Convert size to big-endian
        big_endian = struct.pack('>I', size)
        # Interpret as little-endian (what server does)
        misinterpreted = struct.unpack('<I', big_endian)[0]
        
        if misinterpreted == target_error:
            print(f"✅ Found it! Original size was {size}")
            print(f"Big-endian bytes: {big_endian.hex()}")
            print(f"Misinterpreted as: {misinterpreted}")
            return size
    
    print("❌ Could not find exact match in reasonable size range")
    
    # Try to work backwards from the hex representation
    error_hex = hex(target_error)[2:]  # Remove '0x'
    print(f"Error value hex: {error_hex}")
    
    # Pad to 8 characters
    error_hex_padded = error_hex.zfill(8)
    print(f"Padded hex: {error_hex_padded}")
    
    # Try to interpret as little-endian bytes
    try:
        # Convert hex to bytes (assuming it was stored as little-endian)
        hex_bytes = bytes.fromhex(error_hex_padded)
        print(f"As bytes: {hex_bytes.hex()}")
        
        # Reverse bytes to get big-endian original
        reversed_bytes = hex_bytes[::-1]
        original_value = struct.unpack('>I', reversed_bytes)[0]
        print(f"Reverse-engineered original: {original_value}")
        
    except Exception as e:
        print(f"Reverse engineering failed: {e}")

def main():
    """Run endian bug reproduction tests"""
    print("ENDIAN BUG REPRODUCTION TEST")
    print("Attempting to reproduce: jsonSize=3825401856, totalSize=3825401856")
    
    analyze_error_value()
    find_original_size()
    test_big_endian_client()
    
    print("\n" + "="*60)
    print("REPRODUCTION SUMMARY")
    print("="*60)
    print("The error occurs when:")
    print("1. Client sends data using big-endian format")
    print("2. Server interprets header as little-endian") 
    print("3. This causes massive size values that exceed limits")
    print("4. Server rejects the packet as invalid")
    
    print("\nSolution:")
    print("✅ Current server correctly uses little-endian format")
    print("✅ Protocol detection prevents most issues")
    print("⚠️  Clients must use little-endian format for binary protocol")

if __name__ == "__main__":
    main()