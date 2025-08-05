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
            
            # 응답 수신
            response = b''
            while True:
                data = s.recv(4096)
                if not data:
                    break
                response += data
            
            response_str = response.decode('utf-8')
            return json.loads(response_str)
    
    except Exception as e:
        print(f"[ERROR] 서버 연결 또는 요청 처리 중 오류: {e}")
        return None

def test_custom_shift(test_id, shifts, shift_hours):
    """커스텀 shift 구성에 대한 테스트 수행"""
    nursing_request = {
        "position": "간호",
        "shift_type": 3,  # 기본값 유지, 실제로는 custom_rules가 오버라이드
        "target_month": "2025-09",  # 9월 근무표 생성
        "staff_data": {
            "staff": [
               
                {"name": "장간호사", "staff_id": 111, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 185},
                {"name": "임간호사", "staff_id": 112, "grade": 4, "grade_name": "간호사", "position": "간호", "total_monthly_work_hours": 198},
                {"name": "홍간호사", "staff_id": 113, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 193},
                {"name": "강간호사", "staff_id": 114, "grade": 2, "grade_name": "주임간호사", "position": "간호", "total_monthly_work_hours": 208},
                {"name": "조간호사", "staff_id": 115, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 186},
                {"name": "문간호사", "staff_id": 116, "grade": 4, "grade_name": "간호사", "position": "간호", "total_monthly_work_hours": 198},
                {"name": "배간호사", "staff_id": 117, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 194},
                {"name": "서간호사", "staff_id": 118, "grade": 1, "grade_name": "수간호사", "position": "간호", "total_monthly_work_hours": 207},
                {"name": "허간호사", "staff_id": 119, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 199},
                {"name": "노간호사", "staff_id": 120, "grade": 5, "grade_name": "신규간호사", "position": "간호", "total_monthly_work_hours": 182},
                {"name": "류간호사", "staff_id": 121, "grade": 2, "grade_name": "주임간호사", "position": "간호", "total_monthly_work_hours": 203},
                {"name": "민간호사", "staff_id": 122, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 188},
                {"name": "백간호사", "staff_id": 123, "grade": 4, "grade_name": "간호사", "position": "간호", "total_monthly_work_hours": 195},
                {"name": "하간호사", "staff_id": 124, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 192},
                {"name": "안간호사", "staff_id": 125, "grade": 5, "grade_name": "신규간호사", "position": "간호", "total_monthly_work_hours": 183}
]

        },
        "custom_rules": {
            "shifts": shifts,
            "shift_hours": shift_hours
        }
    }
    
    print(f"\n=== 테스트 {test_id} 시작 ===")
    print(f"요청 데이터: {json.dumps(nursing_request, ensure_ascii=False, indent=2)}")
    
    response = send_request(nursing_request)
    
    if response:
        if response.get("status") == "ok":
            print("[SUCCESS] 근무표 생성 성공")
            # 응답 저장 (예: 파일로)
            output_file = f"./client_data/test_result_custom_{test_id}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
            print(f"결과가 {output_file}에 저장되었습니다.")
        else:
            print("[FAIL] 근무표 생성 실패:", response.get("message", "알 수 없는 오류"))
    else:
        print("[FAIL] 응답 없음")

if __name__ == "__main__":
    # 서버가 실행 중인지 확인 (테스트 전에 약간의 지연)
    time.sleep(1)  # 서버 시작 후 대기
    
    # 테스트 1: ['A', 'B', 'C', 'O'] with {'A':8, 'B':8, 'C':8, 'O':0}
    test_custom_shift(1, ['A', 'B', 'C', 'O'], {'A':8, 'B':8, 'C':8, 'O':0})
    
    # 테스트 2: ['아침', '낮', '밤', '휴일'] with {'아침':7, '낮':7, '밤':10, '휴일':0}
    test_custom_shift(2, ['아침', '낮', '밤', '휴일'], {'아침':7, '낮':7, '밤':10, '휴일':0})
    
    # 테스트 3: ['D', 'N', 'O'] with {'D':12, 'N':12, 'O':0}
    test_custom_shift(3, ['D', 'N', 'O'], {'D':12, 'N':12, 'O':0})
    
    # 테스트 4: ['Morning', 'Afternoon', 'Evening', 'Night', 'Off'] with {'Morning':6, 'Afternoon':6, 'Evening':6, 'Night':6, 'Off':0}
    test_custom_shift(4, ['Morning', 'Afternoon', 'Evening', 'Night', 'Off'], {'Morning':6, 'Afternoon':6, 'Evening':6, 'Night':6, 'Off':0})
    
    # 테스트 5: ['Day', 'Night', 'Off'] with {'Day':8, 'Night':16, 'Off':0}
    test_custom_shift(5, ['Day', 'Night', 'Off'], {'Day':8, 'Night':16, 'Off':0})
    
    # 테스트 6: ['Shift1', 'Shift2', 'Off'] with {'Shift1':9, 'Shift2':9, 'Off':0}
    test_custom_shift(6, ['Shift1', 'Shift2', 'Off'], {'Shift1':9, 'Shift2':9, 'Off':0})    

    # 테스트 8: ['D', 'E', 'N', 'O'] with {'D':8, 'E':8, 'N':8, 'O':0}
    test_custom_shift(8, ['D', 'E', 'N', 'O'], {'D':8, 'E':8, 'N':8, 'O':0})
    
    # 테스트 9: ['FullDay', 'Off'] with {'FullDay':24, 'Off':0}
    test_custom_shift(9, ['FullDay', 'Off'], {'FullDay':24, 'Off':0})
    
    # 테스트 10: ['PartTime1', 'PartTime2', 'PartTime3', 'Off'] with {'PartTime1':4, 'PartTime2':4, 'PartTime3':4, 'Off':0}
    test_custom_shift(10, ['PartTime1', 'PartTime2', 'PartTime3', 'Off'], {'PartTime1':4, 'PartTime2':4, 'PartTime3':4, 'Off':0})