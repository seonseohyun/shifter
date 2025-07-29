#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <ws2tcpip.h>
#include <iostream>
#include <string>
#include <vector>
#include <nlohmann/json.hpp>

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

        std::cout << "서버에 연결됨!" << std::endl;

        // 요청용 JSON
        json requestJson = {
            {"Protocol", "Insert"} // 서버 코드 오타 그대로 맞춤
        };

        WorkItem request{ requestJson.dump(), {} };
        sendWorkItem(sock, request);

        // 서버 응답 수신 (옵션)
        try {
            WorkItem response = receiveWorkItem(sock);
            std::cout << "서버 응답: " << response.jsonStr << std::endl;
        } catch (...) {
            std::cout << "응답 없음 또는 수신 실패 (무시 가능)" << std::endl;
        }

        closesocket(sock);
        WSACleanup();
    }
    catch (const std::exception& e) {
        std::cerr << "클라이언트 오류: " << e.what() << std::endl;
        if (sock != INVALID_SOCKET) closesocket(sock);
        WSACleanup();
    }

    return 0;
}
