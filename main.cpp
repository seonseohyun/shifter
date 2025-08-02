#define _CRT_SECURE_NO_WARNINGS
#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <ws2tcpip.h>
#include <iostream>
#include <string>
#include <vector>
#include <stdexcept>
#include <nlohmann/json.hpp>
#include <mysql/mysql.h>
#include <fstream>
#include <direct.h>
#include <regex>
#include <cstdlib>
#include <cstdio>  // For sscanf

#pragma comment(lib, "ws2_32.lib")

using json = nlohmann::json;

struct WorkItem {
    std::string jsonStr;
    std::vector<char> payload;
};


std::string toUTF8_safely(const std::string& cp949Str) {
    int wlen = MultiByteToWideChar(949, 0, cp949Str.data(), (int)cp949Str.size(), nullptr, 0);
    if (wlen == 0) return "인코딩 오류";

    std::wstring wide(wlen, 0);
    MultiByteToWideChar(949, 0, cp949Str.data(), (int)cp949Str.size(), &wide[0], wlen);

    int ulen = WideCharToMultiByte(CP_UTF8, 0, wide.data(), wlen, nullptr, 0, nullptr, nullptr);
    std::string utf8(ulen, 0);
    WideCharToMultiByte(CP_UTF8, 0, wide.data(), wlen, &utf8[0], ulen, nullptr, nullptr);

    return utf8;
}

std::vector<char> recvExact(SOCKET sock, size_t size) {
    std::vector<char> buffer(size);
    size_t totalRead = 0;

    while (totalRead < size) {
        int bytesRead = recv(sock, buffer.data() + totalRead, (int)(size - totalRead), 0);
        if (bytesRead == SOCKET_ERROR) throw std::runtime_error("recv() failed: " + std::to_string(WSAGetLastError()));
        if (bytesRead == 0) throw std::runtime_error("Connection closed");
        totalRead += bytesRead;
    }
    return buffer;
}

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


// JSON 파라미터를 직접 받는 버전
std::string updateAndExecuteShiftScheduler(const std::string& staff_id, const std::string& date_, const std::string& shift_from, const std::string& shift_to, const std::string& pythonFilePath) {
    try {
        // 단계 1: 날짜 유효성 검사 (2025-08-01 ~ 2025-08-31)
        int year, month, day;
        if (sscanf(date_.c_str(), "%d-%d-%d", &year, &month, &day) != 3 ) {
            return "오류: 유효하지 않은 날짜입니다.  년도-월-일 형식으로 입력되어야합니다.";
        }

        std::cout << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!shift_from  : " <<shift_from << std::endl;
        std::cout << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!desired_shift  : " << shift_to << std::endl;
        
        


        // 단계 2: JSON 요청 생성
        json request = {
            {"staff_id", staff_id},
            {"date", date_},
            {"original_shift", shift_from},
            {"desired_shift", shift_to}
        };

        // 단계 3: JSON 파일 읽기 및 업데이트
        std::string jsonPath = "C:/workspace/shifter/data/change_requests.json";
        json requests;
        std::ifstream jsonIn(jsonPath);
        if (jsonIn.is_open()) {
            jsonIn >> requests;
            jsonIn.close();
        } else {
            requests = json::array();
        }
        requests.push_back(request);

        // 단계 4: JSON 파일 저장 (원자적 쓰기)
        std::string tempPath = jsonPath + ".tmp";
        std::ofstream jsonOut(tempPath);
        if (!jsonOut.is_open()) {
            return "오류: JSON 파일을 저장할 수 없습니다: " + tempPath;
        }
        jsonOut << requests.dump(2);
        jsonOut.close();
        std::rename(tempPath.c_str(), jsonPath.c_str());

        // 단계 5: Python 스크립트 실행
        std::string command = "python " + pythonFilePath;
        int result = std::system(command.c_str());
        if (result != 0) {
            return "오류: Python 실행 오류: 반환 코드 " + std::to_string(result);
        }

        return "성공: . 변경 요청이 반영되었습니다.";
    } catch (const std::exception& ex) {
        return "오류: " + std::string(ex.what());
    }
}

