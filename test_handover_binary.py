#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C++ 바이너리 프로토콜로 인수인계 요청 테스트
"""

import socket
import json
import struct


def test_handover_binary_protocol():
    """C++ 바이너리 프로토콜을 시뮬레이션하여 인수인계 요청 테스트"""
    
    print("🔧 C++ 바이너리 프로토콜로 인수인계 요청 테스트")
    print("=" * 60)
    
    # 인수인계 요청 데이터
    handover_request = {
        "task": "summarize_handover",
        "input_text": "환자 501호 김할머니 혈압 불안정. 2시간마다 체크 필요. 내일 오전 정형외과 수술 예정."
    }
    
    try:
        # JSON 인코딩
        json_str = json.dumps(handover_request, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')
        
        total_size = len(json_bytes)
        json_size = len(json_bytes)
        
        # 리틀엔디안 헤더 생성 (C++ uint32_t 호환)
        header = struct.pack('<I', total_size) + struct.pack('<I', json_size)
        
        print(f"📤 요청 전송:")
        print(f"  - JSON 길이: {len(json_bytes)} 바이트")
        print(f"  - 헤더: totalSize={total_size}, jsonSize={json_size}")
        print(f"  - 요청 내용: {json_str[:80]}...")
        
        # 서버 연결
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(('127.0.0.1', 6004))
            
            # 헤더 + 데이터 전송
            sock.sendall(header + json_bytes)
            print("  ✅ 요청 전송 완료")
            
            # 응답 헤더 수신
            response_header = recv_exact(sock, 8)
            resp_total_size = struct.unpack('<I', response_header[:4])[0]
            resp_json_size = struct.unpack('<I', response_header[4:8])[0]
            
            print(f"\n📥 응답 수신:")
            print(f"  - 응답 헤더: totalSize={resp_total_size}, jsonSize={resp_json_size}")
            
            # 응답 데이터 수신
            response_data = recv_exact(sock, resp_json_size)
            response_json = response_data.decode('utf-8')
            response = json.loads(response_json)
            
            print(f"  - 응답 길이: {len(response_data)} 바이트")
            print(f"  ✅ 응답 수신 완료")
            
            # 결과 출력
            print(f"\n🎯 인수인계 요약 결과:")
            print("-" * 40)
            if response.get("status") == "success":
                result = response.get("result", "")
                print(f"✅ 성공!")
                print(f"요약 내용:\n{result}")
            else:
                print(f"❌ 실패: {response.get('reason', '알 수 없음')}")
            print("-" * 40)
            
            return True
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


def recv_exact(sock, n):
    """정확히 n바이트 수신"""
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("연결이 종료됨")
        buf += chunk
    return buf


if __name__ == "__main__":
    print("🚀 C++ 바이너리 프로토콜 인수인계 테스트")
    print("서버가 실행 중인지 확인: python3 shift_server_optimized.py")
    print()
    
    success = test_handover_binary_protocol()
    
    if success:
        print("\n✨ 테스트 성공! C++ 바이너리 프로토콜로 인수인계 정상 작동")
    else:
        print("\n💥 테스트 실패! 프로토콜 호환성 문제 있음")