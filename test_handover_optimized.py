#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인수인계 요약 기능 테스트 클라이언트 (Optimized Server용)
"""

import socket
import json
import time


def test_handover_summary():
    """인수인계 요약 기능 테스트"""
    
    # 테스트 인수인계 내용
    test_handover_text = """오늘 인수인계 내용은 다음과 같습니다:
    
1. 간병실 501호 김할머니 - 혈압 불안정, 2시간마다 체크 필요
2. 수술실 준비 - 내일 오전 9시 정형외과 수술 예정, 기구 점검 완료
3. 신규 간호사 교육 - 이번 주 금요일까지 야간 근무 금지
4. 의료진 회의 - 매주 화요일 오후 3시, 참석 필수
5. 응급실 상황 - 코로나 환자 증가로 격리실 부족, 추가 대응 방안 논의 중
6. 장비 점검 - 인공호흡기 3번 고장, 수리 업체 연락함
7. 약물 관리 - 마약성 진통제 재고 부족, 내일까지 주문 처리
8. 환자 퇴원 - 302호 박환자 내일 오전 퇴원 예정, 퇴원 준비 완료
9. 보호자 상담 - 405호 환자 보호자와 치료 방향 상담 예정
10. 기타 사항 - 엘리베이터 2호기 점검으로 오후 2-4시 사용 불가"""
    
    request = {
        "task": "summarize_handover",
        "input_text": test_handover_text
    }
    
    try:
        print("📋 인수인계 요약 기능 테스트")
        print("=" * 50)
        print(f"원본 텍스트 길이: {len(test_handover_text)} 문자")
        print("\n🔄 서버에 요청 전송 중...")
        
        # 소켓 연결
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 6004))
            
            # 요청 전송
            request_json = json.dumps(request, ensure_ascii=False)
            s.sendall(request_json.encode('utf-8'))
            s.shutdown(socket.SHUT_WR)
            
            # 응답 수신
            response_data = b''
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response_data += chunk
        
        # 응답 파싱
        response = json.loads(response_data.decode('utf-8'))
        
        print(f"📨 서버 응답 수신 완료")
        print("=" * 50)
        
        if response.get("status") == "success":
            print(f"\n✅ 인수인계 요약 성공!")
            print(f"요약 결과:")
            print("-" * 30)
            print(response.get("result", ""))
            print("-" * 30)
            print(f"요약 길이: {len(response.get('result', ''))} 문자")
            
        elif response.get("status") == "error":
            print(f"\n❌ 인수인계 요약 실패!")
            print(f"오류 원인: {response.get('reason', '알 수 없음')}")
            
        else:
            print(f"\n⚠️  예상치 못한 응답:")
            print(json.dumps(response, ensure_ascii=False, indent=2))
    
    except ConnectionRefusedError:
        print("❌ 서버에 연결할 수 없습니다.")
        print("   서버가 실행 중인지 확인하세요:")
        print("   python shift_server_optimized.py")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")


def test_error_scenarios():
    """오류 시나리오 테스트"""
    
    print("\n🧪 오류 시나리오 테스트")
    print("=" * 50)
    
    # 1. 빈 입력 테스트
    print("1. 빈 입력 테스트...")
    test_empty_request = {
        "task": "summarize_handover",
        "input_text": ""
    }
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 6004))
            request_json = json.dumps(test_empty_request, ensure_ascii=False)
            s.sendall(request_json.encode('utf-8'))
            s.shutdown(socket.SHUT_WR)
            
            response_data = b''
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response_data += chunk
        
        response = json.loads(response_data.decode('utf-8'))
        if response.get("status") == "error":
            print("   ✅ 빈 입력 오류 처리 정상")
        else:
            print("   ❌ 빈 입력 오류 처리 실패")
            
    except Exception as e:
        print(f"   ❌ 빈 입력 테스트 실패: {e}")
    
    # 2. 알 수 없는 task 테스트  
    print("2. 알 수 없는 task 테스트...")
    test_unknown_task = {
        "task": "unknown_task",
        "input_text": "test"
    }
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 6004))
            request_json = json.dumps(test_unknown_task, ensure_ascii=False)
            s.sendall(request_json.encode('utf-8'))
            s.shutdown(socket.SHUT_WR)
            
            response_data = b''
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response_data += chunk
        
        response = json.loads(response_data.decode('utf-8'))
        if response.get("status") == "error" and "Unknown task" in response.get("reason", ""):
            print("   ✅ 알 수 없는 task 오류 처리 정상")
        else:
            print("   ❌ 알 수 없는 task 오류 처리 실패")
            
    except Exception as e:
        print(f"   ❌ 알 수 없는 task 테스트 실패: {e}")


if __name__ == "__main__":
    print("🚀 인수인계 요약 기능 테스트 시작")
    print("서버가 실행 중인지 확인하세요: python shift_server_optimized.py")
    print("")
    
    # 기본 기능 테스트
    test_handover_summary()
    
    # 오류 시나리오 테스트
    test_error_scenarios()
    
    print("\n✨ 테스트 완료")