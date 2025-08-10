#include "ProtocolHandler.h"
#include "DBManager.h"
#include "TcpServer.h"
#include <iostream>
#include <windows.h>  // toUTF8 함수에 필요
using namespace std;
using json = nlohmann::json;

string toUTF8_safely(const string& cp949Str) {
    // CP949 → UTF-16
    int wlen = MultiByteToWideChar(949, 0, cp949Str.data(), (int)cp949Str.size(), nullptr, 0);
    if (wlen == 0) return "인코딩 오류";

    wstring wide(wlen, 0);
    MultiByteToWideChar(949, 0, cp949Str.data(), (int)cp949Str.size(), &wide[0], wlen);

    // UTF-16 → UTF-8
    int ulen = WideCharToMultiByte(CP_UTF8, 0, wide.data(), wlen, nullptr, 0, nullptr, nullptr);
    string utf8(ulen, 0);
    WideCharToMultiByte(CP_UTF8, 0, wide.data(), wlen, &utf8[0], ulen, nullptr, nullptr);

    return utf8;
}

// ============================[로그인 handler]================================
json ProtocolHandler::handle_login(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "login";
   cout << u8"[login] 요청:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = "요청 데이터 형식 오류";
        return response;
    }

    const json& data = root["data"];

    string id = data.value("id", "");
    string pw = data.value("pw", "");

    if (id.empty() || pw.empty()) {
        response["resp"] = "fail";
        response["message"] = u8"아이디 또는 비밀번호 누락";
        return response;
    }

    json result_data;
    string out_err_msg;

    if (db.login(id, pw, result_data, out_err_msg)) {
        int staff_uid = result_data.value("staff_uid", -1);
        int team_uid = result_data.value("team_uid", -1);

        string att_err;
        string req_err;
        string staff_err;
        StaffInfo staff_info;

        db.get_today_attendance     (staff_uid, team_uid, result_data, att_err);
        db.get_request_status_count (staff_uid, result_data, req_err);
        bool ok_staff = db.get_staff_info_by_uid(staff_uid, staff_info, staff_err);

        response["resp"] = "success";
        response["data"] = result_data;

        if (ok_staff && !staff_info.name.empty()) {
            response["data"]["staff_name"] = staff_info.name;
        }
        else {
            // 로그인 결과에 이름이 이미 있었다면 fallback
            response["data"]["staff_name"] = result_data.value("staff_name", "");
            if (!staff_err.empty()) response["message"]= staff_err; 
        }

        response["message"] = u8"로그인 성공";

    }
    else {
        response["resp"] = "fail";
        response["message"] = out_err_msg;
    }
    return response;
}

json ProtocolHandler::handle_login_admin(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "login_admin";
   cout << u8"[login_admin] 요청:\n" << root.dump(2) << endl;
    //[1] 필수 인자 체크
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }
    //[2] 클라이언트에게 받은 data 내부 값 저장
    const json& data = root["data"];

    string id = data.value("id", "");
    string pw = data.value("pw", "");

    if (id.empty() || pw.empty()) {
        response["resp"] = "fail";
        response["message"] = u8"아이디 또는 비밀번호 누락";
        return response;
    }
    // [3] 클라이언트에게 줄 data json 및 에러메시지 할당
    json result_data;
    string out_err_msg;

    // [4] data json에 값 대입
    if (db.login_admin(id, pw, result_data, out_err_msg)) {
        response["resp"] = "success";
        response["data"] = result_data;
        response["message"] = u8"로그인 성공";
    }
    else {
        response["resp"] = "fail";
        response["message"] = out_err_msg;
    }
    return response; //[5] 반환
}

// ============================[정보 등록 handler]================================

