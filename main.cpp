#define WIN32_LEAN_AND_MEAN     // ������ ��� �淮ȭ (���ʿ��� macro ����)
#include "TcpServer.h"          // TCP ���� Ŭ���� ���
#include "DBManager.h"          // DB ���� Ŭ���� ���
#include "ProtocolHandler.h"
#include <iostream>
#include <thread>
#include <string>
#include <codecvt> 
#include <locale>
#include <nlohmann/json.hpp>

#define LINE_LABEL(label) cout << "====================[" << label << "]====================\n";
#define LINE cout << "================================================\n";
#define MIDDLELINE cout << u8"------------------------------------------------\n[ ���� ]\n";

using json = nlohmann::json;
using namespace std;

// UTF-8 -> UTF-16 ��ȯ �� ���
static wstring_convert<codecvt_utf8_utf16<wchar_t>> converter;

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
    string jsonStr;
    vector<char> payload;
    while (1) {
        // [1] JSON + payload ���� (��� ����)
        if (!TcpServer::receivePacket(clientSocket, jsonStr, payload)) {
            cerr << u8"[��Ŷ ���� ����] JSON ���� ����\n";
            TcpServer::sendJsonResponse(clientSocket, R"({"protocol":"unknown","resp":"fail","message":"receive_fail"})");
            closesocket(clientSocket);
            return;
        }

        // [2] JSON ��ȿ�� �˻�
        if (!json::accept(jsonStr)) {
            cerr << u8"[JSON ���� ����] ��ȿ���� ���� JSON�Դϴ�.\n";
            TcpServer::sendJsonResponse(clientSocket, R"({"protocol":"unknown","resp":"fail","message":"invaild_json"})");
            closesocket(clientSocket);
            return;
        }

        try {
            //[STEP 1] JSON �Ľ�
            json json = json::parse(jsonStr);
            //[STEP 2] �������� �Ľ�
            string protocol = json.value("protocol", "");

            if (protocol == u8"login") {
                LINE_LABEL("login") //����
                db.connect(); // DB����
                nlohmann::json response = ProtocolHandler::handle_login(json, db);// �������� ó�� �ڵ鷯�� ����
                TcpServer::sendJsonResponse(clientSocket, response.dump()); // ���̽� ����
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"login_admin") {
                LINE_LABEL("login_admin")
                    db.connect();
                nlohmann::json response = ProtocolHandler::handle_login_admin(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                    cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"shift_change_detail") {
                LINE_LABEL("shift_change_detail")
                    db.connect();
                nlohmann::json response = ProtocolHandler::handle_shift_change_detail(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                    cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"ask_shift_change") {
                LINE_LABEL("ask_shift_change")
                    db.connect();
                nlohmann::json response = ProtocolHandler::handle_ask_shift_change(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                    cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"cancel_shift_change") {
                LINE_LABEL("cancel_shift_change")
                    db.connect();
                nlohmann::json response = ProtocolHandler::handle_cancel_shift_change(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                    cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"ask_check_in") {
                LINE_LABEL("ask_check_in")
                    db.connect();
                nlohmann::json response = ProtocolHandler::handle_check_in(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                    cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"ask_check_out") {
                LINE_LABEL("ask_check_out")
                    db.connect();
                nlohmann::json response = ProtocolHandler::handle_check_out(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                    cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"gen_timeTable") {
                LINE_LABEL("gen_timeTable")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_gen_schedule(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"ask_handover_list") {
                LINE_LABEL("ask_handover_list")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_ask_handover_list(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"ask_handover_detail") {
                LINE_LABEL("ask_handover_detail")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_ask_handover_detail(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"ask_timetable_user") {
                LINE_LABEL("ask_timetable_user")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_ask_timetable_user(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"ask_notice_list") {
                LINE_LABEL("ask_notice_list")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_ask_notice_list(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"ask_notice_detail") {
                LINE_LABEL("ask_notice_detail")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_ask_notice_detail(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
                }
            else if (protocol == u8"check_today_duty") {
                LINE_LABEL("check_today_duty")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_check_today_duty(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"req_shift_info") {
                LINE_LABEL("req_shift_info")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_rgs_shift_info(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"reg_handover") {
                LINE_LABEL("reg_handover")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_reg_handover(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"summary_journal") {
                LINE_LABEL("summary_journal")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_summary_journal(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"attendance_info") {
                LINE_LABEL("attendance_info")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_attendance_info(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"ask_timetable_weekly") {
                LINE_LABEL("ask_timetable_weekly")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_ask_timetable_weekly(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"rgs_team_info") {
                LINE_LABEL("rgs_team_info")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_rgs_team_info(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"rgs_grade_info") {
                LINE_LABEL("rgs_grade_info")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_rgs_grade_info(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }
            else if (protocol == u8"rgs_staff_info") {
                LINE_LABEL("rgs_staff_info")
                db.connect();
                nlohmann::json response = ProtocolHandler::handle_rgs_staff_info(json, db);
                TcpServer::sendJsonResponse(clientSocket, response.dump());
                MIDDLELINE
                cout << response.dump(2) << endl;
                LINE
            }

            else {
                cerr << u8"[����] �� �� ���� ��������: " << protocol << endl;
                TcpServer::sendJsonResponse(clientSocket, R"({"protocol":"unknown","resp":"fail","messege":"unknown_protocol"})");
            }
        }
        catch (const nlohmann::json::parse_error& e) {
            cerr << u8"[����] JSON �Ľ� ���� (parse_error): " << e.what() << endl;
        }
        catch (const nlohmann::json::type_error& e) {
            cerr << u8"[����] JSON Ÿ�� ���� (type_error): " << e.what() << endl;
        }
        catch (const exception& e) {
            cerr << u8"[����] ��Ÿ ����: " << e.what() << endl;
        }
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