// DB 연결 함수
MYSQL* create_db_connection() {
    MYSQL* conn = mysql_init(NULL);
    if (!conn) {
        std::cerr << "mysql_init failed" << std::endl;
        return nullptr;
    }

    if (!mysql_real_connect(conn, "localhost", "master", "1111", "shifter", 0, NULL, 0)) {
        std::cerr << "Database connection error: " << mysql_error(conn) << std::endl;
        mysql_close(conn);
        return nullptr;
    }

    mysql_set_character_set(conn, "utf8mb4");
    return conn;
}

// 스케줄 생성 및 DB 업데이트 함수 (conn 전달받음)
void generate_and_update_schedule(MYSQL* conn) {
    if (!conn) return;

    _chdir("c:\\workspace\\shifter");    
    std::system("python shift_scheduler.py");
    




    std::ifstream json_file("C:/workspace/shifter/data/time_table.json");
    if (!json_file.is_open()) {
        std::cerr << "Failed to open time_table.json" << std::endl;
        return;
    }

    json schedule_data;
    try {
        schedule_data = json::parse(json_file);
    }
    catch (const json::parse_error& e) {
        std::cerr << "JSON parsing error: " << e.what() << std::endl;
        return;
    }

    // 트랜잭션 시작
    if (mysql_query(conn, "START TRANSACTION")) {
        std::cerr << "Failed to start transaction: " << mysql_error(conn) << std::endl;
        return;
    }

    // 기존 스케줄 데이터 삭제 (2025년 8월 데이터만)
    const char* delete_query = "DELETE FROM duty_schedule WHERE duty_date >= '2025-08-01' AND duty_date <= '2025-08-31'";
    if (mysql_query(conn, delete_query)) {
        std::cerr << "Failed to delete existing schedule: " << mysql_error(conn) << std::endl;
        mysql_query(conn, "ROLLBACK");
        return;
    }
    std::cout << "Existing schedule data deleted successfully." << std::endl;

    MYSQL_STMT* stmt = mysql_stmt_init(conn);
    if (!stmt) {
        std::cerr << "mysql_stmt_init failed" << std::endl;
        mysql_query(conn, "ROLLBACK");
        return;
    }

    const char* insert_query =
        "INSERT INTO duty_schedule (staff_id, duty_date, shift_code, work_time, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, NOW(), NOW())";

    if (mysql_stmt_prepare(stmt, insert_query, strlen(insert_query))) {
        std::cerr << "mysql_stmt_prepare failed: " << mysql_stmt_error(stmt) << std::endl;
        mysql_stmt_close(stmt);
        mysql_query(conn, "ROLLBACK");
        return;
    }

    MYSQL_BIND bind[4];
    memset(bind, 0, sizeof(bind));

    char staff_id_buf[256];
    char duty_date_buf[11];
    char shift_code_buf[2];
    char work_time_buf[256] = "";

    unsigned long staff_id_len;
    unsigned long duty_date_len;
    unsigned long shift_code_len;
    unsigned long work_time_len = 0;

    my_bool is_null[4] = { 0, 0, 0, 0 };

    bind[0].buffer_type = MYSQL_TYPE_STRING;
    bind[0].buffer = staff_id_buf;
    bind[0].buffer_length = sizeof(staff_id_buf);
    bind[0].length = &staff_id_len;
    bind[0].is_null = &is_null[0];

    bind[1].buffer_type = MYSQL_TYPE_STRING;
    bind[1].buffer = duty_date_buf;
    bind[1].buffer_length = sizeof(duty_date_buf);
    bind[1].length = &duty_date_len;
    bind[1].is_null = &is_null[1];

    bind[2].buffer_type = MYSQL_TYPE_STRING;
    bind[2].buffer = shift_code_buf;
    bind[2].buffer_length = sizeof(shift_code_buf);
    bind[2].length = &shift_code_len;
    bind[2].is_null = &is_null[2];

    bind[3].buffer_type = MYSQL_TYPE_STRING;
    bind[3].buffer = work_time_buf;
    bind[3].buffer_length = sizeof(work_time_buf);
    bind[3].length = &work_time_len;
    bind[3].is_null = &is_null[3];

    if (mysql_stmt_bind_param(stmt, bind)) {
        std::cerr << "mysql_stmt_bind_param failed: " << mysql_stmt_error(stmt) << std::endl;
        mysql_stmt_close(stmt);
        return;
    }

    try {
        for (auto& date_entry : schedule_data.items()) {
            std::string duty_date = date_entry.key();
            strncpy(duty_date_buf, duty_date.c_str(), sizeof(duty_date_buf) - 1);
            duty_date_buf[sizeof(duty_date_buf) - 1] = '\0';
            duty_date_len = strlen(duty_date_buf);

            auto shifts = date_entry.value();
            if (!shifts.is_array()) continue;

            for (const auto& shift_obj : shifts) {
                if (!shift_obj.contains("shift") || !shift_obj["shift"].is_string()) continue;

                std::string shift_code = shift_obj["shift"];
                strncpy(shift_code_buf, shift_code.c_str(), sizeof(shift_code_buf) - 1);
                shift_code_buf[sizeof(shift_code_buf) - 1] = '\0';
                shift_code_len = strlen(shift_code_buf);

                if (!shift_obj.contains("people") || !shift_obj["people"].is_array()) continue;

                for (const auto& member : shift_obj["people"]) {
                    if (!member.contains("staff_id") || !member["staff_id"].is_string()) continue;

                    std::string staff_id = member["staff_id"];
                    strncpy(staff_id_buf, staff_id.c_str(), sizeof(staff_id_buf) - 1);
                    staff_id_buf[sizeof(staff_id_buf) - 1] = '\0';
                    staff_id_len = strlen(staff_id_buf);

                    if (mysql_stmt_execute(stmt)) {
                        std::cerr << "SQL error during insertion: " << mysql_stmt_error(stmt) << std::endl;
                    }
                }
            }
        }
    }
    catch (const json::exception& e) {
        std::cerr << "JSON processing error: " << e.what() << std::endl;
    }

    mysql_stmt_close(stmt);
    
    // 트랜잭션 커밋
    if (mysql_query(conn, "COMMIT")) {
        std::cerr << "Failed to commit transaction: " << mysql_error(conn) << std::endl;
        mysql_query(conn, "ROLLBACK");
        return;
    }
    
    std::cout << "Duty schedule update completed successfully." << std::endl;
}


