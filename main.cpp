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

#define LINE_LABEL(label) cout << "=======================[" << label << "]=======================\n";
#define LINE cout << "=====================================================\n";
#define MIDDLELINE cout << u8"-----------------------------------------------------\n[ 응답 ]\n";

using json = nlohmann::json;
using namespace std;

// UTF-8 -> UTF-16 변환 및 출력
static std::wstring_convert<std::codecvt_utf8_utf16<wchar_t>> converter;

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
            json json = nlohmann::json::parse(jsonStr);
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
            //else if (protocol == u8"cancel_shift_change") {
            //    LINE_LABEL("ask_shift_change")
            //    db.connect();
            //    nlohmann::json response = ProtocolHandler::handle_cancel_shift_change(json, db);
            //    TcpServer::sendJsonResponse(clientSocket, response.dump());
            //    MIDDLELINE
            //    cout << response.dump(2) << endl;
            //    LINE
            //}
            
            else {
                std::cerr << u8"[에러] 알 수 없는 프로토콜: " << protocol << std::endl;
                TcpServer::sendJsonResponse(clientSocket, R"({"protocol":"unknown","resp":"fail","messege":"unknown_protocol"})");
            }
        }
        catch (const nlohmann::json::parse_error& e) {
            std::cerr << u8"[에러] JSON 파싱 실패 (parse_error): " << e.what() << std::endl;
        }
        catch (const nlohmann::json::type_error& e) {
            std::cerr << u8"[에러] JSON 타입 오류 (type_error): " << e.what() << std::endl;
        }
        catch (const std::exception& e) {
            std::cerr << u8"[에러] 기타 예외: " << e.what() << std::endl;
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
