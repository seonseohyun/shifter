#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <ws2tcpip.h>
#include <iostream>
#include <string>
#include <vector>
#include <stdexcept>
#include <nlohmann/json.hpp>
#include <windows.h>

#pragma comment(lib, "ws2_32.lib")



using json = nlohmann::json;

struct WorkItem {
    std::string jsonStr;
    std::vector<char> payload;
};

// 데이터를 정확히 size 바이트만큼 받는 함수
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
std::string toUTF8_safely(const std::string & cp949Str) {
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


int main() {


    WSADATA wsaData;
    SOCKET clientSocket = INVALID_SOCKET;

    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);  // 입력도 필요하면


    try {
        // Winsock 초기화
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
            throw std::runtime_error("WSAStartup failed");

        // 소켓 생성
        clientSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (clientSocket == INVALID_SOCKET)
            throw std::runtime_error("socket() failed");

        // 서버 주소 설정
        sockaddr_in serverAddr{};
        serverAddr.sin_family = AF_INET;
        serverAddr.sin_port = htons(5556);
        inet_pton(AF_INET, "127.0.0.1", &serverAddr.sin_addr);

        // 서버 연결
        if (connect(clientSocket, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR)
            throw std::runtime_error("connect() failed");

        std::cout << u8"서버에 연결되었습니다!" << std::endl;

        // 테스트 1: Hello 프로토콜
        {
            json j;
            j["Protocol"] = toUTF8_safely("Hello");
            WorkItem item{ j.dump(), {} };

            

            sendWorkItem(clientSocket, item);
            std::cout << u8"Hello 프로토콜 전송: " << item.jsonStr << std::endl;

            WorkItem response = receiveWorkItem(clientSocket);
            std::cout << u8"Hello 프로토콜 응답: " << toUTF8_safely(response.jsonStr) << std::endl;
        }

        // 테스트 2: Insert 프로토콜
        {
            json j;
            j["Protocol"] = toUTF8_safely("Insert");
            j["content"] = toUTF8_safely("잇힝~ㅋㅋ");
            WorkItem item{ j.dump(), {} };
            sendWorkItem(clientSocket, item);
            std::cout << u8"Insert 프로토콜 전송: " << item.jsonStr << std::endl;
            
            WorkItem response = receiveWorkItem(clientSocket);
            std::cout << u8"Hello 프로토콜 응답: " << response.jsonStr << std::endl;
        }

        std::cout <<u8"계속하려면 enter, 종료하려면 ctrl+ c ..." << std::endl;
        std::cin.get();

    }
    catch (const std::exception& e) {
        std::cerr << u8"클라이언트 오류: " << e.what() << std::endl;
    }

    // 정리
    if (clientSocket != INVALID_SOCKET) {
        closesocket(clientSocket);
    }
    WSACleanup();

    return 0;
}