int main() {
    WSADATA wsaData;
    SOCKET listenSocket = INVALID_SOCKET, clientSocket = INVALID_SOCKET;

    // UTF-8 콘솔 설정
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
    
    // UTF-8 로케일 설정
    std::locale::global(std::locale(".UTF-8"));
    std::wcout.imbue(std::locale());
    std::wcin.imbue(std::locale());

    try {
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
            throw std::runtime_error("WSAStartup failed");

        MYSQL* conn = create_db_connection();
        if (!conn) {
            throw std::runtime_error("Failed to connect to DB");
        }

        generate_and_update_schedule(conn);

        sockaddr_in serverAddr{};
        serverAddr.sin_family = AF_INET;
        serverAddr.sin_addr.s_addr = INADDR_ANY;
        serverAddr.sin_port = htons(5556);

        listenSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (listenSocket == INVALID_SOCKET)
            throw std::runtime_error("socket() failed");

        if (bind(listenSocket, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR)
            throw std::runtime_error("bind() failed");

        if (listen(listenSocket, SOMAXCONN) == SOCKET_ERROR)
            throw std::runtime_error("listen() failed");

        std::cout << u8"서버 시작, 포트 5556 대기 중..." << std::endl;

        while (true) {
            clientSocket = accept(listenSocket, nullptr, nullptr);
            if (clientSocket == INVALID_SOCKET) {
                std::cerr << u8"accept() failed: " << WSAGetLastError() << std::endl;
                continue;
            }

            std::cout << u8"클라이언트 접속됨" << std::endl;

            try {
                while (true) {
                    WorkItem req = receiveWorkItem(clientSocket);
                    auto j = json::parse(req.jsonStr);

                    if (j.contains("Protocol") && j["Protocol"] == "Hello") {
                        std::cout << u8"Hello 프로토콜 받음!" << std::endl;
                        j["Protocol"] = "hi";
                        sendWorkItem(clientSocket, WorkItem{ j.dump(), {} });
                    }
                    else if (j.contains("Protocol") && j["Protocol"] == "Insert") {
                        std::cout << u8"Insert 프로토콜 받음!" << std::endl;

                        if (j.contains("content")) {
                            std::string content = j["content"];
                            size_t pos = 0;
                            while ((pos = content.find("'", pos)) != std::string::npos) {
                                content.insert(pos, "'");
                                pos += 2;
                            }
                            std::string queryStr = "INSERT INTO test (TEST_FIELD) VALUES ('" + content + "');";

                            if (mysql_query(conn, queryStr.c_str())) {
                                std::cerr << u8"Insert 쿼리 실패: " << mysql_error(conn) << std::endl;
                            }
                            else {
                                std::cout << u8"Insert 성공!" << std::endl;
                            }
                        }
                        j["Protocol"] = "insert ok";
                        sendWorkItem(clientSocket, WorkItem{ j.dump(), {} });
                    }
                    else if (j.contains("Protocol") && j["Protocol"] == "GetSchedule") {
                        std::cout << u8"GetSchedule 프로토콜 받음!" << std::endl;
                        
                        // time_table.json 파일 읽기 c:\\workspace\\shifter\\shift_scheduler.py
                        std::ifstream json_file("c:/workspace/shifter/data/time_table.json");
                        if (json_file.is_open()) {
                            std::string json_content((std::istreambuf_iterator<char>(json_file)), std::istreambuf_iterator<char>());
                            json_file.close();
                            
                            j["Protocol"] = "schedule_data";
                            j["content"] = json_content;
                        } else {
                            j["Protocol"] = "error";
                            j["message"] = "근무표 파일을 찾을 수 없습니다.";
                        }
                        sendWorkItem(clientSocket, WorkItem{ j.dump(), {} });
                    }
                    else if (j.contains("Protocol") && j["Protocol"] == "ChangeShift") {
                        std::cout << u8"ChangeShift 프로토콜 받음!" << std::endl;

                        if (j.contains("staff_id") && j.contains("date_") && j.contains("shift_from") && j.contains("shift_to")) {
                            std::string staff_id = j["staff_id"];
                            std::string date_ = j["date_"];
                            std::string shift_from = j["shift_from"];
                            std::string shift_to = j["shift_to"];

                            try {
                                                                                                                                    
                                updateAndExecuteShiftScheduler(staff_id, date_, shift_from, shift_to, "c:\\workspace\\shifter\\shift_scheduler.py");

                                // 성공 후 DB 갱신
                                generate_and_update_schedule(conn);

                                j["Protocol"] = "change_success";
                                j["message"] = "근무 변경 요청이 성공적으로 처리되었습니다.";
                            } catch (const std::exception& e) {
                                std::string error_msg = e.what();

                                if (error_msg.find("No solution") != std::string::npos || error_msg.find("해가 없습니다") != std::string::npos) {
                                    j["Protocol"] = "no_solution";
                                    j["message"] = "근무 변경이 불가능합니다. 해당 조건으로는 근무표를 생성할 수 없습니다.";
                                } else {
                                    j["Protocol"] = "change_error";
                                    j["message"] = error_msg;
                                }
                            }
                        } else {
                            j["Protocol"] = "change_error";
                            j["message"] = "필수 정보가 누락되었습니다. staff_id, date_, shift_from, shift_to가 필요합니다.";
                        }

                        sendWorkItem(clientSocket, WorkItem{ j.dump(), {} });
                    }

                }
            }
            catch (const std::exception& e) {
                std::cerr << "클라이언트 처리 중 오류: " << e.what() << std::endl;
            }

            if (clientSocket != INVALID_SOCKET) {
                closesocket(clientSocket);
                clientSocket = INVALID_SOCKET;
            }
            std::cout << "클라이언트 연결 종료, 새 연결 대기 중..." << std::endl;
        }

        mysql_close(conn);
        if (listenSocket != INVALID_SOCKET) closesocket(listenSocket);
        WSACleanup();
    }
    catch (const std::exception& e) {
        std::cerr << "서버 오류: " << e.what() << std::endl;
    }

    return 0;
}