json ProtocolHandler::handle_rgs_shift_info(const json& root, DBManager& db) {
    json resp;
    resp["protocol"] = "req_shift_info";
    cout << u8"[req_shift_info] 요청:\n" << root.dump(2) << endl;

    // team_uid 파싱
    int team_uid = -1;
    if (root.contains("data") && root["data"].is_object() && root["data"].contains("team_uid")) {
        try {
            team_uid = root["data"]["team_uid"].get<int>();
        }
        catch (...) { team_uid = -1; }
    }
    if (team_uid <= 0) {
        resp["resp"] = "fail";
        resp["message"] = u8"team_uid 누락 또는 형식 오류";
        return resp;
    }

    vector<ShiftInfo> shifts;
    string err;
    if (!db.req_shift_info_by_team(team_uid, shifts, err)) {
        resp["resp"] = "fail";
        resp["message"] = err.empty() ? u8"[DB 오류] 조회 실패" : err;
        return resp;
    }

    // 결과 비어있음 처리(선택: 비정상으로 볼지 정상 빈배열로 보낼지 정책 결정)
    if (shifts.empty()) {
        resp["resp"] = "success";
        resp["data"] = { {"shift_info", json::array()} };
        resp["message"] = u8"해당 팀의 교대코드가 없습니다";
        return resp;
    }

    json shift_array = json::array();
    for (const auto& s : shifts) {
        shift_array.push_back({
            {"duty_type",  s.duty_type},
            {"start_time", s.start_time},
            {"end_time",   s.end_time},
            {"duty_hours", s.duty_hours}
            });
    }

    resp["resp"] = "success";
    resp["data"] = { {"shift_info", move(shift_array)} };
    resp["message"] = "";
    return resp;
}

json ProtocolHandler::handle_rgs_team_info(const json& root, DBManager& db) {
    json resp; resp["protocol"] = "rgs_team_info";
    cout << u8"[rgs_team_info] 요청:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        resp["resp"] = "fail";
        resp["message"] = u8"요청 데이터 형식 오류";
        resp["data"] = nullptr;
        return resp;
    }

    const auto& d = root["data"];
    string company_name = d.value("company_name", "");
    string team_name = d.value("team_name", "");
    string job_category = d.value("job_category", "");
    const auto& shift_info = d.contains("shift_info") ? d["shift_info"] : json::array();

    if (company_name.empty() || team_name.empty() || job_category.empty() || !shift_info.is_array()) {
        resp["resp"] = "fail";
        resp["message"] = u8"필수 파라미터 누락";
        resp["data"] = nullptr;
        return resp;
    }

    nlohmann::json out; string err;
    if (!db.register_team_info(company_name, team_name, job_category, shift_info, out, err)) {
        resp["resp"] = "fail";
        resp["message"] = err;
        resp["data"] = nullptr;
        return resp;
    }

    resp["resp"] = "success";
    resp["message"] = u8"팀/교대 정보 등록 완료";
    resp["data"] = out;   
    return resp;
}

json ProtocolHandler::handle_rgs_grade_info(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "rgs_grade_info"; 
    cout << u8"[rgs_grade_info] 요청:\n" << root.dump(2) << endl;

    const json& d = root["data"];                
    const int team_uid = d["team_uid"].get<int>();

    vector<GradeInfo> grades;
    grades.reserve(d["grades"].size());
    for (const auto& g : d["grades"]) {
        if (!g.is_object()
            || !g.contains("grade_level") || !g["grade_level"].is_number_integer()
            || !g.contains("grade_name") || !g["grade_name"].is_string()) {
            response["resp"] = "fail"; response["message"] = "grade item invalid"; response["data"] = json::object();
            return response;
        }
        GradeInfo one;
        one.grade_level = g["grade_level"].get<int>();
        one.grade_name = g["grade_name"].get<string>();
        grades.push_back(move(one));
    }

    // [2] DB 저장
    string err;
    if (!db.register_grade_info(team_uid, grades, err)) {
        response["resp"] = "fail";
        response["message"] = toUTF8_safely(err);  
        response["data"] = json::object();
        return response;
    }

    // [3] 응답 (빈 data)
    response["resp"] = "success";
    response["message"] = u8"직급정보 저장 완료!";
    response["data"] = json::object();
    return response;
}

