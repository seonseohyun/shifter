#!/usr/bin/env python3
import socket
import json
import time

HOST = '127.0.0.1'
PORT = 6001

# 소방 직군 테스트 데이터 (20명)
firefighter_request = {
    "position": "소방",
    "staff_data": {
        "staff": [
            {"name": "김소방관", "staff_id": 201, "grade": 3, "grade_name": "정규소방사", "position": "소방", "total_monthly_work_hours": 192},
            {"name": "박소방관", "staff_id": 202, "grade": 2, "grade_name": "선임소방사", "position": "소방", "total_monthly_work_hours": 200},
            {"name": "이소방관", "staff_id": 203, "grade": 1, "grade_name": "소방장", "position": "소방", "total_monthly_work_hours": 210},
            {"name": "최소방관", "staff_id": 204, "grade": 3, "grade_name": "정규소방사", "position": "소방", "total_monthly_work_hours": 192},
            {"name": "정소방관", "staff_id": 205, "grade": 3, "grade_name": "정규소방사", "position": "소방", "total_monthly_work_hours": 192},
            {"name": "강소방관", "staff_id": 206, "grade": 2, "grade_name": "선임소방사", "position": "소방", "total_monthly_work_hours": 200},
            {"name": "조소방관", "staff_id": 207, "grade": 3, "grade_name": "정규소방사", "position": "소방", "total_monthly_work_hours": 192},
            {"name": "윤소방관", "staff_id": 208, "grade": 1, "grade_name": "소방장", "position": "소방", "total_monthly_work_hours": 210},
            {"name": "장소방관", "staff_id": 209, "grade": 3, "grade_name": "정규소방사", "position": "소방", "total_monthly_work_hours": 192},
            {"name": "임소방관", "staff_id": 210, "grade": 2, "grade_name": "선임소방사", "position": "소방", "total_monthly_work_hours": 200},
            {"name": "한소방관", "staff_id": 211, "grade": 3, "grade_name": "정규소방사", "position": "소방", "total_monthly_work_hours": 192},
            {"name": "오소방관", "staff_id": 212, "grade": 3, "grade_name": "정규소방사", "position": "소방", "total_monthly_work_hours": 192},
            {"name": "서소방관", "staff_id": 213, "grade": 2, "grade_name": "선임소방사", "position": "소방", "total_monthly_work_hours": 200},
            {"name": "노소방관", "staff_id": 214, "grade": 3, "grade_name": "정규소방사", "position": "소방", "total_monthly_work_hours": 192},
            {"name": "배소방관", "staff_id": 215, "grade": 1, "grade_name": "소방장", "position": "소방", "total_monthly_work_hours": 210},
            {"name": "문소방관", "staff_id": 216, "grade": 3, "grade_name": "정규소방사", "position": "소방", "total_monthly_work_hours": 192},
            {"name": "송소방관", "staff_id": 217, "grade": 2, "grade_name": "선임소방사", "position": "소방", "total_monthly_work_hours": 200},
            {"name": "신소방관", "staff_id": 218, "grade": 3, "grade_name": "정규소방사", "position": "소방", "total_monthly_work_hours": 192},
            {"name": "안소방관", "staff_id": 219, "grade": 3, "grade_name": "정규소방사", "position": "소방", "total_monthly_work_hours": 192},
            {"name": "양소방관", "staff_id": 220, "grade": 2, "grade_name": "선임소방사", "position": "소방", "total_monthly_work_hours": 200}
        ]
    },
    "shift_type": 3,
    "change_requests": []
}

def test_firefighter():
    print("=== 소방 직군 근무표 생성 테스트 ===")
    start_time = time.time()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        request_json = json.dumps(firefighter_request, ensure_ascii=False)
        sock.sendall(request_json.encode('utf-8'))
        
        response = b""
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            response += chunk
    
    end_time = time.time()
    duration = end_time - start_time
    
    try:
        response_json = json.loads(response.decode('utf-8'))
        status = response_json.get('status', 'unknown')
        
        print(f"응답 시간: {duration:.2f}초")
        print(f"상태: {status}")
        
        if status == 'ok':
            print("✅ 소방 직군 근무표 생성 성공!")
            
            # D24-O-O 패턴 확인
            schedule = response_json.get('schedule', {})
            pattern_violations = 0
            
            # 첫 번째 소방관의 패턴 확인
            staff_schedule = {}
            for date, day_schedule in schedule.items():
                for shift in day_schedule:
                    for person in shift['people']:
                        if person['staff_id'] == '201':  # 김소방관
                            staff_schedule[date] = shift['shift']
                            break
            
            # 3일 주기 패턴 검증 (간단한 체크)
            dates = sorted(staff_schedule.keys())
            d24_count = sum(1 for shift in staff_schedule.values() if shift == 'D24')
            off_count = sum(1 for shift in staff_schedule.values() if shift == 'O')
            
            print(f"📊 김소방관 - D24: {d24_count}회, 오프: {off_count}회")
            print(f"📊 D24:오프 비율 = 1:{off_count/max(d24_count, 1):.1f} (이상적: 1:2)")
            
            print(schedule)


        else:
            print("❌ 소방 직군 근무표 생성 실패")
            print(f"오류: {response_json}")
            
    except Exception as e:
        print(f"응답 파싱 오류: {e}")
        print(f"응답 데이터: {response.decode('utf-8')[:500]}...")

if __name__ == "__main__":
    test_firefighter()