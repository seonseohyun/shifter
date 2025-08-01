#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <ws2tcpip.h>
#include <iostream>
#include <string>
#include <vector>
#include <nlohmann/json.hpp>
#include <windows.h>

#pragma comment(lib, "ws2_32.lib")

using json = nlohmann::json;

// 서버와 동일한 WorkItem 구조체
struct WorkItem {
    std::string jsonStr;
    std::vector<char> payload;
};

// 정확한 바이트 수 수신 함수
std::vector<char> recvExact(SOCKET sock, size_t size) {
    std::vector<char> buffer(size);
    size_t totalRead = 0;

    while (totalRead < size) {
        int bytesRead = recv(sock, buffer.data() + totalRead, (int)(size - totalRead), 0);
        if (bytesRead == SOCKET_ERROR) throw std::runtime_error("recv() failed");
        if (bytesRead == 0) throw std::runtime_error("Connection closed");
        totalRead += bytesRead;
    }
    return buffer;
}

// WorkItem 수신
WorkItem receiveWorkItem(SOCKET sock) {
    auto header = recvExact(sock, 8);

    int totalLen = *reinterpret_cast<int*>(header.data());
    int jsonLen = *reinterpret_cast<int*>(header.data() + 4);
    int payloadLen = totalLen - jsonLen;

    auto jsonBytes = recvExact(sock, jsonLen);
    std::string jsonStr(jsonBytes.begin(), jsonBytes.end());

    std::vector<char> payload;
    if (payloadLen > 0) {
        payload = recvExact(sock, payloadLen);
    }
    return WorkItem{ jsonStr, payload };
}

// WorkItem 전송
void sendWorkItem(SOCKET sock, const WorkItem& item) {
    int jsonLen = (int)item.jsonStr.size();
    int payloadLen = (int)item.payload.size();
    int totalLen = jsonLen + payloadLen;

    char header[8];
    memcpy(header, &totalLen, 4);
    memcpy(header + 4, &jsonLen, 4);

    send(sock, header, 8, 0);
    send(sock, item.jsonStr.c_str(), jsonLen, 0);
    if (payloadLen > 0) {
        send(sock, item.payload.data(), payloadLen, 0);
    }
}

int main() {
    // UTF-8 콘솔 설정
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
    
    WSADATA wsaData;
    SOCKET sock = INVALID_SOCKET;

    try {
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
            throw std::runtime_error("WSAStartup failed");

        sockaddr_in serverAddr{};
        serverAddr.sin_family = AF_INET;
        serverAddr.sin_port = htons(5556); // 서버 포트
        serverAddr.sin_addr.s_addr = inet_addr("127.0.0.1"); // 로컬호스트로 접속

        sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (sock == INVALID_SOCKET)
            throw std::runtime_error("socket() failed");

        if (connect(sock, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR)
            throw std::runtime_error("connect() failed");

        std::cout << u8"서버에 연결됨!" << std::endl;

        // 테스트 메뉴
        int choice;
        std::cout << u8"\n테스트할 기능을 선택하세요:" << std::endl;
        std::cout << u8"1. Hello 프로토콜 테스트" << std::endl;
        std::cout << u8"2. Insert 프로토콜 테스트" << std::endl;
        std::cout << u8"3. GetSchedule 프로토콜 테스트" << std::endl;
        std::cout << u8"4. ChangeShift 프로토콜 테스트 (updateAndExecuteShiftScheduler)" << std::endl;
        std::cout << u8"선택: ";
        std::cin >> choice;

        json requestJson;
        
        switch (choice) {
        case 1:
            // Hello 프로토콜 테스트
            requestJson = {
                {"Protocol", "Hello"}
            };
            break;
            
        case 2:
            // Insert 프로토콜 테스트
            requestJson = {
                {"Protocol", "Insert"},
                {"content", "테스트 데이터"}
            };
            break;
            
        case 3:
            // GetSchedule 프로토콜 테스트
            requestJson = {
                {"Protocol", "GetSchedule"}
            };
            break;
            
        case 4:
            // ChangeShift 프로토콜 테스트 (updateAndExecuteShiftScheduler 함수 테스트)
            {
                std::string staff_id, date_, shift_from, shift_to;
                
                std::cout << u8"\n=== ChangeShift 프로토콜 테스트 ===" << std::endl;
                std::cout << u8"직원 ID를 입력하세요 (예: 1): ";
                std::cin >> staff_id;
                
                std::cout << u8"날짜를 입력하세요 (예: 2025-08-10): ";
                std::cin >> date_;
                
                std::cout << u8"기존 근무 시간대를 입력하세요 (예: D): ";
                std::cin >> shift_from;
                
                std::cout << u8"변경할 근무 시간대를 입력하세요 (예: E): ";
                std::cin >> shift_to;
                
                requestJson = {
                    {"Protocol", "ChangeShift"},
                    {"staff_id", staff_id},
                    {"date_", date_},
                    {"shift_from", shift_from},
                    {"shift_to", shift_to}
                };
                
                std::cout << u8"\n전송할 JSON: " << requestJson.dump(2) << std::endl;
            }
            break;
            
        default:
            std::cout << u8"잘못된 선택입니다. Insert 프로토콜로 기본 설정합니다." << std::endl;
            requestJson = {
                {"Protocol", "Insert"},
                {"content", "기본 테스트 데이터"}
            };
            break;
        }

        // 요청 전송
        WorkItem request{ requestJson.dump(), {} };
        std::cout << u8"\n서버로 요청 전송 중..." << std::endl;
        sendWorkItem(sock, request);

        // 서버 응답 수신
        try {
            WorkItem response = receiveWorkItem(sock);
            std::cout << u8"\n=== 서버 응답 ===" << std::endl;
            
            // JSON 파싱해서 예쁘게 출력
            try {
                json responseJson = json::parse(response.jsonStr);
                std::cout << u8"응답 JSON: " << responseJson.dump(2) << std::endl;
                
                // ChangeShift 응답에 대한 특별 처리
                if (responseJson.contains("Protocol")) {
                    std::string protocol = responseJson["Protocol"];
                    std::cout << u8"\n응답 프로토콜: " << protocol << std::endl;
                    
                    if (protocol == "change_success") {
                        std::cout << u8"✅ 근무교대 요청이 성공적으로 처리되었습니다!" << std::endl;
                    } else if (protocol == "no_solution") {
                        std::cout << u8"❌ 해가 없습니다. 근무교대가 불가능합니다." << std::endl;
                    } else if (protocol == "change_error") {
                        std::cout << u8"❌ 근무교대 처리 중 오류가 발생했습니다." << std::endl;
                    }
                    
                    if (responseJson.contains("message")) {
                        std::cout << u8"메시지: " << responseJson["message"].get<std::string>() << std::endl;
                    }
                }
            } catch (const json::parse_error& e) {
                std::cout << u8"Raw 응답: " << response.jsonStr << std::endl;
            }
            
        } catch (const std::exception& e) {
            std::cout << u8"응답 수신 실패: " << e.what() << std::endl;
        }

        closesocket(sock);
        WSACleanup();
    }
    catch (const std::exception& e) {
        std::cerr << u8"클라이언트 오류: " << e.what() << std::endl;
        if (sock != INVALID_SOCKET) closesocket(sock);
        WSACleanup();
    }

    return 0;
}