json ProtocolHandler::handle_rgs_staff_info(const json& root, DBManager& db) {
    json resp;
    resp["protocol"] = "rgs_staff_info";
    cout << u8"[rgs_staff_info] 요청:\n" << root.dump(2) << endl;

    const auto& data = root.at("data");
    int team_uid = data.at("team_uid").get<int>();

    int ok = 0, fail = 0;

    for (const auto& s : data.at("staff")) {
        int grade_level = s.value("grade_level", 0);
        string name = s.value("staff_name", "");
        string phone = s.value("phone_num", "");
        int monthly_workhour = s.value("total_hours", 0);

        string new_id, new_pw, err;
        if (db.register_staff_info(team_uid, grade_level, name, phone,
            monthly_workhour, new_id, new_pw, err)) {
            ok++;
        }
        else {
            fail++;
        }
    }

    // resp 값 설정
    if (fail == 0) {
        resp["resp"] = "success";
        resp["message"] = u8"모든 직원 등록 완료";
    }
    else if (ok > 0) {
        resp["resp"] = "fail";
        resp["message"] = u8"일부 직원 등록 실패 (" + to_string(fail) + u8"명 실패)";
    }
    else {
        resp["resp"] = "fail";
        resp["message"] = u8"직원 등록 실패";
    }

    return resp;
}

// ============================[근무 변경 신청 handler]================================

json ProtocolHandler::handle_shift_change_detail(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "shift_change_detail";
   cout << u8"[shift_change_detail] 요청:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }
    const json& data = root["data"];

    // 필수 파라미터 확인
    if (!data.contains("staff_uid") || !data.contains("req_year") || !data.contains("req_month")) {
        response["resp"] = "fail";
        response["message"] = u8"필수 파라미터 누락";
        return response;
    }

    int staff_uid = data["staff_uid"];
    string req_year = data["req_year"];
    string req_month = data["req_month"];
    string year_month = req_year + "-" + (req_month.length() == 1 ? "0" + req_month : req_month);

    json result_data;
    string out_err_msg;

    if (db.shift_change_detail(staff_uid, year_month, result_data, out_err_msg)) {
        response["resp"] = "success";
        response["data"] = result_data;
        response["message"] = u8"변경신청목록 전송완료!";
    }
    else {
        response["resp"] = "fail";
        response["message"] = out_err_msg;
    }
    return response;
}

json ProtocolHandler::handle_ask_shift_change(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_shift_change";
   cout << u8"[ask_shift_change] 요청:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }
    const json& data = root["data"];

    // 필수 파라미터 확인
    if (!data.contains("staff_uid") || !data.contains("date") || !data.contains("duty_type") || !data.contains("message")) {
        response["resp"] = "fail";
        response["message"] = u8"필수 파라미터 누락";
        return response;
    }

    int staff_uid = data["staff_uid"];
    string date = data["date"];
    string duty_type = data["duty_type"];
    string message = data["message"];
    json result_data;
    string out_err_msg;

    if (db.ask_shift_change(staff_uid, date, duty_type, message, out_err_msg)) {
        response["resp"] = "success";
        response["data"] = result_data;
        response["message"] = u8"근무변경신청 처리완료!";
    }
    else {
        response["resp"] = "fail";
        response["message"] = out_err_msg;
    }
    return response;
}

