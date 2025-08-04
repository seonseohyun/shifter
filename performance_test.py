#!/usr/bin/env python3
import socket
import json
import time

HOST = '127.0.0.1'
PORT = 6001

# 테스트 데이터 (더 작은 데이터셋으로 성능 확인)
request_data = {
    "staff_data": {
        "staff": [
            {"name": "박주영", "staff_id": 101, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 180},
            {"name": "최정환", "staff_id": 102, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 180},
            {"name": "문재윤", "staff_id": 103, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 180},
            {"name": "선서현", "staff_id": 104, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 180},
            {"name": "박경태", "staff_id": 105, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 180},
            {"name": "유희라", "staff_id": 106, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 180},
            {"name": "김유범", "staff_id": 107, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 180},
            {"name": "박서은", "staff_id": 108, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 180},
            {"name": "김대업", "staff_id": 109, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 180},
            {"name": "유예솜", "staff_id": 110, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 180}
        ]
    },
    "shift_type": 3,
    "change_requests": []
}

def test_performance():
    start_time = time.time()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        request_json = json.dumps(request_data, ensure_ascii=False)
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
            print("✅ 근무표 생성 성공!")
        else:
            print("❌ 근무표 생성 실패")
            print(f"오류: {response_json}")
            
    except Exception as e:
        print(f"응답 파싱 오류: {e}")
        print(f"응답 데이터: {response.decode('utf-8')[:200]}...")

if __name__ == "__main__":
    print("=== 성능 테스트 시작 (10명 직원) ===")
    test_performance()