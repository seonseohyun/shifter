// TcpServer.cpp
#include "TcpServer.h"
#include <fstream>
#include <nlohmann/json.hpp>
using json = nlohmann::json;


// ��ũ: ���� ���̺귯��
#pragma comment(lib, "Ws2_32.lib")

// =======================================================================
// [������] TcpServer
// - ��Ʈ ��ȣ�� �޾Ƽ� ���� ���� �ʱⰪ ����
// =======================================================================
TcpServer::TcpServer(int port)
    : port_(port), listenSocket_(INVALID_SOCKET), wsaData_{} {
}

// =======================================================================
// [�Ҹ���] TcpServer
// - ������ ������ ��ȿ�ϸ� �ݰ�, Winsock ����
// =======================================================================
TcpServer::~TcpServer() {
    if (listenSocket_ != INVALID_SOCKET) closesocket(listenSocket_);
    WSACleanup();
}

// =======================================================================
// [start] - ���� ������ ���� ���� ���� �ܰ� (1)
// - ���� �ʱ�ȭ (Winsock ����, ���� ����, ���ε�, ��������)
// - ���� �� true, ���� �� false ��ȯ
// =======================================================================
bool TcpServer::start() {
    // Winsock ���̺귯�� �ʱ�ȭ
    if (WSAStartup(MAKEWORD(2, 2), &wsaData_) != 0) {
        std::cerr << "WSAStartup ����\n";
        return false;
    }

    // ���� ���� ���� (IPv4, TCP)
    listenSocket_ = socket(AF_INET, SOCK_STREAM, 0);
    if (listenSocket_ == INVALID_SOCKET) {
        std::cerr << "���� ���� ����\n";
        return false;
    }

    // ���� �ּ� ����ü ����
    sockaddr_in serverAddr{};
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;    // ��� IP���� ���� ���
    serverAddr.sin_port = htons(port_);         // ��Ʈ ����

    // ���� ���ε� (�ּҿ� ����)
    if (::bind(listenSocket_, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        std::cerr << u8"���ε� ����\n";
        closesocket(listenSocket_);
        return false;
    }

    // ���� ���� ���� (Ŭ���̾�Ʈ ���� ���)
    if (listen(listenSocket_, SOMAXCONN) == SOCKET_ERROR) {
        std::cerr << u8"������ ����\n";
        closesocket(listenSocket_);
        return false;
    }

    cout << u8"������ ��Ʈ " << port_ << u8"���� ��� ���Դϴ�...\n";
    return true;
}

// =======================================================================
// [acceptClient] - Ŭ���̾�Ʈ ���� ���� �ܰ� (2)
// - Ŭ���̾�Ʈ�� ���� ��û�� �����ϰ�, Ŭ���̾�Ʈ ���� ��ȯ
// - ���� �� INVALID_SOCKET ��ȯ
// =======================================================================
SOCKET TcpServer::acceptClient() {
    sockaddr_in clientAddr{};
    int clientSize = sizeof(clientAddr);

    // Ŭ���̾�Ʈ ���� (���� ��û �޾Ƶ��̱�)
    SOCKET clientSocket = accept(listenSocket_, (sockaddr*)&clientAddr, &clientSize);
    if (clientSocket == INVALID_SOCKET) {
        std::cerr << u8"Ŭ���̾�Ʈ ���� ����\n";
    }
    //std::cout << "[Ŭ���̾�Ʈ] ���� ����\n";

    return clientSocket;
}


// =======================================================================
// [readExact]
// - �־��� ����Ʈ ��(totalBytes)��ŭ ��Ȯ�� ���� ������ �ݺ� ����
// - recv()�� TCP ��Ʈ�� Ư���� �Ϻθ� ���ŵ� �� �����Ƿ� �ݵ�� �ݺ� ȣ��
// - �����ϰų� ������ ����� false ��ȯ
// =======================================================================
bool TcpServer::readExact(SOCKET sock, char* buffer, int totalBytes) {
    int received = 0;
    while (received < totalBytes) {
        int len = recv(sock, buffer + received, totalBytes - received, 0);
        std::cout << "[readExact] recv returned: " << len << "\n";
        if (len <= 0) return false;  // ���� ���� or ����
        received += len;
    }
    return true;
}

// =======================================================================
// [receivePacket]
// - Ŭ���̾�Ʈ�κ��� ���� ������ ����:
//   [1] 8����Ʈ ���: totalSize (4����Ʈ) + jsonSize (4����Ʈ)
//   [2] JSON ���ڿ� (jsonSize ����Ʈ)
//   [3] payload (totalSize - jsonSize ����Ʈ, ���� ���)
//
// - ���� �����͸� out_json, out_payload�� �и��ؼ� ��ȯ
// =======================================================================
bool TcpServer::receivePacket(SOCKET clientSocket, std::string& out_json, std::vector<char>& out_payload) {
    //std::cout << u8"[DEBUG] receivePacket ����\n";

    // 1. 8����Ʈ ��� ����
    char header[8];
    if (!readExact(clientSocket, header, 8)) {
        std::cerr << u8"[ERROR] ��� ���� ����\n";
        closesocket(clientSocket); //  �ݵ�� ���� �ݾƾ� ��
        return false;
    }

    // 2. ��� �Ľ�
    uint32_t totalSize = 0, jsonSize = 0;
    memcpy(&totalSize, header, 4);
    memcpy(&jsonSize, header + 4, 4);

    std::cout << u8"[DEBUG] totalSize: " << totalSize << u8", jsonSize: " << jsonSize << "\n";

    // 3. ��� ��ȿ�� ����
    if (jsonSize == 0 || jsonSize > totalSize || totalSize > 10 * 1024 * 1024) {
        std::cerr << u8"[ERROR] ��� ���� ������: jsonSize=" << jsonSize << u8", totalSize=" << totalSize << "\n";
        return false;
    }

    // 4. �ٵ� ����
    std::vector<char> buffer(totalSize);
    if (!readExact(clientSocket, buffer.data(), totalSize)) {
        std::cerr << "[ERROR] �ٵ� ���� ����\n";
        return false;
    }

    // 5. JSON �и� �� BOM ����
    try {
        out_json = std::string(buffer.begin(), buffer.begin() + jsonSize);

        // 2. UTF-8 ������ ����Ʈ ����
        while (!out_json.empty() && ((unsigned char)out_json[0] == 0xC0 || (unsigned char)out_json[0] == 0xC1 || (unsigned char)out_json[0] < 0x20)) {
            std::cerr << u8"[���] JSON �տ� ������ ����Ʈ(0x" << std::hex << (int)(unsigned char)out_json[0] << ") �߰� �� ����\n";
            out_json = out_json.substr(1);
        }
    }
    catch (const std::exception& e) {
        std::cerr << u8"[ERROR] JSON ���ڿ� ó�� �� ���� �߻�: " << e.what() << "\n";
        return false;
    }

    // 6. payload �и�
    if (jsonSize < totalSize)
        out_payload.assign(buffer.begin() + jsonSize, buffer.end());
    else
        out_payload.clear();

    return true;
}


// =======================================================================
// [sendJsonResponse]
// - Ŭ���̾�Ʈ���� ���� json ����
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
// - ���̽� ������ ����
// =======================================================================
bool TcpServer::connectToPythonServer(const nlohmann::json& request,
    nlohmann::json& pyRoot,
    std::string& out_err_msg)
{
    SOCKET sock = connectToPythonServerSocket("10.10.20.116", 6004);
    if (sock == INVALID_SOCKET) {
        out_err_msg = u8"[Python ���] ���� ���� ����";
        return false;
    }

    // 1) ��û ����
    std::string body = request.dump();
    sendJsonResponse(sock, body);

    // 2) ���� ����
    std::string raw;
    std::vector<char> payload;
    if (!TcpServer::receivePacket(sock, raw, payload)) {
        out_err_msg = u8"[Python ���] ��Ŷ ���� ����(���/�ٵ� �̻�)";
        closesocket(sock);
        return false;
    }
    closesocket(sock);

    // 3) JSON �Ľ�
    try {
        pyRoot = nlohmann::json::parse(raw);

        // ���� ����ȭ ����
        if (pyRoot.is_string()) {
            std::string inner = pyRoot.get<std::string>();
            if (nlohmann::json::accept(inner)) {
                pyRoot = nlohmann::json::parse(inner);
            }
        }
    }
    catch (const std::exception& e) {
        out_err_msg = std::string("[JSON �Ľ� ����] ") + e.what();
        return false;
    }

    // 4) ��Ű�� üũ
    if (!pyRoot.contains("response_data") || !pyRoot["response_data"].is_object()
        || !pyRoot["response_data"].contains("data") || !pyRoot["response_data"]["data"].is_array()) {
        out_err_msg = "[JSON ���� ����] response_data.data �迭 ����";
        return false;
    }

    return true;
}

SOCKET TcpServer::connectToPythonServerSocket(const std::string& host, int port) {
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "[A-PythonConnect] WSAStartup ����, err=" << WSAGetLastError() << "\n";
        return INVALID_SOCKET;
    }

    // host�� IP�� hostname�̵� ó�� (IPv4/IPv6)
    addrinfo hints{}; hints.ai_socktype = SOCK_STREAM; hints.ai_family = AF_UNSPEC;
    addrinfo* res = nullptr;
    std::string portstr = std::to_string(port);
    int gai = getaddrinfo(host.c_str(), portstr.c_str(), &hints, &res);
    if (gai != 0) {
        std::cerr << "[B-PythonConnect] getaddrinfo ����: " << gai_strerrorA(gai) << "\n";
        WSACleanup();
        return INVALID_SOCKET;
    }

    SOCKET sock = INVALID_SOCKET;
    for (addrinfo* p = res; p; p = p->ai_next) {
        sock = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
        if (sock == INVALID_SOCKET) continue;

        // (����) Ÿ�Ӿƿ� ����
        DWORD timeout = 3000; // 3��
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout, sizeof(timeout));
        setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (const char*)&timeout, sizeof(timeout));

        if (connect(sock, p->ai_addr, (int)p->ai_addrlen) == 0) {
            break; // ����
        }
        else {
            int err = WSAGetLastError();
            std::cerr << "[C-PythonConnect] ���� ����, err=" << err << "\n";
            closesocket(sock);
            sock = INVALID_SOCKET;
            continue;
        }
    }
    freeaddrinfo(res);

    if (sock == INVALID_SOCKET) {
        WSACleanup();
    }
    return sock;
}