json ProtocolHandler::handle_cancel_shift_change(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "cancel_shift_change";
   cout << u8"[cancel_shift_change] 요청:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }
    const json& data = root["data"];

    if (!data.contains("duty_request_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"필수 파라미터 누락";
        return response;
    }
    json result_data;
    string err_msg;

    int duty_request_uid = data["duty_request_uid"];
    if (db.cancel_shift_change(duty_request_uid, result_data, err_msg)) {
        response["resp"] = "success";
        response["data"] = result_data;
        response["message"] = u8"근무변경취소 처리완료!";
    }
    return response;
}

// ============================[출퇴근 handler]================================

json ProtocolHandler::handle_check_in(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_check_in";
   cout << u8"[ask_check_in] 요청:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }

    const json& data = root["data"];

    if (!data.contains("staff_uid") || !data.contains("team_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"필수 파라미터 누락";
        return response;
    }

    json result_data;
    string err_msg;
    int staff_uid = data["staff_uid"];
    int team_uid = data["team_uid"];

    if (db.ask_check_in(staff_uid, team_uid, result_data, err_msg)) {
        response["resp"] = "success";
        response["data"] = result_data;
        response["message"] = u8"출근 완료";
    }
    return response;
}

json ProtocolHandler::handle_check_out(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_check_out";
   cout << u8"[ask_check_out] 요청:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }

    const json& data = root["data"];

    if (!data.contains("check_in_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"필수 파라미터 누락";
        return response;
    }

    int check_in_uid = data["check_in_uid"];
    string err_msg;

    if (db.ask_check_out(check_in_uid, err_msg)) {
        response["resp"] = "success";
        response["message"] = u8"퇴근 완료";
    }
    return response;
}

json ProtocolHandler::handle_attendance_info(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "attendance_info";
    cout << u8"[attendance_info] 요청:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }
    const json& data = root["data"];

    if (!data.contains("staff_uid")|| !data.contains("date")) {
        response["resp"] = "fail";
        response["message"] = u8"필수 파라미터 누락";
        return response;
    }
    int staff_uid = data["staff_uid"];
    string date = data["date"];
    string err_msg;

    nlohmann::json db_json;
    string in_ts, out_ts, err;

    if (!db.get_attendance_info(staff_uid, date, in_ts, out_ts, err)) {
        response["resp"] = "fail"; response["message"] = err;
        response["data"] = { {"attendance", {{"check_in_time", nullptr}, {"check_out_time", nullptr}}} };
        return response;
    }

    nlohmann::json att;
    att["check_in_time"] = in_ts.empty() ? nullptr : nlohmann::json(in_ts);
    att["check_out_time"] = out_ts.empty() ? nullptr : nlohmann::json(out_ts);

    response["resp"] = "success";
    response["message"] = "ok";
    response["data"] = { {"attendance", att} };
    return response;
}


// ============================[근무표 생성 handler]================================

json ProtocolHandler::handle_gen_schedule(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "gen_timeTable";
   cout << u8"[gen_timeTable] 요청:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }

    AdminContext ctx;
    string err_msg;

    const json& data = root["data"];
    int admin_uid = data.value("admin_uid", -1);

    // [1] 연월 추출 및 year_month 생성
    string year = data.value("req_year", "");
    string month = data.value("req_month", "");
    string year_month = year + "-" + (month.length() == 1 ? "0" + month : month);
   cout << "1";
    ctx.admin_uid = admin_uid;
    ctx.year_month = year_month;

    if (!db.get_admin_context_by_uid(admin_uid, ctx, err_msg)) {
        response["resp"] = "fail";
        response["message"] = err_msg;
        return response;
    }

    // [2] 팀 소속 직원 목록 조회
    vector<StaffInfo> staff_list;
    if (!db.get_staff_list_by_team(ctx.team_uid, staff_list, err_msg)) {
        response["resp"] = "fail";
        response["message"] = err_msg;
        return response;
    }
   cout << "2";

    // [3] JSON 배열 구성
    json staff_array = json::array();
    for (const auto& s : staff_list) {
        staff_array.push_back({
            {"name", s.name},
            {"staff_id", s.staff_uid},
            {"grade", s.grade},
            {"total_monthly_work_hours", s.monthly_workhour}
            });
    }
   cout << "3";

    //-------------------------------------------------------------------
    // [4] 파이썬 요청 Json 만들기 ㅜ.ㅜ
    json py_request = {
    {"protocol", "py_gen_timetable"},
    {"data", {
        {"staff_data", {{"staff", staff_array}}},
        {"position", ctx.team_name},
        {"target_month", ctx.year_month},
        {"custom_rules", {
            {"shifts", ctx.shift_setting.shifts},
            {"shift_hours", ctx.shift_setting.shift_hours}
        }},
        {"night_shifts", ctx.shift_setting.night_shifts},
        {"off_shifts", ctx.shift_setting.off_shifts}
    }}
    };
    // [5] 파이썬 호출
    json py_response;
    if (!TcpServer::connectToPythonServer(py_request, py_response, err_msg)) {
        response["resp"] = "fail";
        response["message"] = err_msg;
        return response;
    }
    cout << "[pyrequest]\n" << py_request.dump(2);
   cout << "4";

    // [6] 응답 검증
    if (py_response.value("resp", "") != "success") {
        response["resp"] = "fail";
        response["message"] = py_response.value("message",
            py_response.value("error", u8"파이썬 서버 응답 오류"));
        return response;
    }
    cout << "[pyresponse]\n" << py_response.dump(2);

    // [6-1] data 정규화: 배열이든, 날짜키-객체든 rows로 통일
    json rows = json::array();

    if (py_response.contains("data") && py_response["data"].is_object()) {
        // 형태: { "2025-09-01": [ {...}, {...} ], "2025-09-02": [ ... ] }
        for (auto it = py_response["data"].begin(); it != py_response["data"].end(); ++it) {
            const string date_key = it.key();   // 날짜 문자열
            const json& arr = it.value();            // 해당 날짜의 배열
            if (!arr.is_array()) continue;

            for (const auto& shift_entry : arr) {
                json row = shift_entry;
                row["date"] = date_key;
                rows.push_back(move(row));
            }
        }
    }
    else if (py_response.contains("data") && py_response["data"].is_array()) {
        // 형태: [ { "date": "...", "shift": "...", ... }, ... ]
        for (const auto& row : py_response["data"]) rows.push_back(row);
    }
    else {
        throw runtime_error("[JSON structure error] data not found");
    }

    cout << "5-1";

    // [7] DB 저장
    for (const auto& row : rows) {
       string date = row.value("date", "");
       string shift = row.value("shift", "");
        int hours = row.value("hours", 0);

        if (!row.contains("people") || !row["people"].is_array()) continue;

        for (const auto& person : row["people"]) {
            int staff_uid = person.value("staff_uid",
                person.value("staff_id", -1)); // 키 보정
            if (staff_uid < 0) continue;

           string err;
            if (!db.insert_schedule(date, staff_uid, shift, err)) {
               cerr << u8"[DB 저장 실패] 날짜:" << date
                    << ", UID:" << staff_uid << ", 오류:" << err << "\n";
            }
        }
    }
   cout << "6";

    // [8] 최종 응답(원하면 생성된 스케줄도 그대로 내려주기)
    response["resp"] = "success";
    response["message"] = u8"근무표 생성 완료";
    response["data"] = rows;          // 클라에서 바로 쓰게 전달
    return response;                  // (현재 코드는 py_response를 리턴하고 있음)
}

// ============================[근무표 조회 handler]================================
json ProtocolHandler::handle_ask_timetable_user(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_timetable_user";
   cout << u8"[ask_timetable_user] 요청:\n" << root.dump(2) << endl;

    //[1]
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }
    const json& data = root["data"];
    if (!data.contains("req_year")|| !data.contains("req_month")|| !data.contains("staff_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"필수 파라미터 누락";
        return response;
    }
    int staff_uid = data["staff_uid"];
    string req_year = data["req_year"];
    string req_month = data["req_month"];

    string target_month = req_year + "-" + req_month;
    vector<ScheduleEntry> schedule_list = db.get_staff_schedule(staff_uid, target_month);

    json schedule_array = json::array();
    for (const auto& entry : schedule_list) {
        schedule_array.push_back({
            {"schedule_uid", entry.schedule_uid},
            {"hours", entry.hours},
            {"date", entry.duty_date},
            {"shift", entry.shift_type}
            });
    }
    response["resp"] = "success";
    response["data"] = {
        {"staff_uid", staff_uid},
        {"year", req_year},
        {"month", req_month},
        {"time_table", schedule_array}
    };
    return response;
}

json ProtocolHandler::handle_check_today_duty(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "check_today_duty";
    cout << u8"[check_today_duty] 요청:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        return {
            {"protocol", "check_today_duty"},
            {"resp", "fail"},
            {"message", u8"요청 데이터 형식 오류"}
        };
    }

    const auto& data = root["data"];
    if (!data.contains("date") || !data.contains("team_uid")) {
        return {
            {"protocol", "check_today_duty"},
            {"resp", "fail"},
            {"message", u8"필수 파라미터 누락"}
        };
    }

    int team_uid = data["team_uid"];
    string req_date = data["date"];

    json duty_array;
    string err_msg;
    if (!db.check_today_duty_for_admin(team_uid, req_date, duty_array, err_msg)) {
        response["resp"] = "fail";
        response["message"] = err_msg;
        return response;
    }

    response["resp"] = "success";
    response["data"] = duty_array; // 바로 배열
    response["message"] = u8"조회 성공";
    return response;
}

json ProtocolHandler::handle_ask_timetable_weekly(const json& root, DBManager& db) {
    json response;

    response["protocol"] = "ask_timetable_weekly";
    cout << u8"[ask_timetable_weekly] 요청:\n" << root.dump(2) << endl;
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail"; response["message"] = u8"요청 데이터 형식 오류";
        response["data"] = { {"shift_type", nullptr} };
        return response;
    }
    const auto& d = root["data"];
    int staff_uid = d.value("staff_uid", -1);
    string ymd = d.value("date", ""); // 오늘 날짜
    if (staff_uid < 0 || ymd.empty()) {
        response["resp"] = "fail"; response["message"] = u8"필수 파라미터 누락";
        response["data"] = { {"shift_type", nullptr} };
        return response;
    }

    nlohmann::json out; string err;
    if (!db.get_weekly_shift_mon_sun_compact(staff_uid, ymd, out, err)) {
        response["resp"] = "fail"; response["message"] = err;
        response["data"] = { {"shift_type", nullptr} };
        return response;
    }

    response["resp"] = "success";
    response["message"] = string(u8"주간 근무표");
    response["data"] = out;  // {"shift_type":[7개 문자열]}
    return response;
}



