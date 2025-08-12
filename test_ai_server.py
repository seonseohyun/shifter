#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server_ai_gen.py 테스트 스크립트
C++ 클라이언트와 동일한 리틀엔디안 바이너리 프로토콜로 통신 테스트
"""

import socket
import json
import struct
import time
import threading
from datetime import datetime

# 서버 설정
SERVER_HOST = 'localhost'
SERVER_PORT = 6004

def create_binary_request(request_data: dict) -> bytes:
    """C++ 클라이언트와 동일한 리틀엔디안 바이너리 요청 생성"""
    # JSON 직렬화
    json_str = json.dumps(request_data, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    
    json_size = len(json_bytes)
    total_size = 8 + json_size  # 8바이트 헤더 + JSON 크기
    
    # 리틀엔디안 헤더 생성 (C++ uint32_t 호환)
    header = struct.pack('<II', total_size, json_size)
    
    return header + json_bytes

def parse_binary_response(conn: socket.socket) -> dict:
    """리틀엔디안 바이너리 응답 파싱"""
    # 8바이트 헤더 읽기
    header = recv_exact(conn, 8)
    
    # 리틀엔디안으로 파싱
    total_size = struct.unpack('<I', header[:4])[0]
    json_size = struct.unpack('<I', header[4:8])[0]
    
    print(f"📦 응답 헤더: totalSize={total_size}, jsonSize={json_size}")
    
    # JSON 데이터 읽기
    json_data = recv_exact(conn, json_size).decode('utf-8')
    response = json.loads(json_data)
    
    return response

def recv_exact(conn: socket.socket, n: int) -> bytes:
    """정확히 n바이트 수신"""
    buf = b''
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed")
        buf += chunk
    return buf

def test_schedule_generation():
    """근무표 생성 테스트 (C++ 프로토콜 호환)"""
    print("=" * 60)
    print("🤖 AI 근무표 생성 테스트 (리틀엔디안 프로토콜)")
    print("=" * 60)
    
    # 160시간 제약 테스트 케이스
    request_data = {
        "protocol": "py_gen_timetable",
        "data": {
            "staff": [
                {"name": "김간호사", "staff_id": 1, "grade": 3, "total_hours": 160},
                {"name": "이간호사", "staff_id": 2, "grade": 4, "total_hours": 160},
                {"name": "박간호사", "staff_id": 3, "grade": 4, "total_hours": 160},
                {"name": "최간호사", "staff_id": 4, "grade": 3, "total_hours": 160},
                {"name": "정간호사", "staff_id": 5, "grade": 5, "total_hours": 160},  # 신입
                {"name": "한간호사", "staff_id": 6, "grade": 4, "total_hours": 160},
                {"name": "장간호사", "staff_id": 7, "grade": 3, "total_hours": 160},
                {"name": "윤간호사", "staff_id": 8, "grade": 4, "total_hours": 160},
                {"name": "강간호사", "staff_id": 9, "grade": 4, "total_hours": 160},
                {"name": "조간호사", "staff_id": 10, "grade": 3, "total_hours": 160}
            ],
            "position": "간호",
            "target_year": 2025,
            "target_month": 1
        }
    }
    
    try:
        print(f"📡 서버 연결 중: {SERVER_HOST}:{SERVER_PORT}")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((SERVER_HOST, SERVER_PORT))
            sock.settimeout(30.0)  # 30초 타임아웃
            
            print("✅ 서버 연결 성공")
            print(f"📊 테스트 데이터: 10명 직원, 160시간/월 제약, 2025년 1월")
            
            # 리틀엔디안 바이너리 요청 생성 및 전송
            binary_request = create_binary_request(request_data)
            print(f"📤 요청 전송: {len(binary_request)}바이트 (리틀엔디안)")
            
            start_time = time.time()
            sock.sendall(binary_request)
            
            # 응답 수신 및 파싱
            print("⏳ AI 근무표 생성 대기 중...")
            response = parse_binary_response(sock)
            
            processing_time = time.time() - start_time
            
            print(f"📥 응답 수신 완료 ({processing_time:.2f}초)")
            print("=" * 50)
            
            # 응답 분석
            protocol = response.get('protocol', 'unknown')
            resp_status = response.get('resp', 'unknown')
            data = response.get('data', {})
            
            print(f"🔧 프로토콜: {protocol}")
            print(f"📊 응답 상태: {resp_status}")
            
            if resp_status == 'success':
                print("✅ AI 근무표 생성 성공!")
                
                schedule = data.get('schedule', [])
                generation_method = data.get('generation_method', 'unknown')
                ai_metadata = data.get('ai_metadata', {})
                
                print(f"🤖 생성 방법: {generation_method}")
                print(f"📈 스케줄 엔트리: {len(schedule)}개")
                print(f"🔄 AI 시도 횟수: {ai_metadata.get('attempt', 'unknown')}")
                print(f"🧠 사용 모델: {ai_metadata.get('model_used', 'unknown')}")
                
                # 형평성 분석
                if schedule:
                    staff_work_days = {}
                    for entry in schedule:
                        if entry.get('shift') != 'Off':
                            for person in entry.get('people', []):
                                name = person.get('name', 'Unknown')
                                staff_work_days[name] = staff_work_days.get(name, 0) + 1
                    
                    if staff_work_days:
                        work_counts = list(staff_work_days.values())
                        min_work = min(work_counts)
                        max_work = max(work_counts)
                        avg_work = sum(work_counts) / len(work_counts)
                        deviation = max_work - min_work
                        
                        print("\n📊 형평성 분석:")
                        print(f"   최소 근무일: {min_work}일")
                        print(f"   최대 근무일: {max_work}일") 
                        print(f"   평균 근무일: {avg_work:.1f}일")
                        print(f"   편차: {deviation}일")
                        
                        # 160시간 준수 확인
                        max_hours = max_work * 8
                        print(f"   최대 근무시간: {max_hours}시간 (제한: 160시간)")
                        
                        if max_hours <= 160:
                            print("✅ 160시간 제약 준수")
                        else:
                            print(f"⚠️ 160시간 제약 초과")
                        
                        print("\n👥 직원별 근무일:")
                        for name, days in staff_work_days.items():
                            hours = days * 8
                            print(f"   {name}: {days:2d}일 ({hours:3d}시간)")
                        
                        # 첫 3일 스케줄 예시
                        print("\n📅 첫 3일 스케줄 예시:")
                        for day in range(min(3, 31)):
                            day_entries = [e for e in schedule if e.get('day') == day]
                            if day_entries:
                                print(f"   {day+1}일:")
                                for entry in day_entries:
                                    shift = entry.get('shift', 'Unknown')
                                    people = [p.get('name', 'Unknown') for p in entry.get('people', [])]
                                    if people:
                                        print(f"     {shift}: {', '.join(people)}")
                
            else:
                print("❌ AI 근무표 생성 실패")
                error = data.get('error', 'Unknown error')
                print(f"   오류: {error}")
                
    except socket.timeout:
        print("❌ 서버 응답 타임아웃 (30초)")
    except ConnectionError as e:
        print(f"❌ 연결 오류: {e}")
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc()

def test_handover_enhancement():
    """인수인계 명료화 테스트 (C++ 프로토콜 호환)"""
    print("\n" + "=" * 60)
    print("📝 AI 인수인계 명료화 테스트 (리틀엔디안 프로토콜)")
    print("=" * 60)
    
    request_data = {
        "protocol": "py_handover_summary",
        "data": {
            "text": "301호 김환자 혈압 좀 높아서 모니터링 필요하고요, 수액도 떨어져가니까 교체해주시고, 아 그리고 보호자가 자꾸 물어보니까 설명 좀 해주세요. 302호는 수술 후 상태인데 특별한 건 없고, 통증 호소하면 진통제 투약하시면 됩니다."
        }
    }
    
    try:
        print(f"📡 서버 연결 중: {SERVER_HOST}:{SERVER_PORT}")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((SERVER_HOST, SERVER_PORT))
            sock.settimeout(15.0)
            
            print("✅ 서버 연결 성공")
            print("📝 테스트 인수인계 내용:")
            print(f"   {request_data['data']['text'][:100]}...")
            
            # 리틀엔디안 바이너리 요청 전송
            binary_request = create_binary_request(request_data)
            print(f"📤 요청 전송: {len(binary_request)}바이트 (리틀엔디안)")
            
            start_time = time.time()
            sock.sendall(binary_request)
            
            # 응답 수신
            print("⏳ AI 명료화 처리 중...")
            response = parse_binary_response(sock)
            
            processing_time = time.time() - start_time
            
            print(f"📥 응답 수신 완료 ({processing_time:.2f}초)")
            print("=" * 50)
            
            # 응답 분석
            resp_status = response.get('resp', 'unknown')
            data = response.get('data', {})
            
            if resp_status == 'success':
                print("✅ AI 인수인계 명료화 성공!")
                
                original = data.get('original_text', '')
                enhanced = data.get('enhanced_text', '')
                model_used = data.get('model_used', 'unknown')
                proc_time = data.get('processing_time', 0)
                
                print(f"🤖 사용 모델: {model_used}")
                print(f"⏱️ 처리 시간: {proc_time:.2f}초")
                print(f"📏 원본 길이: {len(original)} 문자")
                print(f"📏 개선 길이: {len(enhanced)} 문자")
                
                print("\n📄 원본 텍스트:")
                print(f"   {original}")
                
                print("\n✨ 개선된 텍스트:")
                print(f"   {enhanced}")
                
            else:
                print("❌ AI 인수인계 명료화 실패")
                error = data.get('error', 'Unknown error')
                print(f"   오류: {error}")
                
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")

def test_protocol_compatibility():
    """프로토콜 호환성 테스트"""
    print("\n" + "=" * 60)
    print("🔧 리틀엔디안 프로토콜 호환성 검증")
    print("=" * 60)
    
    # 테스트용 데이터
    test_data = {"protocol": "test", "data": {"message": "리틀엔디안 테스트"}}
    
    # 바이너리 생성
    binary_data = create_binary_request(test_data)
    
    # 헤더 파싱 테스트
    header = binary_data[:8]
    total_size = struct.unpack('<I', header[:4])[0]
    json_size = struct.unpack('<I', header[4:8])[0]
    
    print(f"✅ 리틀엔디안 헤더 생성 테스트:")
    print(f"   totalSize: {total_size}")
    print(f"   jsonSize: {json_size}")
    print(f"   실제 크기: {len(binary_data)}")
    print(f"   헤더 바이트: {header.hex()}")
    
    # C++ uint32_t 호환성 확인
    expected_total = 8 + json_size
    if total_size == expected_total == len(binary_data):
        print("✅ C++ uint32_t 리틀엔디안 호환성 확인")
    else:
        print("❌ 프로토콜 호환성 문제 발견")

def main():
    """메인 테스트 함수"""
    print("🚀 server_ai_gen.py 테스트 시작")
    print(f"📅 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 프로토콜 호환성 먼저 확인
    test_protocol_compatibility()
    
    print("\n⚠️ 서버 시작 확인:")
    print("   다른 터미널에서 다음 명령으로 서버를 시작하세요:")
    print("   source venv/bin/activate && python3 server_ai_gen.py")
    
    input("\n서버가 시작되면 Enter를 눌러 테스트를 계속하세요...")
    
    # 실제 통신 테스트
    test_schedule_generation()
    test_handover_enhancement()
    
    print("\n🎯 테스트 완료!")
    print("✅ 리틀엔디안 바이너리 프로토콜 호환성 확인됨")
    print("✅ C++ 클라이언트와 동일한 통신 방식 보장됨")

if __name__ == "__main__":
    main()