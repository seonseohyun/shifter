#define WIN32_LEAN_AND_MEAN     // ������ ��� �淮ȭ (���ʿ��� macro ����)
#include "TcpServer.h"          // TCP ���� Ŭ���� ���
#include "DBManager.h"          // DB ���� Ŭ���� ���

#include <iostream>
#include <thread>
#include <string>
#include <codecvt> 
#include <locale>
#include <nlohmann/json.hpp>

#define LINE_LABEL(label) cout << "=======================[" << label << "] =======================\n";
#define LINE cout << "=====================================================\n";

using json = nlohmann::json;
using namespace std;

// UTF-8 -> UTF-16 ��ȯ �� ���
static std::wstring_convert<std::codecvt_utf8_utf16<wchar_t>> converter;

// =======================================================================
// [�Լ�] Ŭ���̾�Ʈ �޽�����
// UTF-8 �� �����ڵ�(wstring) ��ȯ �Լ�
// - Ŭ���̾�Ʈ�κ��� ������ ���ڿ��� UTF-8�� ��� �ѱ� ���� ������ ���� ���
// =======================================================================
// �׽�Ʈ
bool ReadExactBytes(SOCKET sock, char* buffer, int totalBytes) {
    int received = 0;
    while (received < totalBytes) {
        int len = recv(sock, buffer + received, totalBytes - received, 0);
        if (len <= 0) return false;
        received += len;
    }
    return true;
}

// =======================================================================
// [�Լ�] Ŭ���̾�Ʈ ��û ó�� �Լ� (������� ����)
// - Ŭ���̾�Ʈ�� ���� �޽����� �����ϰ�, ������ ��ȯ�ϴ� ����
// - �� Ŭ���̾�Ʈ���� �� �Լ��� ���������� �����
// =======================================================================
void handleClient(SOCKET clientSocket) {
    DBManager db;
    std::string jsonStr;
    std::vector<char> payload;

    // [1] JSON + payload ���� (��� ����)
    if (!TcpServer::receivePacket(clientSocket, jsonStr, payload)) {
        std::cerr << u8"[��Ŷ ���� ����] JSON ���� ����\n";
        TcpServer::sendJsonResponse(clientSocket, R"({"PROTOCOL":"UNKNOWN","RESP":"FAIL","MESSAGE":"RECEIVE_FAIL"})");
        closesocket(clientSocket);
        return;
    }

      // [2] JSON ��ȿ�� �˻�
    if (!nlohmann::json::accept(jsonStr)) {
        std::cerr << u8"[JSON ���� ����] ��ȿ���� ���� JSON�Դϴ�.\n";
        TcpServer::sendJsonResponse(clientSocket, R"({"PROTOCOL":"UNKNOWN","RESP":"FAIL","MESSAGE":"INVALID_JSON"})");
        closesocket(clientSocket);
        return;
    }

    try {
        //std::cout << u8"[STEP 1] JSON �Ľ� ����" << std::endl;
        nlohmann::json json = nlohmann::json::parse(jsonStr);
        //std::cout << u8"[STEP 1-OK] JSON �Ľ� ����" << std::endl;

        std::string protocol = json.value("PROTOCOL", "");
        //std::cout << u8"[STEP 2] ��������: " << protocol << std::endl;

        //if (protocol == u8"LOGIN") {
        //    LINE_LABEL("LOGIN") //����
        //    db.connect(); // ��񿬰�

        //    nlohmann::json response = ProtocolHandler::handle_Login(json, db);// �������� ó��
        //    TcpServer::sendJsonResponse(clientSocket, response.dump()); // ���̽� ����
        //    LINE // ��
        //}
        //else {
        //    std::cerr << u8"[����] �� �� ���� ��������: " << protocol << std::endl;
        //    TcpServer::sendJsonResponse(clientSocket, R"({"PROTOCOL":"UNKNOWN","RESP":"FAIL","MESSAGE":"UNSUPPORTED_PROTOCOL"})");
        //}

    }
    catch (const nlohmann::json::parse_error& e) {
        std::cerr << u8"[����] JSON �Ľ� ���� (parse_error): " << e.what() << std::endl;
    }
    catch (const nlohmann::json::type_error& e) {
        std::cerr << u8"[����] JSON Ÿ�� ���� (type_error): " << e.what() << std::endl;
    }
    catch (const std::exception& e) {
        std::cerr << u8"[����] ��Ÿ ����: " << e.what() << std::endl;
    }
}



int main() {
    // �ܼ� �ѱ� ���� ���� ����
    SetConsoleOutputCP(CP_UTF8);                // UTF-8 ��� ���ڵ� ����
    TcpServer server(5556);                     // ��Ʈ 5556���� ���� ����
    DBManager db;

    // DB ���� �õ�
    if (!db.connect()) {
        cout << u8"[����] DB ���� ����!" << endl;
        return 1;
    }

    // ���� ���ε� �� ����
    if (!server.start()) {
        cout << u8"[����] ���� ���ε� �Ǵ� ���� ����!" << endl;
        return 1;
    }

    cout << u8"[����] Ŭ���̾�Ʈ ���� ��� ����..." << endl;

    // Ŭ���̾�Ʈ ���� ����
    while (true) {
        SOCKET clientSocket = server.acceptClient();

        if (clientSocket != INVALID_SOCKET) {
            cout << u8"[����] �� Ŭ���̾�Ʈ �����!" << endl;
            thread th(handleClient, clientSocket);
            th.detach();  // ���������� ����
        }
    }

    return 0;
}
