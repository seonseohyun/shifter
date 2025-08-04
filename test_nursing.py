#!/usr/bin/env python3
import socket
import json
import time

HOST = '127.0.0.1'
PORT = 6001

# 간호 직군 테스트 데이터 (20명)
nursing_request = {
    "position": "간호",
    "staff_data": {
        "staff": [
            {"name": "김간호사", "staff_id": 101, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 180},
            {"name": "박신규", "staff_id": 102, "grade": 5, "grade_name": "신규간호사", "position": "간호", "total_monthly_work_hours": 160},
            {"name": "이수간호사", "staff_id": 103, "grade": 1, "grade_name": "수간호사", "position": "간호", "total_monthly_work_hours": 190},
            {"name": "최간호사", "staff_id": 104, "grade": 2, "grade_name": "주임간호사", "position": "간호", "total_monthly_work_hours": 185},
            {"name": "정간호사", "staff_id": 105, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 180},
            {"name": "한간호사", "staff_id": 106, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 180},
            {"name": "신신규간호사", "staff_id": 107, "grade": 5, "grade_name": "신규간호사", "position": "간호", "total_monthly_work_hours": 160},
            {"name": "오간호사", "staff_id": 108, "grade": 4, "grade_name": "간호사", "position": "간호", "total_monthly_work_hours": 175},
            {"name": "송간호사", "staff_id": 109, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 180},
            {"name": "윤간호사", "staff_id": 110, "grade": 2, "grade_name": "주임간호사", "position": "간호", "total_monthly_work_hours": 185},
            {"name": "장간호사", "staff_id": 111, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 180},
            {"name": "임간호사", "staff_id": 112, "grade": 4, "grade_name": "간호사", "position": "간호", "total_monthly_work_hours": 175},
            {"name": "홍간호사", "staff_id": 113, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 180},
            {"name": "강간호사", "staff_id": 114, "grade": 2, "grade_name": "주임간호사", "position": "간호", "total_monthly_work_hours": 185},
            {"name": "조간호사", "staff_id": 115, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 180},
            {"name": "문간호사", "staff_id": 116, "grade": 4, "grade_name": "간호사", "position": "간호", "total_monthly_work_hours": 175},
            {"name": "배간호사", "staff_id": 117, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 180},
            {"name": "서간호사", "staff_id": 118, "grade": 1, "grade_name": "수간호사", "position": "간호", "total_monthly_work_hours": 190},
            {"name": "허간호사", "staff_id": 119, "grade": 3, "grade_name": "일반간호사", "position": "간호", "total_monthly_work_hours": 180},
            {"name": "노간호사", "staff_id": 120, "grade": 5, "grade_name": "신규간호사", "position": "간호", "total_monthly_work_hours": 160}
        ]
    },
    "shift_type": 3,
    "change_requests": []
}

def test_nursing():
    print("=== 간호 직군 근무표 생성 테스트 ===")
    start_time = time.time()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        request_json = json.dumps(nursing_request, ensure_ascii=False)
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
            print("✅ 간호 직군 근무표 생성 성공!")
            
            # 신규간호사 야간 근무 확인 (3명)
            schedule = response_json.get('schedule', {})
            newbie_night_counts = {'102': 0, '107': 0, '120': 0}  # 신규간호사 3명
            newbie_names = {'102': '박신규', '107': '신신규간호사', '120': '노간호사'}
            
            for date, day_schedule in schedule.items():
                for shift in day_schedule:
                    if shift['shift'] == 'N':  # 야간 근무
                        for person in shift['people']:
                            if person['staff_id'] in newbie_night_counts:
                                newbie_night_counts[person['staff_id']] += 1
            
            print("📊 신규간호사별 야간 근무 횟수 (모두 0회여야 정상):")
            for staff_id, count in newbie_night_counts.items():
                name = newbie_names[staff_id]
                status = "✅ 정상" if count == 0 else "❌ 위반"
                print(f"   - {name}: {count}회 {status}")
            
        else:
            print("❌ 간호 직군 근무표 생성 실패")
            print(f"오류: {response_json}")
            
    except Exception as e:
        print(f"응답 파싱 오류: {e}")
        print(f"응답 데이터: {response.decode('utf-8')[:500]}...")

if __name__ == "__main__":
    test_nursing()