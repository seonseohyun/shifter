#!/usr/bin/env python3
import socket
import json

def test_handover_summary():
    """인수인계 요약 기능 테스트"""
    
    # 테스트 인수인계 내용
    test_handover_text = """오늘 인수인계 내용은 다음과 같습니다:

- A 환자 (301호): 내일 오전 9시 수술 예정, 금식 상태 유지 필요
- B 환자 (302호): 혈압약 변경됨 (아모잘탄 → 올메사르탄), 부작용 모니터링 필요
- C 환자 (303호): 당뇨 수치 상승으로 인슐린 용량 조정, 혈당 체크 2시간마다
- D 환자 (304호): 낙상 위험 높음, 침대 난간 올리고 이동 시 보조 필요
- 응급실에서 E 환자 입원 예정 (21:30경), 복통 의심 급성 충수염
- 야간 당직의 연락처: 내선 2345
- 의료진 회의 내일 오전 8시, 새로운 감염관리 지침 논의
- 장비실 점검으로 인해 2층 MRI 내일 오후 3-5시 사용 불가"""

    # 요청 생성
    request = {
        "task": "summarize_handover",
        "input_text": test_handover_text
    }
    
    # 서버 연결
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 6004))
        
        # 요청 전송
        request_json = json.dumps(request, ensure_ascii=False)
        print("=== 전송 요청 ===")
        print(json.dumps(request, ensure_ascii=False, indent=2))
        
        sock.sendall(request_json.encode('utf-8'))
        sock.shutdown(socket.SHUT_WR)
        
        # 응답 수신
        response_data = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
        
        sock.close()
        
        # 응답 처리
        print("\n=== 서버 응답 ===")
        response_str = response_data.decode('utf-8')
        
        try:
            response_json = json.loads(response_str)
            print(json.dumps(response_json, ensure_ascii=False, indent=2))
            
            # 결과 분석
            if response_json.get("status") == "success":
                print(f"\n✅ 인수인계 요약 성공!")
                print(f"📋 요약 결과:")
                print(f"{response_json.get('result', 'N/A')}")
            else:
                print(f"\n❌ 인수인계 요약 실패!")
                print(f"오류: {response_json.get('reason', 'N/A')}")
                
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 실패: {e}")
            print(f"Raw 응답: {response_str}")
            
    except Exception as e:
        print(f"테스트 오류: {e}")

def test_empty_input():
    """빈 입력 테스트"""
    print("\n" + "="*50)
    print("빈 입력 테스트")
    print("="*50)
    
    request = {
        "task": "summarize_handover", 
        "input_text": ""
    }
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 6004))
        
        request_json = json.dumps(request, ensure_ascii=False)
        sock.sendall(request_json.encode('utf-8'))
        sock.shutdown(socket.SHUT_WR)
        
        response_data = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
        
        sock.close()
        
        response_str = response_data.decode('utf-8')
        response_json = json.loads(response_str)
        print(json.dumps(response_json, ensure_ascii=False, indent=2))
        
        if response_json.get("status") == "error":
            print(f"\n✅ 빈 입력 처리 정상: {response_json.get('reason')}")
        
    except Exception as e:
        print(f"빈 입력 테스트 오류: {e}")

def test_unknown_task():
    """알 수 없는 task 테스트"""
    print("\n" + "="*50)
    print("알 수 없는 task 테스트")
    print("="*50)
    
    request = {
        "task": "unknown_task",
        "input_text": "test"
    }
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 6004))
        
        request_json = json.dumps(request, ensure_ascii=False)
        sock.sendall(request_json.encode('utf-8'))
        sock.shutdown(socket.SHUT_WR)
        
        response_data = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
        
        sock.close()
        
        response_str = response_data.decode('utf-8')
        response_json = json.loads(response_str)
        print(json.dumps(response_json, ensure_ascii=False, indent=2))
        
        if response_json.get("status") == "error":
            print(f"\n✅ 알 수 없는 task 처리 정상: {response_json.get('reason')}")
        
    except Exception as e:
        print(f"알 수 없는 task 테스트 오류: {e}")

if __name__ == "__main__":
    print("="*50)
    print("인수인계 요약 기능 테스트")
    print("="*50)
    
    test_handover_summary()
    test_empty_input() 
    test_unknown_task()
    
    print(f"\n테스트 완료!")