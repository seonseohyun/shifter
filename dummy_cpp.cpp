#include <iostream>
#include <string>
#include <vector>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdint.h>

const std::string SERVER_HOST = "127.0.0.1";
const int SERVER_PORT = 6004;

class NurseScheduleClient {
private:
    int sockfd;
    
public:
    NurseScheduleClient() : sockfd(-1) {}
    
    ~NurseScheduleClient() {
        disconnect();
    }
    
    bool connect_to_server() {
        // 소켓 생성
        sockfd = socket(AF_INET, SOCK_STREAM, 0);
        if (sockfd < 0) {
            std::cerr << "[ERROR] 소켓 생성 실패" << std::endl;
            return false;
        }
        
        // 서버 주소 설정
        struct sockaddr_in server_addr;
        memset(&server_addr, 0, sizeof(server_addr));
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(SERVER_PORT);
        server_addr.sin_addr.s_addr = inet_addr(SERVER_HOST.c_str());
        
        // 서버 연결
        if (connect(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            std::cerr << "[ERROR] 서버 연결 실패 (" << SERVER_HOST << ":" << SERVER_PORT << ")" << std::endl;
            close(sockfd);
            sockfd = -1;
            return false;
        }
        
        std::cout << "[INFO] 서버 연결 성공: " << SERVER_HOST << ":" << SERVER_PORT << std::endl;
        return true;
    }
    
    void disconnect() {
        if (sockfd >= 0) {
            close(sockfd);
            sockfd = -1;
        }
    }
    
    std::string send_request(const std::string& json_request) {
        if (sockfd < 0) {
            std::cerr << "[ERROR] 서버 연결되지 않음" << std::endl;
            return "";
        }
        
        // JSON 데이터 전송
        ssize_t sent_bytes = send(sockfd, json_request.c_str(), json_request.length(), 0);
        if (sent_bytes < 0) {
            std::cerr << "[ERROR] 데이터 전송 실패" << std::endl;
            return "";
        }
        
        std::cout << "[INFO] 요청 전송 완료: " << sent_bytes << " bytes" << std::endl;
        
        // 소켓 쓰기 종료
        shutdown(sockfd, SHUT_WR);
        
        // 응답 수신
        std::string response;
        char buffer[4096];
        ssize_t received;
        
        while ((received = recv(sockfd, buffer, sizeof(buffer) - 1, 0)) > 0) {
            buffer[received] = '\0';
            response += buffer;
        }
        
        if (received < 0) {
            std::cerr << "[ERROR] 응답 수신 실패" << std::endl;
            return "";
        }
        
        std::cout << "[INFO] 응답 수신 완료: " << response.length() << " bytes" << std::endl;
        return response;
    }
};

// 간호사 정보 생성
std::string create_nurse_staff_data() {
    return R"({
        "staff": [
            {"name": "김수련", "staff_id": 1001, "grade": 3, "position": "간호", "total_monthly_work_hours": 195},
            {"name": "이영희", "staff_id": 1002, "grade": 4, "position": "간호", "total_monthly_work_hours": 190},
            {"name": "박민정", "staff_id": 1003, "grade": 5, "position": "간호", "total_monthly_work_hours": 180},
            {"name": "최은영", "staff_id": 1004, "grade": 3, "position": "간호", "total_monthly_work_hours": 200},
            {"name": "정소희", "staff_id": 1005, "grade": 4, "position": "간호", "total_monthly_work_hours": 188},
            {"name": "한미래", "staff_id": 1006, "grade": 2, "position": "간호", "total_monthly_work_hours": 205},
            {"name": "윤서영", "staff_id": 1007, "grade": 4, "position": "간호", "total_monthly_work_hours": 192},
            {"name": "강혜진", "staff_id": 1008, "grade": 3, "position": "간호", "total_monthly_work_hours": 198},
            {"name": "오지은", "staff_id": 1009, "grade": 5, "position": "간호", "total_monthly_work_hours": 175},
            {"name": "송나리", "staff_id": 1010, "grade": 4, "position": "간호", "total_monthly_work_hours": 185},
            {"name": "임지현", "staff_id": 1011, "grade": 2, "position": "간호", "total_monthly_work_hours": 208},
            {"name": "조은서", "staff_id": 1012, "grade": 3, "position": "간호", "total_monthly_work_hours": 195}
        ]
    })";
}

// C++ 프로토콜 요청 생성
std::string create_cpp_protocol_request() {
    std::string staff_data = create_nurse_staff_data();
    
    std::string request = R"({
        "protocol": "gen_schedule",
        "data": {
            "staff_data": )" + staff_data + R"(,
            "position": "간호",
            "target_month": "2025-09",
            "custom_rules": {
                "shifts": ["Day", "Evening", "Night", "Off"],
                "shift_hours": {
                    "Day": 8,
                    "Evening": 8,
                    "Night": 8,
                    "Off": 0
                },
                "night_shifts": ["Night"],
                "off_shifts": ["Off"]
            }
        }
    })";
    
    return request;
}

