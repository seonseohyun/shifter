#include <iostream>
#include <string>
#include <vector>
#include <nlohmann/json.hpp>

#ifdef _WIN32
    #define _WINSOCK_DEPRECATED_NO_WARNINGS
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <windows.h>
    #pragma comment(lib, "ws2_32.lib")
    typedef SOCKET socket_t;
#else
    #include <sys/socket.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    typedef int socket_t;
    #define INVALID_SOCKET -1
    #define SOCKET_ERROR -1
    #define closesocket close
#endif

using json = nlohmann::json;

class SchedulerTestClient {
private:
    socket_t sock;
    
public:
    SchedulerTestClient() : sock(INVALID_SOCKET) {
#ifdef _WIN32
        WSADATA wsaData;
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
            throw std::runtime_error("WSAStartup failed");
        }
        SetConsoleOutputCP(CP_UTF8);
        SetConsoleCP(CP_UTF8);
#endif
    }
    
    ~SchedulerTestClient() {
        if (sock != INVALID_SOCKET) {
            closesocket(sock);
        }
#ifdef _WIN32
        WSACleanup();
#endif
    }
    
    void connect_to_server(const std::string& host = "127.0.0.1", int port = 6004) {
        sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock == INVALID_SOCKET) {
            throw std::runtime_error("socket() failed");
        }
        
        sockaddr_in server_addr{};
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(port);
        
#ifdef _WIN32
        server_addr.sin_addr.s_addr = inet_addr(host.c_str());
#else
        inet_pton(AF_INET, host.c_str(), &server_addr.sin_addr);
#endif
        
        if (::connect(sock, (sockaddr*)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
            throw std::runtime_error("connect() failed");
        }
        
        std::cout << u8"Python 스케줄러 서버에 연결됨! (" << host << ":" << port << ")" << std::endl;
    }
    
    std::string send_request(const json& request) {
        std::string json_str = request.dump();
        
        std::cout << u8"\\n전송할 요청:" << std::endl;
        std::cout << request.dump(2) << std::endl;
        
        // JSON 데이터 전송
        int bytes_sent = send(sock, json_str.c_str(), (int)json_str.length(), 0);
        if (bytes_sent == SOCKET_ERROR) {
            throw std::runtime_error("send() failed");
        }
        
        // 연결 종료 신호
        shutdown(sock, 1); // 송신 종료
        
        // 응답 수신
        std::string response;
        char buffer[4096];
        int bytes_received;
        
        while ((bytes_received = recv(sock, buffer, sizeof(buffer) - 1, 0)) > 0) {
            buffer[bytes_received] = '\0';
            response += buffer;
        }
        
        return response;
    }
    
    json create_test_request() {
        // 12명의 간호사 데이터 생성
        json staff_list = json::array();
        
        std::vector<std::string> nurse_names = {
            "김간호사", "이간호사", "박간호사", "최간호사", 
            "정간호사", "강간호사", "조간호사", "윤간호사",
            "장간호사", "임간호사", "한간호사", "오간호사"
        };
        
        for (int i = 0; i < 12; i++) {
            json nurse = {
                {"name", nurse_names[i]},
                {"staff_id", 1001 + i},
                {"grade", (i < 2) ? 5 : 3}, // 처음 2명은 신규(grade 5)
                {"total_monthly_work_hours", 195}
            };
            staff_list.push_back(nurse);
        }
        
        // py_gen_timetable 요청 생성
        json request = {
            {"protocol", "py_gen_timetable"},
            {"data", {
                {"staff_data", {
                    {"staff", staff_list}
                }},
                {"position", "간호"},
                {"target_month", "2025-09"},
                {"custom_rules", {
                    {"shifts", {"Day", "Evening", "Night", "Off"}},
                    {"shift_hours", {
                        {"Day", 8},
                        {"Evening", 8}, 
                        {"Night", 8},
                        {"Off", 0}
                    }},
                    {"night_shifts", {"Night"}},
                    {"off_shifts", {"Off"}}
                }}
            }}
        };
        
        return request;
    }
    
    void test_scheduler() {
        try {
            connect_to_server();
            
            std::cout << u8"\\n12명 간호사 시프트 스케줄 생성 요청..." << std::endl;
            
            json request = create_test_request();
            std::string response_str = send_request(request);
            
            std::cout << u8"\\n=== 서버 응답 ===" << std::endl;
            
            try {
                json response = json::parse(response_str);
                std::cout << response.dump(2) << std::endl;
                
                // 결과 분석
                if (response.contains("protocol") && response["protocol"] == "py_gen_schedule") {
                    if (response.contains("resp")) {
                        std::string resp = response["resp"];
                        if (resp == "success") {
                            std::cout << u8"\\n✅ 스케줄 생성 성공!" << std::endl;
                            if (response.contains("data") && response["data"].is_array()) {
                                int schedule_count = response["data"].size();
                                std::cout << u8"생성된 스케줄 항목 수: " << schedule_count << std::endl;
                                
                                // 첫 번째 스케줄 항목 예시 출력
                                if (schedule_count > 0) {
                                    auto first_item = response["data"][0];
                                    std::cout << u8"\\n첫 번째 스케줄 예시:" << std::endl;
                                    std::cout << u8"날짜: " << first_item["date"].get<std::string>() << std::endl;
                                    std::cout << u8"시프트: " << first_item["shift"].get<std::string>() << std::endl;
                                    std::cout << u8"근무시간: " << first_item["hours"].get<int>() << u8"시간" << std::endl;
                                    std::cout << u8"배정된 인원 수: " << first_item["people"].size() << u8"명" << std::endl;
                                }
                            }
                        } else if (resp == "fail") {
                            std::cout << u8"\\n❌ 스케줄 생성 실패!" << std::endl;
                        }
                    }
                }
                
            } catch (const json::parse_error& e) {
                std::cout << u8"JSON 파싱 실패, Raw 응답:" << std::endl;
                std::cout << response_str << std::endl;
            }
            
        } catch (const std::exception& e) {
            std::cerr << u8"테스트 오류: " << e.what() << std::endl;
        }
    }
};

int main() {
    try {
        SchedulerTestClient client;
        client.test_scheduler();
        
        std::cout << u8"\\n테스트 완료. 엔터키를 눌러 종료하세요..." << std::endl;
        std::cin.get();
        
    } catch (const std::exception& e) {
        std::cerr << u8"프로그램 오류: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}