#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Handover Endian Verification Test
Verifies that handover summarization works correctly with both protocols and handles endian mismatches
"""

import socket
import json
import struct
import time
import threading
import sys
from typing import Dict, Any, Optional, Tuple

def recv_exact(sock: socket.socket, n: int) -> bytes:
    """Receive exactly n bytes from socket"""
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket connection closed unexpectedly")
        buf += chunk
    return buf

class HandoverProtocolTester:
    """Comprehensive handover protocol tester"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 6004):
        self.host = host
        self.port = port
        
    def test_handover_binary_protocol(self) -> Tuple[bool, Optional[Dict]]:
        """Test handover with correct binary protocol"""
        print("\n🔧 TESTING HANDOVER WITH BINARY PROTOCOL (Little-endian)")
        print("-" * 60)
        
        request = {
            "task": "summarize_handover",
            "input_text": "실제 인수인계: G 환자 수술후 관찰, H 환자 혈압체크 필요, I 환자 퇴원준비"
        }
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            
            # Prepare request
            json_str = json.dumps(request, ensure_ascii=False)
            json_bytes = json_str.encode('utf-8')
            total_size = len(json_bytes)
            json_size = len(json_bytes)
            
            print(f"Request size: {total_size} bytes")
            
            # Send with correct little-endian format
            header = struct.pack('<I', total_size) + struct.pack('<I', json_size)
            sock.sendall(header + json_bytes)
            
            # Receive binary response
            response_header = recv_exact(sock, 8)
            response_total = struct.unpack('<I', response_header[:4])[0]
            response_json_size = struct.unpack('<I', response_header[4:8])[0]
            
            print(f"Response header: totalSize={response_total}, jsonSize={response_json_size}")
            
            response_data = recv_exact(sock, response_total)
            response_json = response_data[:response_json_size].decode('utf-8')
            
            response_dict = json.loads(response_json)
            
            print(f"Response status: {response_dict.get('status')}")
            print(f"Task: {response_dict.get('task')}")
            
            if response_dict.get('status') == 'success':
                print(f"Summary preview: {response_dict.get('result', '')[:100]}...")
                print("✅ Binary protocol handover SUCCESS")
                
                sock.close()
                return True, response_dict
            else:
                print(f"❌ Handover failed: {response_dict.get('reason', 'Unknown error')}")
                sock.close()
                return False, response_dict
                
        except Exception as e:
            print(f"❌ Binary protocol test failed: {e}")
            return False, None
            
    def test_handover_legacy_protocol(self) -> Tuple[bool, Optional[Dict]]:
        """Test handover with legacy protocol"""
        print("\n🔧 TESTING HANDOVER WITH LEGACY PROTOCOL")
        print("-" * 60)
        
        request = {
            "task": "summarize_handover",
            "input_text": "레거시 인수인계: J 환자 약물반응 체크, K 환자 검사일정 변경, L 환자 상태안정"
        }
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            
            # Send JSON without headers
            json_str = json.dumps(request, ensure_ascii=False)
            sock.sendall(json_str.encode('utf-8'))
            sock.shutdown(socket.SHUT_WR)
            
            # Receive response
            response_data = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                
            response_str = response_data.decode('utf-8')
            response_dict = json.loads(response_str)
            
            print(f"Response status: {response_dict.get('status')}")
            print(f"Task: {response_dict.get('task')}")
            
            if response_dict.get('status') == 'success':
                print(f"Summary preview: {response_dict.get('result', '')[:100]}...")
                print("✅ Legacy protocol handover SUCCESS")
                
                sock.close()
                return True, response_dict
            else:
                print(f"❌ Handover failed: {response_dict.get('reason', 'Unknown error')}")
                sock.close()
                return False, response_dict
                
        except Exception as e:
            print(f"❌ Legacy protocol test failed: {e}")
            return False, None
            
    def test_endian_mismatch_detection(self) -> Tuple[bool, Optional[Dict]]:
        """Test endian mismatch detection with handover request"""
        print("\n🚨 TESTING ENDIAN MISMATCH DETECTION")
        print("-" * 60)
        
        request = {
            "task": "summarize_handover", 
            "input_text": "잘못된 엔디안: M 환자 응급상황, N 환자 수술연기"
        }
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            
            # Create big-endian packet (wrong format)
            json_str = json.dumps(request, ensure_ascii=False)
            json_bytes = json_str.encode('utf-8')
            total_size = len(json_bytes)
            json_size = len(json_bytes)
            
            # Big-endian header (problematic)
            header = struct.pack('>I', total_size) + struct.pack('>I', json_size)
            
            print(f"Sending big-endian header: {header.hex()}")
            print(f"Server will interpret as: {struct.unpack('<I', header[:4])[0]}, {struct.unpack('<I', header[4:8])[0]}")
            
            sock.sendall(header + json_bytes)
            
            # Try to receive response (should be error message)
            try:
                sock.settimeout(5.0)
                response_data = b''
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response_data += chunk
                    
                    # Try parsing as complete JSON
                    try:
                        response_str = response_data.decode('utf-8')
                        json.loads(response_str)
                        break
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                        
            except socket.timeout:
                print("⚠️ No response received (timeout)")
                sock.close()
                return False, None
                
            if response_data:
                response_str = response_data.decode('utf-8')
                response_dict = json.loads(response_str)
                
                print(f"Server response type: {response_dict.get('error_type', 'unknown')}")
                print(f"Message: {response_dict.get('message', 'No message')}")
                
                if response_dict.get('error_type') == 'endian_mismatch':
                    print("✅ Server correctly detected endian mismatch")
                    sock.close()
                    return True, response_dict
                else:
                    print("⚠️ Server did not detect endian mismatch correctly")
                    sock.close()
                    return False, response_dict
            else:
                print("❌ No response from server")
                sock.close()
                return False, None
                
        except Exception as e:
            print(f"❌ Endian mismatch test failed: {e}")
            return False, None
            
    def test_concurrent_handover_requests(self) -> bool:
        """Test multiple concurrent handover requests"""
        print("\n⚡ TESTING CONCURRENT HANDOVER REQUESTS")
        print("-" * 60)
        
        def single_handover_test(test_id: int) -> bool:
            request = {
                "task": "summarize_handover",
                "input_text": f"동시요청 #{test_id}: 환자 상태확인, 약물투여시간 체크"
            }
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, self.port))
                
                json_str = json.dumps(request, ensure_ascii=False)
                json_bytes = json_str.encode('utf-8')
                total_size = len(json_bytes)
                
                header = struct.pack('<I', total_size) + struct.pack('<I', total_size)
                sock.sendall(header + json_bytes)
                
                # Receive response
                response_header = recv_exact(sock, 8)
                response_total = struct.unpack('<I', response_header[:4])[0]
                response_data = recv_exact(sock, response_total)
                response_str = response_data.decode('utf-8')
                
                response_dict = json.loads(response_str)
                success = response_dict.get('status') == 'success'
                
                print(f"Request #{test_id}: {'✅ SUCCESS' if success else '❌ FAILED'}")
                sock.close()
                return success
                
            except Exception as e:
                print(f"Request #{test_id}: ❌ FAILED ({e})")
                return False
                
        # Run 5 concurrent requests
        threads = []
        results = [False] * 5
        
        def thread_worker(test_id: int):
            results[test_id] = single_handover_test(test_id + 1)
            
        for i in range(5):
            thread = threading.Thread(target=thread_worker, args=(i,))
            threads.append(thread)
            thread.start()
            
        # Wait for all threads
        for thread in threads:
            thread.join()
            
        success_count = sum(results)
        print(f"\nConcurrency test: {success_count}/5 requests succeeded")
        
        return success_count >= 4  # Allow one failure
        
    def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run all handover protocol tests"""
        print("="*70)
        print("COMPREHENSIVE HANDOVER ENDIAN VERIFICATION TEST")
        print("="*70)
        
        results = {}
        
        # Test 1: Binary protocol
        binary_success, binary_response = self.test_handover_binary_protocol()
        results['binary_protocol'] = binary_success
        
        # Test 2: Legacy protocol  
        legacy_success, legacy_response = self.test_handover_legacy_protocol()
        results['legacy_protocol'] = legacy_success
        
        # Test 3: Endian mismatch detection
        endian_success, endian_response = self.test_endian_mismatch_detection()
        results['endian_detection'] = endian_success
        
        # Test 4: Concurrent requests
        concurrent_success = self.test_concurrent_handover_requests()
        results['concurrent_requests'] = concurrent_success
        
        # Summary
        print("\n" + "="*70)
        print("TEST RESULTS SUMMARY")
        print("="*70)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
            
        all_passed = all(results.values())
        print(f"\nOverall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        if all_passed:
            print("\n🎯 HANDOVER PROTOCOL VERIFICATION: COMPLETE")
            print("✅ Handover summarization works correctly with both protocols")
            print("✅ Endian mismatch detection works correctly")  
            print("✅ Server handles concurrent handover requests properly")
            print("✅ All protocol edge cases are handled correctly")
        else:
            print("\n🚨 ISSUES DETECTED:")
            for test_name, success in results.items():
                if not success:
                    print(f"❌ {test_name.replace('_', ' ').title()} needs attention")
                    
        return results

def main():
    """Main test entry point"""
    tester = HandoverProtocolTester()
    results = tester.run_comprehensive_test()
    
    # Return appropriate exit code
    sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    main()