// ============================[인수인계 handler]================================
json ProtocolHandler::handle_ask_handover_list(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_handover_list";
   cout << u8"[ask_handover_list] 요청:\n" << root.dump(2) << endl;

    // [1] 요청 파싱
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }

    const  json& data = root["data"];

    if (!data.contains("team_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"필수 파라미터 누락";
        return response;
    }
    int team_uid = data["team_uid"];
    vector<HandoverNoteInfo> note_list;
    string err_msg;

    // [2] DB에서 인수인계 목록 가져오기
    if (!db.get_handover_notes_by_team(team_uid, note_list, err_msg)) {
        response["resp"] = "fail";
        response["message"] = err_msg;
        return response;
    }

    // [3] JSON 변환
    json list_array = json::array();
    for (const auto& note : note_list) {
        list_array.push_back({
            {"handover_uid", note.handover_uid},
            {"staff_name", note.staff_name},
            {"handover_time", note.handover_time},
            {"shift_type", note.shift_type},
            {"note_type", note.note_type},
            {"title", note.title}
            });
    }

    // [4] 응답 구성
    response["resp"] = "success";
    response["data"]["list"] = list_array;
	response["data"]["team_uid"] = team_uid;
    return response;
}

json ProtocolHandler::handle_ask_handover_detail(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_handover_detail";
   cout << u8"[ask_handover_detail] 요청:\n" << root.dump(2) << endl;

    // [1] 요청 파싱
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }

    const  json& data = root["data"];

    if (!data.contains("handover_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"필수 파라미터 누락";
        return response;
    }

    int handover_uid = data["handover_uid"];
    HandoverNoteInfo note;
    string err_msg;


    if (!db.get_handover_notes_by_uid(handover_uid, note, err_msg)) {
        response["resp"] = "fail";
        response["message"] = err_msg;
        return response;
    }
    response["data"] = {
       {"handover_time", note.handover_time},
       {"staff_name", note.staff_name},
       {"shift_type", note.shift_type},
       {"note_type", note.note_type},
       {"title", note.title},
       {"text", note.text},
       {"text_particular", note.text_particular},
       {"additional_info", note.additional_info},
       {"is_attached", note.is_refined},
       {"file_name", note.file_name} 
    };
    response["resp"] = "success";
    return response;
}

