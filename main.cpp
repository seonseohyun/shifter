#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <ws2tcpip.h>
#include <iostream>
#include <string>
#include <vector>
#include <stdexcept>
#include <nlohmann/json.hpp>
#include <mysql/mysql.h>

#pragma comment(lib, "ws2_32.lib")

using json = nlohmann::json;

struct WorkItem {
    std::string jsonStr;
    std::vector<char> payload;
};

std::string toUTF8_safely(const std::string& cp949Str) {
    // CP949 → UTF-16
    int wlen = MultiByteToWideChar(949, 0, cp949Str.data(), (int)cp949Str.size(), nullptr, 0);
    if (wlen == 0) return "인코딩 오류";

    std::wstring wide(wlen, 0);
    MultiByteToWideChar(949, 0, cp949Str.data(), (int)cp949Str.size(), &wide[0], wlen);

    // UTF-16 → UTF-8
    int ulen = WideCharToMultiByte(CP_UTF8, 0, wide.data(), wlen, nullptr, 0, nullptr, nullptr);
    std::string utf8(ulen, 0);
    WideCharToMultiByte(CP_UTF8, 0, wide.data(), wlen, &utf8[0], ulen, nullptr, nullptr);

    return utf8;
}

// 데이터를 정확히 size 바이트만큼 받는 함수
std::vector<char> recvExact(SOCKET sock, size_t size) {
    std::vector<char> buffer(size);
    size_t totalRead = 0;

    while (totalRead < size) {
        int bytesRead = recv(sock, buffer.data() + totalRead, (int)(size - totalRead), 0);
        if (bytesRead == SOCKET_ERROR) throw std::runtime_error("recv() failed: " + std::to_string(WSAGetLastError()));
        if (bytesRead == 0) throw std::runtime_error("Connection closed");
        totalRead += bytesRead;
    }
    return buffer;
}

// WorkItem 보내기
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

// WorkItem 받기
WorkItem receiveWorkItem(SOCKET sock) {
    std::cout << "receiveWorkItem 시작" << std::endl;
    auto header = recvExact(sock, 8);
    std::cout << "헤더 수신 완료" << std::endl;

    int totalLen = *reinterpret_cast<int*>(header.data());
    int jsonLen = *reinterpret_cast<int*>(header.data() + 4);
    int payloadLen = totalLen - jsonLen;
    std::cout << "totalLen: " << totalLen << ", jsonLen: " << jsonLen << ", payloadLen: " << payloadLen << std::endl;

    auto jsonBytes = recvExact(sock, jsonLen);
    std::string jsonStr(jsonBytes.begin(), jsonBytes.end());
    std::cout << "JSON 수신: " << jsonStr << std::endl;

    std::vector<char> payload;
    if (payloadLen > 0) {
        payload = recvExact(sock, payloadLen);
        std::cout << "페이로드 수신 완료" << std::endl;
    }
    return WorkItem{ jsonStr, payload };
}

int main() {
    WSADATA wsaData;
    SOCKET listenSocket = INVALID_SOCKET, clientSocket = INVALID_SOCKET;
    

    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);  // 입력도 필요하면

    try {
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
            throw std::runtime_error("WSAStartup failed");

        sockaddr_in serverAddr{};
        serverAddr.sin_family = AF_INET;
        serverAddr.sin_addr.s_addr = INADDR_ANY;
        serverAddr.sin_port = htons(5556);

        listenSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (listenSocket == INVALID_SOCKET)
            throw std::runtime_error("socket() failed");

        if (bind(listenSocket, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR)
            throw std::runtime_error("bind() failed");

        if (listen(listenSocket, SOMAXCONN) == SOCKET_ERROR)
            throw std::runtime_error("listen() failed");

        std::cout << u8"서버 시작, 포트 5556 대기 중..." << std::endl;

        while (true) {
            clientSocket = accept(listenSocket, nullptr, nullptr);
            if (clientSocket == INVALID_SOCKET) {
                std::cerr << u8"accept() failed: " << WSAGetLastError() << std::endl;
                continue; // 새 연결 시도
            }

            std::cout << u8"클라이언트 접속됨" << std::endl;

            MYSQL* conn = nullptr;
            try {
                conn = mysql_init(NULL);
                if (conn == NULL) {
                    throw std::runtime_error(u8"mysql_init() 실패");
                }
                if (mysql_real_connect(conn, "localhost", "master", "1111", "mydb", 3306, NULL, 0) == NULL) {
                    throw std::runtime_error(std::string(u8"mysql_real_connect() 실패: ") + mysql_error(conn));
                }
                mysql_set_character_set(conn, "utf8mb4");

                while (true) {
                    try {
                        WorkItem req = receiveWorkItem(clientSocket);
                        std::cout << u8"받은 JSON: " << req.jsonStr << std::endl;

                        auto j = json::parse(req.jsonStr);
                        if (j.contains("Protocol") && j["Protocol"] == "Hello") {
                            std::cout << u8"Hello 프로토콜 받음!" << std::endl;
                            j["Protocol"] = "hi";
                            WorkItem resp{ j.dump(), {} };
                            sendWorkItem(clientSocket, resp);
                        }
                        
                        //인서트 프로토콜 왔을때 
                        else if (j.contains("Protocol") && j["Protocol"] == "Insert") {

                            std::cout << u8"Insert 프로토콜 받음!" << std::endl;

                            if (j.contains("content"))
                            {
                                std::string content = j["content"];
                                
                                // content 안에 따옴표가 있는 경우를 대비한 간단한 이스케이프 처리
                                size_t pos = 0;
                                while ((pos = content.find("'", pos)) != std::string::npos) {
                                    content.insert(pos, "'");
                                    pos += 2;
                                }

                                // 쿼리 문자열 생성
                                std::string queryStr = "INSERT INTO test (TEST_FIELD) VALUES ('" + content + "');";

                                // const char* 로 변환
                                const char* query = queryStr.c_str();

                                // 출력
                                std::cout << u8"쿼리: " << query << std::endl;
                                

                                if (mysql_query(conn, query)) {
                                    std::cerr << u8"Insert 쿼리 실패: " << mysql_error(conn) << std::endl;
                                }
                                else {
                                    std::cout << u8"Insert 성공!" << std::endl;
                                }
                                
                            }
                            

                            j["Protocol"] = "insert ok";
                            WorkItem resp{ j.dump(), {} };
                            sendWorkItem(clientSocket, resp);

                        }
                    }
                    catch (const std::exception& e) {
                        std::cerr << "클라이언트 처리 중 오류: " << e.what() << std::endl;
                        break; // 클라이언트 연결 종료, 새 연결 대기
                    }
                }
            }
            catch (const std::exception& e) {
                std::cerr << "DB 연결 오류: " << e.what() << std::endl;
            }

            // 클라이언트 연결 정리
            if (conn) {
                mysql_close(conn);
                conn = nullptr;
            }
            if (clientSocket != INVALID_SOCKET) {
                closesocket(clientSocket);
                clientSocket = INVALID_SOCKET;
            }
            std::cout << "클라이언트 연결 종료, 새 연결 대기 중..." << std::endl;
        }
    }
    catch (const std::exception& e) {
        std::cerr << "서버 오류: " << e.what() << std::endl;
    }

    if (clientSocket != INVALID_SOCKET) closesocket(clientSocket);
    if (listenSocket != INVALID_SOCKET) closesocket(listenSocket);
    WSACleanup();

    return 0;
}