// 응답 분석
void analyze_response(const std::string& response) {
    std::cout << "\n=== 응답 분석 ===" << std::endl;
    
    if (response.empty()) {
        std::cout << "❌ 응답이 비어있음" << std::endl;
        return;
    }
    
    std::cout << "📦 응답 크기: " << response.length() << " bytes" << std::endl;
    
    // 기본 응답 구조 확인
    if (response.find("\"protocol\"") != std::string::npos) {
        std::cout << "✅ C++ 프로토콜 응답 형식 확인됨" << std::endl;
        
        if (response.find("\"py_gen_schedule\"") != std::string::npos) {
            std::cout << "✅ 응답 프로토콜: py_gen_schedule" << std::endl;
        }
    } else {
        std::cout << "❌ C++ 프로토콜 응답 형식 누락" << std::endl;
    }
    
    // 성공 응답 확인
    if (response.find("\"status\": \"ok\"") != std::string::npos) {
        std::cout << "✅ 스케줄 생성 성공" << std::endl;
        
        // 스케줄 데이터 확인
        if (response.find("\"schedule\"") != std::string::npos) {
            std::cout << "✅ 스케줄 데이터 포함됨" << std::endl;
        }
        
        // 처리 시간 추출
        size_t time_pos = response.find("\"solve_time\": \"");
        if (time_pos != std::string::npos) {
            size_t start = time_pos + 15;
            size_t end = response.find("\"", start);
            if (end != std::string::npos) {
                std::string solve_time = response.substr(start, end - start);
                std::cout << "⏱️ 처리 시간: " << solve_time << std::endl;
            }
        }
        
        // 직원 수 확인
        size_t staff_pos = response.find("\"staff_count\": ");
        if (staff_pos != std::string::npos) {
            size_t start = staff_pos + 16;
            size_t end = response.find(",", start);
            if (end == std::string::npos) end = response.find("}", start);
            if (end != std::string::npos) {
                std::string staff_count = response.substr(start, end - start);
                std::cout << "👥 직원 수: " << staff_count << "명" << std::endl;
            }
        }
        
        // 시프트 식별 확인
        if (response.find("\"shifts_identified\"") != std::string::npos) {
            std::cout << "🔍 시프트 식별 정보 포함됨" << std::endl;
        }
        
    } else if (response.find("\"status\": \"error\"") != std::string::npos || response.find("\"result\": \"생성실패\"") != std::string::npos) {
        std::cout << "❌ 스케줄 생성 실패" << std::endl;
        
        // 오류 사유 추출
        size_t reason_pos = response.find("\"reason\": \"");
        if (reason_pos != std::string::npos) {
            size_t start = reason_pos + 11;
            size_t end = response.find("\"", start);
            if (end != std::string::npos) {
                std::string reason = response.substr(start, end - start);
                std::cout << "📝 오류 사유: " << reason << std::endl;
            }
        }
        
        // 해결 방안 확인
        if (response.find("\"suggestions\"") != std::string::npos) {
            std::cout << "💡 해결 방안 제시됨" << std::endl;
        }
    }
    
    // 신규간호사 야간 근무 확인
    size_t schedule_start = response.find("\"schedule\"");
    if (schedule_start != std::string::npos) {
        std::cout << "\n📊 신규간호사 야간 근무 분석:" << std::endl;
        
        // grade 5 (신규간호사) + Night 시프트 검색
        int newbie_night_count = 0;
        size_t pos = 0;
        
        while ((pos = response.find("\"grade\": 5", pos)) != std::string::npos) {
            // 해당 사람이 Night 시프트에 배정되었는지 확인
            size_t shift_start = response.rfind("\"shift\": \"Night\"", pos);
            size_t people_start = response.rfind("\"people\"", pos);
            
            if (shift_start != std::string::npos && people_start != std::string::npos && shift_start > people_start) {
                newbie_night_count++;
            }
            pos++;
        }
        
        if (newbie_night_count == 0) {
            std::cout << "✅ 신규간호사 야간 근무 금지 제약 정상 작동" << std::endl;
        } else {
            std::cout << "❌ 신규간호사 야간 근무 " << newbie_night_count << "건 발견" << std::endl;
        }
    }
}

int main() {
    std::cout << "=== C++ 더미 클라이언트 - 시프트 스케줄러 테스트 ===" << std::endl;
    std::cout << "대상: Python 서버 (" << SERVER_HOST << ":" << SERVER_PORT << ")" << std::endl;
    std::cout << "직원 수: 12명 간호사" << std::endl;
    std::cout << "시프트: Day(8h), Evening(8h), Night(8h), Off(0h)" << std::endl;
    
    NurseScheduleClient client;
    
    // 서버 연결
    if (!client.connect_to_server()) {
        std::cerr << "서버 연결 실패. 서버가 실행 중인지 확인하세요." << std::endl;
        return 1;
    }
    
    // C++ 프로토콜 요청 생성
    std::string request = create_cpp_protocol_request();
    std::cout << "\n📤 요청 데이터 크기: " << request.length() << " bytes" << std::endl;
    std::cout << "📤 프로토콜: gen_schedule" << std::endl;
    
    // 요청 전송 및 응답 수신
    std::string response = client.send_request(request);
    
    // 연결 종료
    client.disconnect();
    
    // 응답 분석
    if (!response.empty()) {
        analyze_response(response);
        
        std::cout << "\n=== 전체 응답 (첫 500자) ===" << std::endl;
        std::cout << response.substr(0, 500);
        if (response.length() > 500) {
            std::cout << "..." << std::endl;
        }
        std::cout << std::endl;
    } else {
        std::cout << "❌ 응답을 받지 못했습니다." << std::endl;
        return 1;
    }
    
    std::cout << "\n✅ 테스트 완료" << std::endl;
    return 0;
}