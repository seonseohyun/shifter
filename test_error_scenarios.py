#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import json
import time

HOST = '127.0.0.1'
PORT = 6002

def send_request(request_data):
    """TCP 소켓을 통해 서버에 요청을 보내고 응답을 받음"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            
            request_json = json.dumps(request_data, ensure_ascii=False)
            s.sendall(request_json.encode('utf-8'))
            s.shutdown(socket.SHUT_WR)
            
            # 응답 수신
            response_data = b''
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            response_str = response_data.decode('utf-8')
            return json.loads(response_str)
    
    except Exception as e:
        print(f"[ERROR] 서버 연결 또는 요청 처리 중 오류: {e}")
        return None

def test_error_scenario(test_id, request_data, expected_failure, description):
    """오류 시나리오 테스트"""
    
    print(f"\n{'='*60}")
    print(f"오류 테스트 {test_id:2d}: {description}")
    print(f"{'='*60}")
    print(f"예상 결과: {expected_failure}")
    
    response = send_request(request_data)
    
    if response:
        if response.get("result") == "생성실패":
            print("✅ 예상대로 실패함")
            print(f"📝 실패 사유: {response.get('reason', '사유 없음')}")
            if "warnings" in response and response["warnings"]:
                print(f"⚠️  경고사항: {'; '.join(response['warnings'])}")
            if "details" in response:
                print(f"🔍 상세정보: {response['details']}")
            return True
        else:
            print("❌ 예상과 달리 성공함 (문제 있음)")
            return False
    else:
        print("🚨 응답 없음")
        return False

def run_error_tests():
    """다양한 오류 시나리오 테스트"""
    
    print("=== 서버 오류 처리 개선 테스트 ===")
    print("✅ 상세한 실패 사유 제공")
    print("✅ 입력 매개변수 사전 검증")
    print("✅ 솔버 상태별 맞춤 메시지")
    
    # 기본 직원 데이터 (정상)
    valid_staff = [
        {"name": "김간호사", "staff_id": 1001, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 185},
        {"name": "이간호사", "staff_id": 1002, "grade": 4, "grade_name": "간호사", "position": "간호", "total_monthly_work_hours": 195},
        {"name": "박간호사", "staff_id": 1003, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 188}
    ]
    
    error_tests = [
        # 1. staff_data 누락
        {
            "request": {"position": "간호", "shift_type": 3},
            "expected": "staff_data 누락",
            "description": "staff_data 필드 누락"
        },
        
        # 2. 직원 데이터 누락
        {
            "request": {
                "position": "간호", 
                "shift_type": 3,
                "staff_data": {"staff": []}
            },
            "expected": "직원 수 부족",
            "description": "직원 데이터 빈 배열"
        },
        
        # 3. 필수 필드 누락
        {
            "request": {
                "position": "간호",
                "shift_type": 3,
                "staff_data": {
                    "staff": [{"name": "김간호사"}]  # 다른 필수 필드 누락
                }
            },
            "expected": "필수 필드 누락",
            "description": "직원 필수 필드 누락"
        },
        
        # 4. 비현실적인 근무시간
        {
            "request": {
                "position": "간호",
                "shift_type": 3,
                "staff_data": {
                    "staff": [{
                        "name": "김간호사", "staff_id": 1001, "grade": 3, 
                        "grade_name": "일반간호사", "position": "간호", 
                        "total_monthly_work_hours": 500  # 비현실적
                    }]
                }
            },
            "expected": "비현실적 근무시간",
            "description": "월 500시간 근무 (비현실적)"
        },
        
        # 5. custom_rules 불완전
        {
            "request": {
                "position": "간호",
                "shift_type": 3,
                "staff_data": {"staff": valid_staff},
                "custom_rules": {"shifts": ["D", "N", "O"]}  # shift_hours 누락
            },
            "expected": "custom_rules 불완전",
            "description": "custom_rules에 shift_hours 누락"
        },
        
        # 6. 시프트 수 부족
        {
            "request": {
                "position": "간호",
                "shift_type": 3,
                "staff_data": {"staff": valid_staff},
                "custom_rules": {
                    "shifts": ["O"],  # 휴무만 있음
                    "shift_hours": {"O": 0}
                }
            },
            "expected": "시프트 수 부족",
            "description": "휴무 시프트만 존재"
        },
        
        # 7. 휴무 시프트 누락
        {
            "request": {
                "position": "간호",
                "shift_type": 3,
                "staff_data": {"staff": valid_staff},
                "custom_rules": {
                    "shifts": ["D", "E", "N"],  # 휴무 없음
                    "shift_hours": {"D": 8, "E": 8, "N": 8}
                }
            },
            "expected": "휴무 시프트 누락",
            "description": "휴무 시프트가 없음"
        },
        
        # 8. 시간 배정 누락
        {
            "request": {
                "position": "간호",
                "shift_type": 3,
                "staff_data": {"staff": valid_staff},
                "custom_rules": {
                    "shifts": ["D", "E", "N", "O"],
                    "shift_hours": {"D": 8, "E": 8}  # N, O 시간 누락
                }
            },
            "expected": "시간 배정 누락",
            "description": "일부 시프트 시간 배정 누락"
        },
        
        # 9. 휴무에 근무시간 배정
        {
            "request": {
                "position": "간호",
                "shift_type": 3,
                "staff_data": {"staff": valid_staff},
                "custom_rules": {
                    "shifts": ["D", "E", "N", "O"],
                    "shift_hours": {"D": 8, "E": 8, "N": 8, "O": 4}  # 휴무에 4시간
                }
            },
            "expected": "휴무 시간 오류",
            "description": "휴무 시프트에 근무시간 배정"
        },
        
        # 10. 수학적으로 불가능한 조합 (기존 4교대 6시간 문제)
        {
            "request": {
                "position": "간호",
                "shift_type": 3,
                "staff_data": {"staff": valid_staff},  # 3명만으로
                "custom_rules": {
                    "shifts": ["새벽", "오전", "오후", "밤", "휴무"],  # 4교대
                    "shift_hours": {"새벽": 6, "오전": 6, "오후": 6, "밤": 6, "휴무": 0}
                }
            },
            "expected": "수학적 불가능",
            "description": "3명으로 4교대 운영 (수학적 불가능)"
        }
    ]
    
    success_count = 0
    
    for i, test in enumerate(error_tests, 1):
        success = test_error_scenario(
            i, 
            test["request"], 
            test["expected"], 
            test["description"]
        )
        if success:
            success_count += 1
        
        time.sleep(0.1)  # 서버 부담 줄이기
    
    # 최종 결과
    print(f"\n{'='*60}")
    print(f"🏆 오류 처리 테스트 결과")
    print(f"{'='*60}")
    print(f"총 테스트: {len(error_tests)}개")
    print(f"올바른 오류 처리: {success_count}개 ({success_count/len(error_tests)*100:.1f}%)")
    print(f"잘못된 처리: {len(error_tests)-success_count}개")
    
    if success_count == len(error_tests):
        print(f"\n🎉 모든 오류 시나리오가 올바르게 처리됨!")
    else:
        print(f"\n⚠️  일부 오류 처리 개선 필요")
    
    return success_count, len(error_tests)

if __name__ == "__main__":
    print("서버 오류 처리 개선 테스트 클라이언트")
    print("서버가 실행 중인지 확인하세요 (포트 6002)")
    
    success, total = run_error_tests()
    
    print(f"\n테스트 완료 - 오류 처리 성공률: {success}/{total}")