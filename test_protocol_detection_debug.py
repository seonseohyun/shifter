#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Protocol Detection Debug Test
Debug the protocol detection and error handling flow
"""

import socket
import json
import struct
import time

def test_big_endian_with_short_data():
    """Test with shorter data to see protocol detection in action"""
    print("="*60)
    print("BIG-ENDIAN WITH SHORT DATA TEST")
    print("="*60)
    
    # Very short request to avoid memory issues
    request_data = {"task": "summarize_handover", "input_text": "test"}
    
    json_str = json.dumps(request_data)  # No ensure_ascii=False to keep it shorter
    json_bytes = json_str.encode('utf-8')
    total_size = len(json_bytes)
    json_size = len(json_bytes)
    
    print(f"Short request: {json_str}")
    print(f"Actual sizes - Total: {total_size}, JSON: {json_size}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)  # Short timeout
        sock.connect(('127.0.0.1', 6004))
        
        # Send big-endian header
        header = struct.pack('>I', total_size) + struct.pack('>I', json_size)
        print(f"Big-endian header: {header.hex()}")
        
        # Calculate server interpretation
        server_total = struct.unpack('<I', header[:4])[0]
        server_json = struct.unpack('<I', header[4:8])[0]
        print(f"Server will see: Total={server_total}, JSON={server_json}")
        
        if server_total > 10*1024*1024:
            print("❌ Server will reject as too large")
        elif server_total < 1000000:  # Less suspicious
            print("✅ Size might pass initial validation")
        
        # Send just the header first to test protocol detection
        print("Sending header only...")
        sock.send(header)
        time.sleep(0.1)  # Give server time to process
        
        # Send the JSON data
        print("Sending JSON data...")
        sock.send(json_bytes)
        
        # Try to get response
        print("Waiting for response...")
        
        # Try to receive as binary first
        try:
            response_header = sock.recv(8)
            if len(response_header) == 8:
                response_total = struct.unpack('<I', response_header[:4])[0]
                response_json = struct.unpack('<I', response_header[4:8])[0]
                print(f"Binary response header: Total={response_total}, JSON={response_json}")
                
                if response_total < 10000:  # Reasonable size
                    response_data = sock.recv(response_total)
                    response_str = response_data[:response_json].decode('utf-8')
                    print(f"Binary response: {response_str}")
                    return True
            else:
                print(f"Got partial header: {response_header}")
        except Exception as e:
            print(f"Binary read failed: {e}")
        
        # Try legacy response
        try:
            sock.settimeout(2.0)
            all_data = b''
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                all_data += chunk
            
            if all_data:
                response_str = all_data.decode('utf-8')
                print(f"Legacy response: {response_str}")
                return True
        except Exception as e:
            print(f"Legacy read failed: {e}")
        
        print("❌ No response received")
        return False
        
    except Exception as e:
        print(f"Connection error: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass

def test_protocol_peek_behavior():
    """Test how protocol detection peek works"""
    print("\n" + "="*60)
    print("PROTOCOL PEEK BEHAVIOR TEST")
    print("="*60)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 6004))
        
        # Send a big-endian header that will create a large misinterpreted size
        header = struct.pack('>I', 100) + struct.pack('>I', 100)
        print(f"Sending big-endian header: {header.hex()}")
        
        # Server interpretation
        server_total = struct.unpack('<I', header[:4])[0]
        server_json = struct.unpack('<I', header[4:8])[0]
        print(f"Server will interpret as: Total={server_total}, JSON={server_json}")
        
        if server_total > 1000000:
            print("This should trigger endian mismatch detection")
        
        # Send header
        sock.send(header)
        
        # Send some JSON data
        json_data = json.dumps({"task": "summarize_handover", "input_text": "test"})
        sock.send(json_data.encode('utf-8'))
        
        # Server should detect protocol and respond
        print("Waiting for server response...")
        sock.settimeout(5.0)
        
        try:
            # Try to read any response
            response = sock.recv(4096)
            if response:
                print(f"Got response ({len(response)} bytes): {response[:200]}...")
                try:
                    response_str = response.decode('utf-8')
                    print(f"Decoded response: {response_str}")
                    
                    if 'endian' in response_str.lower():
                        print("✅ Endian mismatch detected in response!")
                        return True
                except Exception as e:
                    print(f"Could not decode as text: {e}")
                    print(f"Raw bytes: {response.hex()}")
                
                return True
            else:
                print("❌ No response received")
                return False
        except socket.timeout:
            print("⏰ Timeout - no response")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass

def main():
    """Run protocol detection debug tests"""
    print("PROTOCOL DETECTION DEBUG TEST")
    print("="*60)
    
    # Test the peek behavior
    peek_result = test_protocol_peek_behavior()
    
    # Test with short data
    short_result = test_big_endian_with_short_data()
    
    print(f"\n🔍 Test Results:")
    print(f"Protocol peek test: {'✅ PASS' if peek_result else '❌ FAIL'}")
    print(f"Short data test: {'✅ PASS' if short_result else '❌ FAIL'}")
    
    if not (peek_result or short_result):
        print("\n⚠️  Server may be closing connections before sending error responses")
        print("🔧 Check server logs for protocol detection messages")

if __name__ == "__main__":
    main()