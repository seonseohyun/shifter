// TcpServer.cpp
#include "TcpServer.h"
#include <fstream>
#include <nlohmann/json.hpp>
using json = nlohmann::json;
#include <algorithm>    // std::max, std::min
#include <string>
#include <vector>
#include <iostream>
#include <cstdio>
#include <winsock2.h>
#pragma comment(lib, "ws2_32.lib")
#define NOMINMAX

#undef min
#undef max

#include <filesystem>  // 파일 시스템 관련
#include <ctime>   
#undef byte


bool createDirIfNotExists(const std::string& path) {
    DWORD attrs = GetFileAttributesA(path.c_str());
    if (attrs != INVALID_FILE_ATTRIBUTES && (attrs & FILE_ATTRIBUTE_DIRECTORY))
        return true; // 이미 폴더 있음
    return CreateDirectoryA(path.c_str(), NULL) || GetLastError() == ERROR_ALREADY_EXISTS;
}

TcpServer::TcpServer(int port)
    : port_(port), listenSocket_(INVALID_SOCKET), wsaData_{} {
}

TcpServer::~TcpServer() {
    if (listenSocket_ != INVALID_SOCKET) closesocket(listenSocket_);
    WSACleanup();
}

bool TcpServer::start() {
    if (WSAStartup(MAKEWORD(2, 2), &wsaData_) != 0) {
        std::cerr << "WSAStartup failed\n";
        return false;
    }

    listenSocket_ = socket(AF_INET, SOCK_STREAM, 0);
    if (listenSocket_ == INVALID_SOCKET) {
        std::cerr << "Socket creation failed\n";
        return false;
    }

    sockaddr_in serverAddr{};
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;
    serverAddr.sin_port = htons(port_);

    if (::bind(listenSocket_, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        std::cerr << "Bind failed\n";
        closesocket(listenSocket_);
        return false;
    }

    if (listen(listenSocket_, SOMAXCONN) == SOCKET_ERROR) {
        std::cerr << "Listen failed\n";
        closesocket(listenSocket_);
        return false;
    }

    std::cout << "Server listening on port " << port_ << "...\n";
    return true;
}

SOCKET TcpServer::acceptClient() {
    sockaddr_in clientAddr{};
    int clientSize = sizeof(clientAddr);

    SOCKET clientSocket = accept(listenSocket_, (sockaddr*)&clientAddr, &clientSize);
    if (clientSocket == INVALID_SOCKET) {
        std::cerr << "Accept failed\n";
    }

    return clientSocket;
}

bool TcpServer::readExact(SOCKET sock, char* buffer, int totalBytes) {
    int received = 0;
    while (received < totalBytes) {
        int len = recv(sock, buffer + received, totalBytes - received, 0);
        if (len <= 0) return false;
        received += len;
    }

    return received == totalBytes;
}

bool TcpServer::receivePacket(SOCKET clientSocket, std::string& out_json, std::vector<char>& out_payload) {
    char header[8];
    if (!readExact(clientSocket, header, 8)) {
        std::cerr << "[ERROR] Failed to read header\n";
        closesocket(clientSocket);
        return false;
    }

    uint32_t totalSize = 0, jsonSize = 0;
    memcpy(&totalSize, header, 4);
    memcpy(&jsonSize, header + 4, 4);

    std::cout << "[DEBUG] totalSize: " << totalSize << ", jsonSize: " << jsonSize << "\n";

    if (jsonSize == 0 || jsonSize > totalSize || totalSize > 10 * 1024 * 1024) {
        std::cerr << "[ERROR] Invalid packet sizes\n";
        return false;
    }

    std::vector<char> buffer(totalSize, 0);
    if (!readExact(clientSocket, buffer.data(), totalSize)) {
        std::cerr << "[ERROR] Failed to read body\n";
        return false;
    }

    try {
        out_json = std::string(buffer.begin(), buffer.begin() + jsonSize);

        int dumpStart = std::max(0, std::min(-3, (int)jsonSize - 1));
        int dumpEnd = std::min((int)jsonSize, 27);
        std::cout << "[DEBUG] Received JSON bytes (" << dumpStart << "-" << dumpEnd - 1 << "):\n";
        for (int i = dumpStart; i < dumpEnd; ++i) {
            if (i == 7) printf("[%02X] ", (unsigned char)buffer[i]);
            else printf("%02X ", (unsigned char)buffer[i]);
            if ((i - dumpStart + 1) % 16 == 0) printf("\n");
        }
        printf("\n");

        std::string cleaned_json;
        cleaned_json.reserve(out_json.size());

        for (size_t i = 0; i < out_json.size();) {
            unsigned char byte = (unsigned char)out_json[i];

            if (byte <= 0x7F) {
                if (byte >= 0x20 || byte == 0x09 || byte == 0x0A || byte == 0x0D) {
                    cleaned_json += (char)byte;
                }
                i++;
            }
            else if (byte >= 0xC2 && byte <= 0xDF && i + 1 < out_json.size()) {
                unsigned char byte2 = (unsigned char)out_json[i + 1];
                if (byte2 >= 0x80 && byte2 <= 0xBF) {
                    cleaned_json += (char)byte;
                    cleaned_json += (char)byte2;
                    i += 2;
                }
                else {
                    i++;
                }
            }
            else if (byte >= 0xE0 && byte <= 0xEF && i + 2 < out_json.size()) {
                unsigned char byte2 = (unsigned char)out_json[i + 1];
                unsigned char byte3 = (unsigned char)out_json[i + 2];
                if (byte2 >= 0x80 && byte2 <= 0xBF && byte3 >= 0x80 && byte3 <= 0xBF) {
                    cleaned_json += (char)byte;
                    cleaned_json += (char)byte2;
                    cleaned_json += (char)byte3;
                    i += 3;
                }
                else {
                    i++;
                }
            }
            else if (byte >= 0xF0 && byte <= 0xF7 && i + 3 < out_json.size()) {
                unsigned char byte2 = (unsigned char)out_json[i + 1];
                unsigned char byte3 = (unsigned char)out_json[i + 2];
                unsigned char byte4 = (unsigned char)out_json[i + 3];
                if (byte2 >= 0x80 && byte2 <= 0xBF && byte3 >= 0x80 && byte3 <= 0xBF && byte4 >= 0x80 && byte4 <= 0xBF) {
                    cleaned_json += (char)byte;
                    cleaned_json += (char)byte2;
                    cleaned_json += (char)byte3;
                    cleaned_json += (char)byte4;
                    i += 4;
                }
                else {
                    i++;
                }
            }
            else {
                i++;
            }
        }

        out_json = cleaned_json;
        //std::cout << "[DEBUG] Cleaned JSON length: " << out_json.size() << " bytes\n";
    }
    catch (const std::exception& e) {
        //std::cerr << "[ERROR] JSON string processing error: " << e.what() << "\n";
        return false;
    }

    if (jsonSize < totalSize)
        out_payload.assign(buffer.begin() + jsonSize, buffer.end());
    else
        out_payload.clear();

    return true;
}

void TcpServer::sendJsonResponse(SOCKET sock, const std::string& jsonStr) {
    uint32_t totalSize = static_cast<uint32_t>(jsonStr.size());
    uint32_t jsonSize = totalSize;

    char header[8];
    memcpy(header, &totalSize, 4);
    memcpy(header + 4, &jsonSize, 4);

    send(sock, header, 8, 0);
    send(sock, jsonStr.c_str(), jsonStr.size(), 0);
}

bool TcpServer::connectToPythonServer(const nlohmann::json& request,
    nlohmann::json& pyRoot, std::string& out_err_msg)
{
    SOCKET sock = connectToPythonServerSocket("10.10.20.116", 6004);
    if (sock == INVALID_SOCKET) { out_err_msg = "[Python] Connection failed"; return false; }

    std::string body = request.dump();
    sendJsonResponse(sock, body);

    std::string raw; std::vector<char> payload;
    if (!TcpServer::receivePacket(sock, raw, payload)) {
        out_err_msg = "[Python] Packet receive failed"; closesocket(sock); return false;
    }
    closesocket(sock);

    // 로그/백업 저장 (생략 가능)
    createDirIfNotExists("receive_data");
    { std::ofstream ofs("receive_data\\last_response.json", std::ios::binary); ofs.write(raw.data(), raw.size()); }

    try {
        pyRoot = nlohmann::json::parse(raw);
        if (pyRoot.is_string() && nlohmann::json::accept(pyRoot.get<std::string>()))
            pyRoot = nlohmann::json::parse(pyRoot.get<std::string>());

        if (pyRoot.contains("response_data") && pyRoot["response_data"].is_object())
            pyRoot = pyRoot["response_data"];

        return true;
    }
    catch (const std::exception& e) {
        out_err_msg = std::string("[JSON parsing error] ") + e.what();
        return false;
    }
}

SOCKET TcpServer::connectToPythonServerSocket(const std::string& host, int port) {
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "[A-PythonConnect] WSAStartup failed, err=" << WSAGetLastError() << "\n";
        return INVALID_SOCKET;
    }

    addrinfo hints{}; hints.ai_socktype = SOCK_STREAM; hints.ai_family = AF_UNSPEC;
    addrinfo* res = nullptr;
    std::string portstr = std::to_string(port);
    int gai = getaddrinfo(host.c_str(), portstr.c_str(), &hints, &res);
    if (gai != 0) {
        WSACleanup();
        return INVALID_SOCKET;
    }

    SOCKET sock = INVALID_SOCKET;
    for (addrinfo* p = res; p; p = p->ai_next) {
        sock = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
        if (sock == INVALID_SOCKET) continue;

        DWORD timeout = 7000;
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout, sizeof(timeout));
        setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (const char*)&timeout, sizeof(timeout));

        if (connect(sock, p->ai_addr, (int)p->ai_addrlen) == 0) {
            break;
        }
        else {
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
