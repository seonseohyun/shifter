#pragma once
#include <winsock2.h>
#include <string>
#include <vector>
#include <iostream>
#include <nlohmann/json.hpp>
#include <ws2tcpip.h>

using namespace std;

class TcpServer
{
public:
    TcpServer(int port);
    ~TcpServer();

    SOCKET acceptClient();

    bool start();
    static bool readExact(SOCKET sock, char* buffer, int totalBytes);
    static bool receivePacket(SOCKET clientSocket, string& out_json, vector<char>& out_payload);
    static void sendJsonResponse(SOCKET sock, const string& jsonStr);

    // Python 서버 접속용 함수
    static SOCKET connectToPythonServer(const std::string& ip = "10.10.20.116", int port = 6004);

private:
    int port_;
    SOCKET listenSocket_;
    WSADATA wsaData_;
};

