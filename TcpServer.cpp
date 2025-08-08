// TcpServer.cpp
#include "TcpServer.h"
#include <fstream>
#include <nlohmann/json.hpp>
using json = nlohmann::json;


// 링크: 윈속 라이브러리
#pragma comment(lib, "Ws2_32.lib")

// =======================================================================
// [생성자] TcpServer
// - 포트 번호를 받아서 서버 소켓 초기값 설정
// =======================================================================
TcpServer::TcpServer(int port)
    : port_(port), listenSocket_(INVALID_SOCKET), wsaData_{} {
}

// =======================================================================
// [소멸자] TcpServer
// - 리스닝 소켓이 유효하면 닫고, Winsock 종료
// =======================================================================
TcpServer::~TcpServer() {
    if (listenSocket_ != INVALID_SOCKET) closesocket(listenSocket_);
    WSACleanup();
}

// =======================================================================
// [start] - 서버 오픈을 위한 소켓 생성 단계 (1)
// - 서버 초기화 (Winsock 시작, 소켓 생성, 바인딩, 리슨까지)
// - 성공 시 true, 실패 시 false 반환
// =======================================================================
bool TcpServer::start() {
    // Winsock 라이브러리 초기화
    if (WSAStartup(MAKEWORD(2, 2), &wsaData_) != 0) {
        std::cerr << "WSAStartup 실패\n";
        return false;
    }

    // 서버 소켓 생성 (IPv4, TCP)
    listenSocket_ = socket(AF_INET, SOCK_STREAM, 0);
    if (listenSocket_ == INVALID_SOCKET) {
        std::cerr << "소켓 생성 실패\n";
        return false;
    }

    // 서버 주소 구조체 설정
    sockaddr_in serverAddr{};
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;    // 모든 IP에서 접속 허용
    serverAddr.sin_port = htons(port_);         // 포트 설정

    // 소켓 바인딩 (주소와 연결)
    if (::bind(listenSocket_, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        std::cerr << u8"바인딩 실패\n";
        closesocket(listenSocket_);
        return false;
    }

    // 리슨 상태 진입 (클라이언트 연결 대기)
    if (listen(listenSocket_, SOMAXCONN) == SOCKET_ERROR) {
        std::cerr << u8"리스닝 실패\n";
        closesocket(listenSocket_);
        return false;
    }

    cout << u8"서버가 포트 " << port_ << u8"에서 대기 중입니다...\n";
    return true;
}

// =======================================================================
// [acceptClient] - 클라이언트 연결 감지 단계 (2)
// - 클라이언트의 연결 요청을 수락하고, 클라이언트 소켓 반환
// - 실패 시 INVALID_SOCKET 반환
// =======================================================================
SOCKET TcpServer::acceptClient() {
    sockaddr_in clientAddr{};
    int clientSize = sizeof(clientAddr);

    // 클라이언트 수락 (연결 요청 받아들이기)
    SOCKET clientSocket = accept(listenSocket_, (sockaddr*)&clientAddr, &clientSize);
    if (clientSocket == INVALID_SOCKET) {
        std::cerr << u8"클라이언트 수락 실패\n";
    }
    //std::cout << "[클라이언트] 연결 성공\n";

    return clientSocket;
}


// =======================================================================
// [readExact]
// - 주어진 바이트 수(totalBytes)만큼 정확히 읽을 때까지 반복 수신
// - recv()는 TCP 스트림 특성상 일부만 수신될 수 있으므로 반드시 반복 호출
// - 실패하거나 연결이 끊기면 false 반환
// =======================================================================
bool TcpServer::readExact(SOCKET sock, char* buffer, int totalBytes) {
    int received = 0;
    while (received < totalBytes) {
        int len = recv(sock, buffer + received, totalBytes - received, 0);
        std::cout << "[readExact] recv returned: " << len << "\n";
        if (len <= 0) return false;  // 연결 끊김 or 오류
        received += len;
    }
    return true;
}

// =======================================================================
// [receivePacket]
// - 클라이언트로부터 다음 순서로 수신:
//   [1] 8바이트 헤더: totalSize (4바이트) + jsonSize (4바이트)
//   [2] JSON 문자열 (jsonSize 바이트)
//   [3] payload (totalSize - jsonSize 바이트, 있을 경우)
//
// - 받은 데이터를 out_json, out_payload로 분리해서 반환
// =======================================================================
bool TcpServer::receivePacket(SOCKET clientSocket, std::string& out_json, std::vector<char>& out_payload) {
    //std::cout << u8"[DEBUG] receivePacket 진입\n";

    // 1. 8바이트 헤더 수신
    char header[8];
    if (!readExact(clientSocket, header, 8)) {
        std::cerr << u8"[ERROR] 헤더 수신 실패\n";
        closesocket(clientSocket); //  반드시 소켓 닫아야 함
        return false;
    }

    // 2. 헤더 파싱
    uint32_t totalSize = 0, jsonSize = 0;
    memcpy(&totalSize, header, 4);
    memcpy(&jsonSize, header + 4, 4);

    std::cout << u8"[DEBUG] totalSize: " << totalSize << u8", jsonSize: " << jsonSize << "\n";

    // 3. 헤더 유효성 검증
    if (jsonSize == 0 || jsonSize > totalSize || totalSize > 10 * 1024 * 1024) {
        std::cerr << u8"[ERROR] 헤더 정보 비정상: jsonSize=" << jsonSize << u8", totalSize=" << totalSize << "\n";
        return false;
    }

    // 4. 바디 수신
    std::vector<char> buffer(totalSize);
    if (!readExact(clientSocket, buffer.data(), totalSize)) {
        std::cerr << "[ERROR] 바디 수신 실패\n";
        return false;
    }

    // 5. JSON 분리 및 BOM 제거
    try {
        out_json = std::string(buffer.begin(), buffer.begin() + jsonSize);

        // 2. UTF-8 비정상 바이트 제거
        while (!out_json.empty() && ((unsigned char)out_json[0] == 0xC0 || (unsigned char)out_json[0] == 0xC1 || (unsigned char)out_json[0] < 0x20)) {
            std::cerr << u8"[경고] JSON 앞에 비정상 바이트(0x" << std::hex << (int)(unsigned char)out_json[0] << ") 발견 → 제거\n";
            out_json = out_json.substr(1);
        }
    }
    catch (const std::exception& e) {
        std::cerr << u8"[ERROR] JSON 문자열 처리 중 예외 발생: " << e.what() << "\n";
        return false;
    }

    // 6. payload 분리
    if (jsonSize < totalSize)
        out_payload.assign(buffer.begin() + jsonSize, buffer.end());
    else
        out_payload.clear();

    return true;
}

// =======================================================================
// [sendJsonResponse]
// - 클라이언트에게 보낼 json 생성
// =======================================================================

void TcpServer::sendJsonResponse(SOCKET sock, const std::string& jsonStr) {
    uint32_t totalSize = static_cast<uint32_t>(jsonStr.size());
    uint32_t jsonSize = totalSize;

    char header[8];
    memcpy(header, &totalSize, 4);
    memcpy(header + 4, &jsonSize, 4);

    send(sock, header, 8, 0);
    send(sock, jsonStr.c_str(), jsonStr.size(), 0);
}

// =======================================================================
// [connectToPythonServer]
// - 파이썬 서버와 연결
// =======================================================================
bool TcpServer::connectToPythonServer(const json& request, json& response, std::string& out_err_msg) {
    const std::string ip = "127.0.0.1";
    const int port = 5555;

    SOCKET sock = connectToPythonServerSocket(ip, port);  // 이름 수정
    if (sock == INVALID_SOCKET) {
        out_err_msg = "[Python 통신] 서버 연결 실패";
        return false;
    }

    bool success = false;
    try {
        // [1] JSON → 문자열 변환 및 전송
        std::string reqStr = request.dump();
        sendJsonResponse(sock, reqStr);  // 반환값 없는 함수이므로 그냥 호출

        // [2] 응답 수신
        std::string resp_json_str;
        std::vector<char> unused_payload;

        if (!receivePacket(sock, resp_json_str, unused_payload)) {
            out_err_msg = "[Python 통신] 응답 수신 실패";
            goto cleanup;
        }

        // [3] 응답 파싱
        try {
            response = json::parse(resp_json_str);
            success = true;
        }
        catch (const std::exception& e) {
            out_err_msg = std::string("[Python 통신] 응답 JSON 파싱 실패: ") + e.what();
        }
    }
    catch (const std::exception& e) {
        out_err_msg = std::string("[Python 통신] 예외 발생: ") + e.what();
    }

cleanup:
    closesocket(sock);
    WSACleanup();
    return success;
}

SOCKET TcpServer::connectToPythonServerSocket(const std::string& ip, int port) {
    WSADATA wsaData;
    SOCKET sock = INVALID_SOCKET;
    sockaddr_in serverAddr{};

    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "[PythonConnect] WSAStartup 실패\n";
        return INVALID_SOCKET;
    }

    sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock == INVALID_SOCKET) {
        std::cerr << "[PythonConnect] 소켓 생성 실패\n";
        WSACleanup();
        return INVALID_SOCKET;
    }

    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(port);
    inet_pton(AF_INET, ip.c_str(), &serverAddr.sin_addr);

    if (connect(sock, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        std::cerr << "[PythonConnect] 연결 실패\n";
        closesocket(sock);
        WSACleanup();
        return INVALID_SOCKET;
    }

    return sock;  // 연결 성공 시 소켓 반환
}