json ProtocolHandler::handle_reg_handover(const json& root, DBManager& db) {
    json resp; resp["protocol"] = "reg_handover";
    resp["protocol"] = "reg_handover";
    cout << u8"[reg_handover] 요청:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        resp["resp"] = "fail";
        resp["message"] = u8"요청 데이터 형식 오류";
        return resp;
    }
    const auto& d = root["data"];

    int staff_uid = d.value("staff_uid", -1);
    int team_uid = d.value("team_uid", -1);
    string title = d.value("title", "");
    string text = d.value("text", "");
    string text_particular = d.value("text_particular", "");
    string additional_info = d.value("additional_info", "");
    int is_attached = d.value("is_attached", 0);
    string file_name = d.value("file_name", "");
	string note_type = d.value("note_type", "");
	string shift_type = d.value("shift_type", "");

    if (staff_uid < 0 || team_uid < 0) {
        resp["resp"] = "fail";
        resp["message"] = u8"필수 파라미터 누락";
        return resp;
    }

    nlohmann::json db_json;
    string err;
    if (!db.reg_handover(staff_uid, team_uid, title, text, text_particular,
		additional_info, is_attached, file_name, note_type, shift_type,
        db_json, err)) {
        resp["resp"] = "fail";
        resp["message"] = err;
        return resp;
    }

    resp["resp"] = "success";
    resp["message"] = u8"인수인계 등록 완료";
    resp.update(db_json); 
    cout << u8"내가만든거: " << resp.dump(2);
    return resp;
}

