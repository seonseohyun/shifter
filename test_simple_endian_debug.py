#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Endian Debug Test
Tests just the basic connection and header handling
"""

import socket
import struct
import time

def test_simple_endian_connection():
    """Test basic connection with endian mismatch header"""
    print("="*50)
    print("SIMPLE ENDIAN CONNECTION TEST")
    print("="*50)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        
        print("Connecting to server...")
        sock.connect(('127.0.0.1', 6004))
        print("✅ Connected successfully")
        
        # Create a big-endian header that will cause endian mismatch
        total_size = 100
        json_size = 100
        
        big_endian_header = struct.pack('>I', total_size) + struct.pack('>I', json_size)
        print(f"Sending big-endian header: {big_endian_header.hex()}")
        
        # Show what server will interpret this as
        server_total = struct.unpack('<I', big_endian_header[:4])[0]
        server_json = struct.unpack('<I', big_endian_header[4:8])[0]
        print(f"Server will interpret as: Total={server_total}, JSON={server_json}")
        
        # Send just the header
        print("Sending header...")
        sent = sock.send(big_endian_header)
        print(f"✅ Sent {sent} bytes")
        
        # Wait a moment for server processing
        time.sleep(0.5)
        
        # Check if connection is still alive
        try:
            # Try to send another byte to see if connection is alive
            sock.send(b'x')
            print("✅ Connection still alive after header")
        except Exception as e:
            print(f"⚠️  Connection seems closed: {e}")
        
        # Try to read any response
        print("Waiting for any response...")
        try:
            sock.settimeout(2.0)
            response = sock.recv(1024)
            if response:
                print(f"✅ Got response: {len(response)} bytes")
                print(f"Raw response: {response}")
                try:
                    decoded = response.decode('utf-8')
                    print(f"Decoded response: {decoded}")
                except Exception as e:
                    print(f"Could not decode as UTF-8: {e}")
            else:
                print("❌ No response received")
        except socket.timeout:
            print("⏰ Timeout waiting for response")
        except Exception as e:
            print(f"Error reading response: {e}")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass

def test_minimal_big_endian_request():
    """Test with a complete but minimal big-endian request"""
    print("\n" + "="*50)
    print("MINIMAL BIG-ENDIAN REQUEST TEST")
    print("="*50)
    
    # Minimal JSON
    json_data = '{"test":1}'
    json_bytes = json_data.encode('utf-8')
    total_size = len(json_bytes)
    json_size = len(json_bytes)
    
    print(f"JSON: {json_data}")
    print(f"Sizes: Total={total_size}, JSON={json_size}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        sock.connect(('127.0.0.1', 6004))
        print("✅ Connected")
        
        # Big-endian header
        header = struct.pack('>I', total_size) + struct.pack('>I', json_size)
        print(f"Big-endian header: {header.hex()}")
        
        # Server interpretation
        server_total = struct.unpack('<I', header[:4])[0]
        server_json = struct.unpack('<I', header[4:8])[0]
        print(f"Server sees: Total={server_total}, JSON={server_json}")
        
        # Send header + data
        full_packet = header + json_bytes
        print(f"Sending full packet ({len(full_packet)} bytes)...")
        sock.sendall(full_packet)
        
        # Wait for response
        print("Waiting for response...")
        
        start_time = time.time()
        response_data = b''
        
        while time.time() - start_time < 8.0:  # 8 second timeout
            try:
                chunk = sock.recv(1024)
                if not chunk:
                    print("Connection closed by server")
                    break
                response_data += chunk
                print(f"Got chunk: {len(chunk)} bytes")
                
                # Try to decode partial response
                try:
                    decoded = response_data.decode('utf-8')
                    print(f"Partial decoded: {decoded[:100]}...")
                    
                    # If it looks like complete JSON, break
                    if decoded.strip().endswith('}'):
                        break
                        
                except Exception:
                    continue
                    
            except socket.timeout:
                print("Timeout on recv")
                break
            except Exception as e:
                print(f"Error receiving: {e}")
                break
        
        if response_data:
            print(f"Final response ({len(response_data)} bytes):")
            try:
                decoded = response_data.decode('utf-8')
                print(decoded)
                
                # Check if it mentions endian
                if 'endian' in decoded.lower():
                    print("✅ Got endian-related response!")
                    return True
                else:
                    print("ℹ️  Got response but not endian-related")
                    return True
                    
            except Exception as e:
                print(f"Could not decode: {e}")
                print(f"Raw bytes: {response_data}")
        else:
            print("❌ No response received at all")
        
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
    """Run simple endian debug tests"""
    print("SIMPLE ENDIAN DEBUG TEST")
    print("="*50)
    
    result1 = test_simple_endian_connection()
    result2 = test_minimal_big_endian_request()
    
    print(f"\n📊 Results:")
    print(f"Simple connection test: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Minimal request test: {'✅ PASS' if result2 else '❌ FAIL'}")
    
    if not (result1 or result2):
        print("\n🔧 Debug suggestions:")
        print("• Check if server is running on port 6004")
        print("• Check server logs for connection attempts")
        print("• Verify protocol detection is working")
        print("• Test with a working client first")

if __name__ == "__main__":
    main()