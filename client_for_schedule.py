import socket
import json

HOST = '127.0.0.1'  # Python 서버 주소
PORT = 6001         # Python 서버 포트

# JSON 요청 데이터
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
            {"name": "유예솜", "staff_id": 110, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 180},
            {"name": "고준영", "staff_id": 111, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 180},
            {"name": "하진영", "staff_id": 112, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 180},
            {"name": "오장관", "staff_id": 113, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 200},
            {"name": "윤진영", "staff_id": 114, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 200},
            {"name": "한경식", "staff_id": 115, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 200},
            {"name": "한현희", "staff_id": 116, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 200},
            {"name": "정종옥", "staff_id": 117, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 200},
            {"name": "양성규", "staff_id": 118, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 200},
            {"name": "김화백", "staff_id": 119, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 200},
            {"name": "이병희", "staff_id": 120, "grade": 1, "grade_name": "제일높은직급", "total_monthly_work_hours": 220}
        ]
    },
    "shift_type": 3,
    "change_requests": [
        {
            "staff_id": 101,
            "date": "2025-08-12",
            "desired_shift": "N",
            "original_shift": "D"
        }
    ]
}

# 서버로 보내고 응답 받기
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

    response_json = response.decode('utf-8')
    print("[서버 응답]:")
    print(response_json)