json ProtocolHandler::handle_summary_journal(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "summary_journal";
    cout << u8"[summary_journal] 요청:\n" << root.dump(2) << endl;
    // [1] 요청 파싱
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }
    const auto& d = root["data"];
    string input_text = d.value("text", "");

    // [1] 파이썬 요청
    json py_req = {
        {"protocol", "py_req_handover_summary"},
        {"data", {
            {"task", "summarize_handover"},
            {"input_text", input_text}
        }}
    };
    json py_res;
    string err;
    if (!TcpServer::connectToPythonServer(py_req, py_res, err)) {
        response["resp"] = "fail";
        response["message"] = err;
        response["data"] = { {"text", ""} };
        return response;
    }
    // [2] 파이썬 응답 검증
    if (py_res.value("resp", "") != "success") {
        response["resp"] = "fail";
        response["message"] = py_res.value("message",
        response.value("error", u8"파이썬 서버 응답 오류"));
        response["data"] = { {"text", ""} };
        return response;
    }
    if (!py_res.contains("data") || !py_res["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"[JSON 구조] data 누락";
        response["data"] = { {"text", ""} };
        return response;
    }

    // [3] 결과 추출
    string summary = py_res["data"].value("result", "");
    response["resp"] = "success";
    response["message"] = u8"요약 완료";
    response["data"] = { {"text", summary} };
    return response;
}


// ============================[공지사항 handler]================================

json ProtocolHandler::handle_ask_notice_list(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_notice_list";
   cout << u8"[ask_notice_list] 요청:\n" << root.dump(2) << endl;
    // [1] 요청 파싱
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }
    const json& data = root["data"];

    if (!data.contains("team_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"필수 파라미터 누락";
        return response;
    }

    int team_uid = data["team_uid"];
    vector <NoticeSummary> note_list;
    string out_err_msg;
    if (!db.get_notice_list_by_team(team_uid, note_list, out_err_msg)) {
        response["resp"] = "fail";
        response["message"] = toUTF8_safely(out_err_msg);
        return response;
    }
    json arr = json::array();
    for (const auto& x : note_list) {
        arr.push_back({
            {"notice_uid",  x.notice_uid},
            {"staff_name",  x.staff_name},
            {"notice_date", x.notice_date},
            {"title",       x.title}
            });
    }
    response["resp"] = "success";
    response["data"] = { {"list", arr} };
    return response;
}

json ProtocolHandler::handle_ask_notice_detail(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_notice_detail";
   cout << u8"[ask_notice_detail] 요청:\n" << root.dump(2) << endl;
    // [1] 요청 파싱
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"요청 데이터 형식 오류";
        return response;
    }
    const json& data = root["data"];

    if (!data.contains("notice_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"필수 파라미터 누락";
        return response;
    }
    int notice_uid = data["notice_uid"];
    NoticeDetail notice;
    string out_err_msg;


    if (!db.get_notice_detail_by_uid(notice_uid, notice, out_err_msg)) {
        response["resp"] = "fail";
        response["message"] = out_err_msg;
        return response;
    }

    response["resp"] = "success";
    response["data"] = {
        {"notice_uid",  notice.notice_uid},
        {"staff_name",  notice.staff_name},
        {"notice_date", notice.notice_date},
        {"title",       notice.title},
        {"content",     notice.content}
    };
    return response;
}