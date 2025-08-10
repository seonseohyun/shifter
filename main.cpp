#define WIN32_LEAN_AND_MEAN     // 윈도우 헤더 경량화 (불필요한 macro 제거)
#include "TcpServer.h"          // TCP 서버 클래스 헤더
#include "DBManager.h"          // DB 실행 클래스 헤더
#include "ProtocolHandler.h"
#include <iostream>
#include <thread>
#include <string>
#include <codecvt> 
#include <locale>
#include <nlohmann/json.hpp>

#define LINE_LABEL(label) cout << "====================[" << label << "]====================\n";
#define LINE cout << "================================================\n";
#define MIDDLELINE cout << u8"------------------------------------------------\n[ 응답 ]\n";

using json = nlohmann::json;
using namespace std;

// UTF-8 -> UTF-16 변환 및 출력
static wstring_convert<codecvt_utf8_utf16<wchar_t>> converter;

// =======================================================================
// [함수] 클라이언트 메시지용
// UTF-8 → 유니코드(wstring) 변환 함수
// - 클라이언트로부터 수신한 문자열이 UTF-8인 경우 한글 깨짐 방지를 위해 사용
// =======================================================================
// 테스트
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
// [함수] 클라이언트 요청 처리 함수 (쓰레드로 실행)
// - 클라이언트가 보낸 메시지를 수신하고, 응답을 반환하는 역할
// - 각 클라이언트마다 이 함수가 독립적으로 실행됨
// =======================================================================
void handleClient(SOCKET clientSocket) {
    DBManager db;
    string jsonStr;
    vector<char> payload;
    while (1) {
        // [1] JSON + payload 수신 (헤더 포함)
        if (!TcpServer::receivePacket(clientSocket, jsonStr, payload)) {
            cerr << u8"[패킷 수신 실패] JSON 수신 실패\n";
            TcpServer::sendJsonResponse(clientSocket, R"({"protocol":"unknown","resp":"fail","message":"receive_fail"})");
            closesocket(clientSocket);
            return;
        }

        // [2] JSON 유효성 검사
        if (!json::accept(jsonStr)) {
            cerr << u8"[JSON 검증 실패] 유효하지 않은 JSON입니다.\n";
            TcpServer::sendJsonResponse(clientSocket, R"({"protocol":"unknown","resp":"fail","message":"invaild_json"})");
            closesocket(clientSocket);
            return;
        }

        try {
            //[STEP 1] JSON 파싱
            json json = json::parse(jsonStr);
            //[STEP 2] 프로토콜 파싱
            string protocol = json.value("protocol", "");

            if (protocol == u8"login") {
                LINE_LABEL("login") //라인
                db.connect(); // DB연결
                nlohmann::json response = ProtocolHandler::handle_login(json, db);// 프로토콜 처리 핸들러로 전송
                TcpServer::sendJsonResponse(clientSocket, response.dump()); // 제이슨 전송
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
                cerr << u8"[에러] 알 수 없는 프로토콜: " << protocol << endl;
                TcpServer::sendJsonResponse(clientSocket, R"({"protocol":"unknown","resp":"fail","messege":"unknown_protocol"})");
            }
        }
        catch (const nlohmann::json::parse_error& e) {
            cerr << u8"[에러] JSON 파싱 실패 (parse_error): " << e.what() << endl;
        }
        catch (const nlohmann::json::type_error& e) {
            cerr << u8"[에러] JSON 타입 오류 (type_error): " << e.what() << endl;
        }
        catch (const exception& e) {
            cerr << u8"[에러] 기타 예외: " << e.what() << endl;
        }
    }
}

int main() {
    // 콘솔 한글 깨짐 방지 설정
    SetConsoleOutputCP(CP_UTF8);                // UTF-8 출력 인코딩 설정
    TcpServer server(5556);                     // 포트 5556으로 서버 시작
    DBManager db;

    // DB 연결 시도
    if (!db.connect()) {
        cout << u8"[서버] DB 연결 실패!" << endl;
        return 1;
    }

    // 서버 바인딩 및 리슨
    if (!server.start()) {
        cout << u8"[서버] 소켓 바인딩 또는 리슨 실패!" << endl;
        return 1;
    }

    cout << u8"[서버] 클라이언트 수신 대기 시작..." << endl;

    // 클라이언트 수신 루프
    while (true) {
        SOCKET clientSocket = server.acceptClient();

        if (clientSocket != INVALID_SOCKET) {
            cout << u8"[서버] 새 클라이언트 연결됨!" << endl;
            thread th(handleClient, clientSocket);
            th.detach();  // 독립적으로 실행
        }
    }
    return 0;
}
