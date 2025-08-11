#include "ProtocolHandler.h"
#include "DBManager.h"
#include "TcpServer.h"
#include <iostream>
#include <windows.h>  // toUTF8 �Լ��� �ʿ�
using namespace std;
using json = nlohmann::json;

string toUTF8_safely(const string& cp949Str) {
    // CP949 �� UTF-16
    int wlen = MultiByteToWideChar(949, 0, cp949Str.data(), (int)cp949Str.size(), nullptr, 0);
    if (wlen == 0) return "���ڵ� ����";

    wstring wide(wlen, 0);
    MultiByteToWideChar(949, 0, cp949Str.data(), (int)cp949Str.size(), &wide[0], wlen);

    // UTF-16 �� UTF-8
    int ulen = WideCharToMultiByte(CP_UTF8, 0, wide.data(), wlen, nullptr, 0, nullptr, nullptr);
    string utf8(ulen, 0);
    WideCharToMultiByte(CP_UTF8, 0, wide.data(), wlen, &utf8[0], ulen, nullptr, nullptr);

    return utf8;
}

static void strip_bom_everywhere(string& s) {
    // ���ڿ� ��� �־ BOM�� ���� (Ŭ�� �߰��� �� �ִ� ��� ���)
    const string bom = "\xEF\xBB\xBF";
    for (size_t pos = s.find(bom); pos != string::npos; pos = s.find(bom, pos)) {
        s.erase(pos, bom.size());
    }
}

static void strip_leading_trailing_noise(string& s) {
    // �յ� ����/�ٹٲ�/�ι��� �� ���� (JSON �յڿ� ����� ��� ���)
    auto is_noise = [](unsigned char c) {
        return c == 0 || c == '\r' || c == '\n' || c == '\t' || c == ' ';
        };
    size_t b = 0, e = s.size();
    while (b < e && is_noise((unsigned char)s[b])) ++b;
    while (e > b && is_noise((unsigned char)s[e - 1])) --e;
    if (b > 0 || e < s.size()) s = s.substr(b, e - b);
}

// ============================[�α��� handler]================================
json ProtocolHandler::handle_login(const json& root, DBManager& db) {
    json resp; resp["protocol"] = "login";
    cout << u8"[login] ��û:\n" << root.dump(2) << endl;

    // 0) �Է� ����
    if (!root.contains("data") || !root["data"].is_object()) {
        resp["resp"] = "fail"; resp["message"] = "��û ������ ���� ����"; return resp;
    }
    const auto& data = root["data"];
    string id = data.value("id", "");
    string pw = data.value("pw", "");
    if (id.empty() || pw.empty()) {
        resp["resp"] = "fail"; resp["message"] = u8"���̵� �Ǵ� ��й�ȣ ����"; return resp;
    }

    // 1) 1�� ����: �ּ� Ű�� Ȯ�� (staff_uid, team_uid)
    nlohmann::json auth; string err;
    if (!db.login(id, pw, auth, err)) {   // db.login �� �ּ��� staff_uid, team_uid�� �־��ְ�
        resp["resp"] = "fail"; resp["message"] = err; return resp;
    }
    int staff_uid = auth.value("staff_uid", -1);
    int team_uid = auth.value("team_uid", -1);
    if (staff_uid < 0 || team_uid < 0) {
        resp["resp"] = "fail"; resp["message"] = u8"�α��� �� �ĺ��� ����"; return resp;
    }

    // 2) �� ��Ÿ �ε� ��, �� ���ڵ� ã��
    vector<StaffInfo> meta;  // ��Ÿ ����ü: name/id/pw/phone/is_tmp_id/grade_level/grade_name/monthly_workhour/company_name ...
    if (!db.get_staff_list_by_team(team_uid, meta, err)) {
        resp["resp"] = "fail"; resp["message"] = err; return resp;
    }
    const StaffInfo* me = nullptr;
    for (const auto& m : meta) { if (m.staff_uid == staff_uid) { me = &m; break; } }
    if (!me) { resp["resp"] = "fail"; resp["message"] = u8"����� ��Ÿ�� ã�� ���߽��ϴ�"; return resp; }

    // 3) ���� �⺻ ������ ����(��Ÿ ���)
    json out;
    out["date"] = DateUtil::get_today();
    out["staff_uid"] = staff_uid;
    out["team_uid"] = team_uid;
    out["staff_name"] = me->name;            
    out["team_name"] = me->team_name;    
    out["grade_level"] = me->grade_level;
    out["grade_name"] = me->grade_name;     
    out["is_tmp_id"] = me->is_tmp_id;

    string att_err, req_err;
    db.get_today_attendance(staff_uid, team_uid, out, att_err);
    db.get_request_status_count(staff_uid, out, req_err);

    resp["resp"] = "success";
    resp["message"] = u8"�α��� ����";
    resp["data"] = move(out);
    return resp;
}
json ProtocolHandler::handle_login_admin(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "login_admin";
   cout << u8"[login_admin] ��û:\n" << root.dump(2) << endl;
    //[1] �ʼ� ���� üũ
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    //[2] Ŭ���̾�Ʈ���� ���� data ���� �� ����
    const json& data = root["data"];

    string id = data.value("id", "");
    string pw = data.value("pw", "");

    if (id.empty() || pw.empty()) {
        response["resp"] = "fail";
        response["message"] = u8"���̵� �Ǵ� ��й�ȣ ����";
        return response;
    }
    // [3] Ŭ���̾�Ʈ���� �� data json �� �����޽��� �Ҵ�
    json result_data;
    string out_err_msg;

    // [4] data json�� �� ����
    if (db.login_admin(id, pw, result_data, out_err_msg)) {
        response["resp"] = "success";
        response["data"] = result_data;
        response["message"] = u8"�α��� ����";
    }
    else {
        response["resp"] = "fail";
        response["message"] = out_err_msg;
    }
    return response; //[5] ��ȯ
}

// ============================[���� ��� / ����  handler]================================

json ProtocolHandler::handle_rgs_shift_info(const json& root, DBManager& db) {
    json resp;
    resp["protocol"] = "req_shift_info";
    cout << u8"[req_shift_info] ��û:\n" << root.dump(2) << endl;

    // team_uid �Ľ�
    int team_uid = -1;
    if (root.contains("data") && root["data"].is_object() && root["data"].contains("team_uid")) {
        try {
            team_uid = root["data"]["team_uid"].get<int>();
        }
        catch (...) { team_uid = -1; }
    }
    if (team_uid <= 0) {
        resp["resp"] = "fail";
        resp["message"] = u8"team_uid ���� �Ǵ� ���� ����";
        return resp;
    }

    vector<ShiftInfo> shifts;
    string err;
    if (!db.req_shift_info_by_team(team_uid, shifts, err)) {
        resp["resp"] = "fail";
        resp["message"] = err.empty() ? u8"[DB ����] ��ȸ ����" : err;
        return resp;
    }

    // ��� ������� ó��(����: ���������� ���� ���� ��迭�� ������ ��å ����)
    if (shifts.empty()) {
        resp["resp"] = "success";
        resp["data"] = { {"shift_info", json::array()} };
        resp["message"] = u8"�ش� ���� �����ڵ尡 �����ϴ�";
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
    cout << u8"[rgs_team_info] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        resp["resp"] = "fail";
        resp["message"] = u8"��û ������ ���� ����";
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
        resp["message"] = u8"�ʼ� �Ķ���� ����";
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
    resp["message"] = u8"��/���� ���� ��� �Ϸ�";
    resp["data"] = out;   
    return resp;
}

json ProtocolHandler::handle_rgs_grade_info(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "rgs_grade_info"; 
    cout << u8"[rgs_grade_info] ��û:\n" << root.dump(2) << endl;

    const json& d = root["data"];                
    const int team_uid = d["team_uid"].get<int>();
    const int admin_uid = d["admin_uid"].get<int>();

    vector<GradeInfo> grades;
    grades.reserve(d["grades"].size());
    for (const auto& g : d["grades"]) {
        GradeInfo one;
        one.grade_level = g["grade_level"].get<int>();
        one.grade_name = g["grade_name"].get<string>();
        grades.push_back(move(one));
    }

    // [2] DB ����
    string err;
    if (!db.register_grade_info(team_uid, admin_uid, grades, err)) {
        response["resp"] = "fail";
        response["message"] = toUTF8_safely(err);  
        return response;
    }

    // [3] ���� (�� data)
    response["resp"] = "success";
    response["message"] = u8"�������� ���� �Ϸ�!";
    return response;
}

json ProtocolHandler::handle_rgs_staff_info(const json& root, DBManager& db) {
    json resp;
    resp["protocol"] = "rgs_staff_info";
    cout << u8"[rgs_staff_info] ��û:\n" << root.dump(2) << endl;

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
        
    // resp �� ����
    if (fail == 0) {
        resp["resp"] = "success";
        resp["message"] = u8"��� ���� ��� �Ϸ�";
    }
    else if (ok > 0) {
        resp["resp"] = "fail";
        resp["message"] = u8"�Ϻ� ���� ��� ���� (" + to_string(fail) + u8"�� ����)";
    }
    else {
        resp["resp"] = "fail";
        resp["message"] = u8"���� ��� ����";
    }

    return resp;
}

json ProtocolHandler::handle_modify_user_info(const json& root, DBManager& db)
{
    json resp;
    resp["protocol"] = "modify_user_info";
    cout << u8"[modify_user_info] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        resp["resp"] = "fail";
        resp["message"] = u8"��û ������ ���� ����";
        return resp;
    }

    const json& data = root["data"];
    if (!data.contains("staff_uid") || !data.contains("pw")) {
        resp["resp"] = "fail";
        resp["message"] = u8"�ʼ� �Ķ���� ����";
        return resp;
    }

    int staff_uid = data["staff_uid"];
    string pw = data["pw"];

    // DB���� ���� ���� ����
    string err_msg;
    if (db.modify_user_info(staff_uid, pw, err_msg)) {
        resp["resp"] = "success";
        resp["message"] = u8"���� ���� ���� �Ϸ�";
    }
    else {
        resp["resp"] = "fail";
        resp["message"] = err_msg;
    }

    return resp;    
}

// ============================[�ٹ� ���� ��û handler]================================

json ProtocolHandler::handle_shift_change_detail(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "shift_change_detail";
   cout << u8"[shift_change_detail] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    const json& data = root["data"];

    // �ʼ� �Ķ���� Ȯ��
    if (!data.contains("staff_uid") || !data.contains("req_year") || !data.contains("req_month")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
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
        response["message"] = u8"�����û��� ���ۿϷ�!";
    }
    else {
        response["resp"] = "fail";
        response["message"] = out_err_msg;
    }
    return response;
}

json ProtocolHandler::handle_shift_change_list(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "shift_change_list"; 
    cout << u8"[shift_change_list] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    const json& data = root["data"];

    if (!data.contains("team_uid") || !data.contains("req_year") || !data.contains("req_month")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
        return response;
    }

    int team_uid = data["team_uid"];
    string year = data["req_year"];
    string month = data["req_month"];
    string year_month = year + "-" + (month.length() == 1 ? "0" + month : month);

    json rows; 
    string err;
    if (db.shift_change_list(team_uid, year_month, rows, err)) {
        response["resp"] = "success";
        response["message"] = "";
        response["data"] = rows;  // �� �迭 �״��
    }
    else {
        response["resp"] = "fail";
        response["message"] = err;
        response["data"] = json::array(); // �� �迭
    }
    return response;
}

json ProtocolHandler::handle_ask_shift_change(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_shift_change";
   cout << u8"[ask_shift_change] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    const json& data = root["data"];

    // �ʼ� �Ķ���� Ȯ��
    if (!data.contains("staff_uid") || !data.contains("date") || !data.contains("duty_type") || !data.contains("message")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
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
        response["message"] = u8"�ٹ������û ó���Ϸ�!";
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
   cout << u8"[cancel_shift_change] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    const json& data = root["data"];

    if (!data.contains("duty_request_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
        return response;
    }
    json result_data;
    string err_msg;

    int duty_request_uid = data["duty_request_uid"];
    if (db.cancel_shift_change(duty_request_uid, result_data, err_msg)) {
        response["resp"] = "success";
        response["data"] = result_data;
        response["message"] = u8"�ٹ�������� ó���Ϸ�!";
    }
    return response;
}

json ProtocolHandler::handle_answer_shift_change(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "answer_shift_change";
    cout << u8"[answer_shift_change] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }

    const json& data = root["data"];

    int duty_request_uid = data["duty_request_uid"];
    string status = data["status"];
    string date = data["date"];
    string admin_msg = data["admin_msg"];
    string err_msg;

    if (db.answer_shift_change(duty_request_uid, status, date, admin_msg, err_msg)) {
        response["resp"] = "success";
        response["message"] = u8"�ٹ������û ����/���� ó���Ϸ�!";
    }
    else {
        response["resp"] = "fail";
        response["message"] = err_msg;
    }
    return response;
}

// ============================[����� handler]================================

json ProtocolHandler::handle_check_in(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_check_in";
   cout << u8"[ask_check_in] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }

    const json& data = root["data"];

    if (!data.contains("staff_uid") || !data.contains("team_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
        return response;
    }

    json result_data;
    string err_msg;
    int staff_uid = data["staff_uid"];
    int team_uid = data["team_uid"];

    if (db.ask_check_in(staff_uid, team_uid, result_data, err_msg)) {
        response["resp"] = "success";
        response["data"] = result_data;
        response["message"] = u8"��� �Ϸ�";
    }
    return response;
}

json ProtocolHandler::handle_check_out(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_check_out";
   cout << u8"[ask_check_out] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }

    const json& data = root["data"];

    if (!data.contains("check_in_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
        return response;
    }

    int check_in_uid = data["check_in_uid"];
    string err_msg;

    if (db.ask_check_out(check_in_uid, err_msg)) {
        response["resp"] = "success";
        response["message"] = u8"��� �Ϸ�";
    }
    return response;
}

json ProtocolHandler::handle_attendance_info(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "attendance_info";
    cout << u8"[attendance_info] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    const json& data = root["data"];

    if (!data.contains("staff_uid")|| !data.contains("date")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
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

json ProtocolHandler::handle_attendance_info_admin(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "attendance_info_admin";
    cout << u8"[attendance_info_admin] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    const json& data = root["data"];

    if (!data.contains("team_uid") || !data.contains("date")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
        return response;
    }
    int team_uid = data["team_uid"];
    string date = data["date"];
    string err_msg;

    nlohmann::json db_json;

    if (!db.get_attendance_info_admin(team_uid, date, db_json, err_msg)) {
        response["resp"] = "fail"; response["message"] = err_msg;
        response["data"] = { {"attendance", {{"check_in_time", nullptr}, {"check_out_time", nullptr}}} };
        return response;
    }

    nlohmann::json att;
    att["check_in_time"] = db_json["check_in_time"];
    att["check_out_time"] = db_json["check_out_time"];
    att["staff_name"] = db_json["staff_name"];

    response["resp"] = "success";
    response["message"] = "ok";
    response["data"] = { {"attendance", att} };
    return response;
}


// ============================[�ٹ�ǥ ���� handler]================================
json ProtocolHandler::handle_gen_schedule_raw(const string& raw_json, DBManager& db) {
    string s = raw_json;
    strip_bom_everywhere(s);
    strip_leading_trailing_noise(s);

    nlohmann::json root = nlohmann::json::parse(s);   // �� ���� �� �Ľ�
    return handle_gen_schedule(root, db);             // �� ���� �ڵ鷯 ����
}

json ProtocolHandler::handle_gen_schedule(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "gen_timeTable";
    cout << u8"[gen_timeTable] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }

    AdminContext ctx;
    string err_msg;

    const json& data = root["data"];
    int admin_uid = data.value("admin_uid", -1);

    // [1] ���� ���� �� year_month ����
    string year = data.value("req_year", "");
    string month = data.value("req_month", "");
    string year_month = year + "-" + (month.length() == 1 ? "0" + month : month);
    cout << "1";
    ctx.admin_uid = admin_uid;
    ctx.year_month = year_month;

    if (!db.get_admin_context_by_uid(admin_uid, ctx, err_msg)) {
        response["resp"] = "fail";
        response["message"] = toUTF8_safely(err_msg);
        return response;
    }

    // [2] �� �Ҽ� ���� ��� ��ȸ
    vector<StaffInfo> staff_list;
    if (!db.get_staff_list_by_team(ctx.team_uid, staff_list, err_msg)) {
        response["resp"] = "fail";
        response["message"] = toUTF8_safely(err_msg);
        return response;
    }
   cout << "2";

    // [3] JSON �迭 ����
    json staff_array = json::array();
    for (const auto& s : staff_list) {
        staff_array.push_back({
            {"name", s.name},
            {"staff_id", s.staff_uid},
            {"grade", s.grade_level},
            {"total_monthly_work_hours", s.monthly_workhour}
            });
    }
   cout << "3";

    //-------------------------------------------------------------------
    // [4] ���̽� ��û Json ����� ��.��
    json py_request = {
    {"protocol", "py_gen_timetable"},
    {"data", {
        {"staff_data", {{"staff", staff_array}}},
        {"position", ctx.position},
        {"target_month", ctx.year_month},
        {"custom_rules", {
            {"shifts", ctx.shift_setting.shifts},
            {"shift_hours", ctx.shift_setting.shift_hours}
        }},
        {"night_shifts", ctx.shift_setting.night_shifts},
        {"off_shifts", ctx.shift_setting.off_shifts}
    }}
    };
    // [5] ���̽� ȣ��
    json py_response;
    if (!TcpServer::connectToPythonServer(py_request, py_response, err_msg)) {
        response["resp"] = "fail";
        response["message"] = toUTF8_safely(err_msg);
        return response;
    }
    cout << "[pyrequest]\n" << py_request.dump(2);
   cout << "4";

    // [6] ���� ����
    if (py_response.value("resp", "") != "success") {
        response["resp"] = "fail";
        response["message"] = py_response.value("message",
            py_response.value("error", u8"���̽� ���� ���� ����"));
        return response;
    }
    cout << "[pyresponse]\n" << py_response.dump(2);

    // [6-1] data ����ȭ: �迭�̵�, ��¥Ű-��ü�� rows�� ����
    json rows = json::array();

    if (py_response.contains("data") && py_response["data"].is_object()) {
        for (auto it = py_response["data"].begin(); it != py_response["data"].end(); ++it) {
            const string date_key = it.key();   // ��¥ ���ڿ�
            const json& arr = it.value();            // �ش� ��¥�� �迭
            if (!arr.is_array()) continue;

            for (const auto& shift_entry : arr) {
                json row = shift_entry;
                row["date"] = date_key;
                rows.push_back(move(row));
            }
        }
    }
    else if (py_response.contains("data") && py_response["data"].is_array()) {
        for (const auto& row : py_response["data"]) rows.push_back(row);
    }
    else {
        throw runtime_error("[JSON structure error] data not found");
    }

    cout << "5-1";

    // [7] DB ����
    for (const auto& row : rows) {
        string date = row.value("date", "");
        string shift = row.value("shift", "");
        int duty_hours = row.value("hours", 0);

        if (!row.contains("people") || !row["people"].is_array()) continue;

        for (const auto& person : row["people"]) {
            int staff_uid = person.value("staff_uid", person.value("staff_id", -1)); // Ű ����
            if (staff_uid < 0) continue;

           string err;
            if (!db.insert_schedule(date, staff_uid, shift, duty_hours, err)) {
               cerr << u8"[DB ���� ����] ��¥:" << date
                    << u8", UID:" << staff_uid << u8", ����:" << toUTF8_safely(err) << "\n";
            }
        }
    }
   cout << "6";

    // [8] ���� ����(���ϸ� ������ �����ٵ� �״�� �����ֱ�)
    response["resp"] = "success";
    response["message"] = u8"�ٹ�ǥ ���� �Ϸ�";
    response["data"] = rows;          // Ŭ�󿡼� �ٷ� ���� ����
    return response;                  // (���� �ڵ�� py_response�� �����ϰ� ����)
}

// ============================[�ٹ�ǥ ��ȸ handler]================================
json ProtocolHandler::handle_ask_timetable_user(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_timetable_user";
   cout << u8"[ask_timetable_user] ��û:\n" << root.dump(2) << endl;

    //[1]
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    const json& data = root["data"];
    if (!data.contains("req_year")|| !data.contains("req_month")|| !data.contains("staff_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
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

json ProtocolHandler::handle_ask_timetable_admin(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_timetable_admin";
    cout << u8"[ask_timetable_admin] ��û:\n" << root.dump(2) << endl;

    // [1] ��ȿ�� üũ
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail"; response["message"] = u8"��û ������ ���� ����"; return response;
    }
    const json& data = root["data"];

    auto get_str = [&](const json& j, const char* k)->string {
        if (!j.contains(k)) return {};
        if (j[k].is_string()) return j[k].get<string>();
        if (j[k].is_number_integer()) return to_string(j[k].get<int>());
        if (j[k].is_number()) return to_string(j[k].get<double>());
        return {};
        };

    if (!data.contains("team_uid")) {
        response["resp"] = "fail"; response["message"] = u8"�ʼ� �Ķ���� ����: team_uid"; return response;
    }

    int team_uid = data["team_uid"].get<int>();
    string req_year = get_str(data, "req_year");
    string req_month = get_str(data, "req_month");
    if (req_year.empty() || req_month.empty()) {
        response["resp"] = "fail"; response["message"] = u8"�ʼ� �Ķ���� ����: req_year/req_month"; return response;
    }

    // [2] �� ��¥ ���� ���: [from, to)
    int y = stoi(req_year);
    int m = stoi(req_month);
    char from_[11], to_[11];
    snprintf(from_, sizeof(from_), "%04d-%02d-01", y, m);
    if (++m == 13) { m = 1; ++y; }
    snprintf(to_, sizeof(to_), "%04d-%02d-01", y, m);

    // [3] DB �ε� (������� �Ϸ�� �迭�� ����)
    json rows; string err;
    if (!db.load_timetable_admin(team_uid, from_, to_, rows, err)) {
        response["resp"] = "fail"; response["message"] = err; return response;
    }

    // [4] ����
    response["resp"] = "success";
    response["message"] = u8"�ٹ�ǥ ���� �Ϸ�";
    response["data"] = rows; // ���ϴ� ���� �迭 ���� �״��
    return response;
}

json ProtocolHandler::handle_check_today_duty(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "check_today_duty";
    cout << u8"[check_today_duty] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        return {
            {"protocol", "check_today_duty"},
            {"resp", "fail"},
            {"message", u8"��û ������ ���� ����"}
        };
    }

    const auto& data = root["data"];
    if (!data.contains("date") || !data.contains("team_uid")) {
        return {
            {"protocol", "check_today_duty"},
            {"resp", "fail"},
            {"message", u8"�ʼ� �Ķ���� ����"}
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
    response["data"] = duty_array; // �ٷ� �迭
    response["message"] = u8"��ȸ ����";
    return response;
}

json ProtocolHandler::handle_ask_timetable_weekly(const json& root, DBManager& db) {
    json response;

    response["protocol"] = "ask_timetable_weekly";
    cout << u8"[ask_timetable_weekly] ��û:\n" << root.dump(2) << endl;
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail"; response["message"] = u8"��û ������ ���� ����";
        response["data"] = { {"shift_type", nullptr} };
        return response;
    }
    const auto& d = root["data"];
    int staff_uid = d.value("staff_uid", -1);
    string ymd = d.value("date", ""); // ���� ��¥
    if (staff_uid < 0 || ymd.empty()) {
        response["resp"] = "fail"; response["message"] = u8"�ʼ� �Ķ���� ����";
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
    response["message"] = string(u8"�ְ� �ٹ�ǥ");
    response["data"] = out;  // {"shift_type":[7�� ���ڿ�]}
    return response;
}



// ============================[�μ��ΰ� handler]================================
json ProtocolHandler::handle_ask_handover_list(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_handover_list";
   cout << u8"[ask_handover_list] ��û:\n" << root.dump(2) << endl;

    // [1] ��û �Ľ�
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }

    const  json& data = root["data"];

    if (!data.contains("team_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
        return response;
    }
    int team_uid = data["team_uid"];
    vector<HandoverNoteInfo> note_list;
    string err_msg;

    // [2] DB���� �μ��ΰ� ��� ��������
    if (!db.get_handover_notes_by_team(team_uid, note_list, err_msg)) {
        response["resp"] = "fail";
        response["message"] = err_msg;
        return response;
    }

    // [3] JSON ��ȯ
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

    // [4] ���� ����
    response["resp"] = "success";
    response["data"]["list"] = list_array;
	response["data"]["team_uid"] = team_uid;
    return response;
}

json ProtocolHandler::handle_ask_handover_detail(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_handover_detail";
   cout << u8"[ask_handover_detail] ��û:\n" << root.dump(2) << endl;

    // [1] ��û �Ľ�
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }

    const  json& data = root["data"];

    if (!data.contains("handover_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
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
    cout << u8"[reg_handover] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        resp["resp"] = "fail";
        resp["message"] = u8"��û ������ ���� ����";
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
        resp["message"] = u8"�ʼ� �Ķ���� ����";
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
    resp["message"] = u8"�μ��ΰ� ��� �Ϸ�";
    resp.update(db_json); 
    cout << u8"���������: " << resp.dump(2);
    return resp;
}

json ProtocolHandler::handle_summary_journal(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "summary_journal";
    cout << u8"[summary_journal] ��û:\n" << root.dump(2) << endl;
    // [1] ��û �Ľ�
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    const auto& d = root["data"];
    string input_text = d.value("text", "");

    // [1] ���̽� ��û
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
    // [2] ���̽� ���� ����
    if (py_res.value("resp", "") != "success") {
        response["resp"] = "fail";
        response["message"] = py_res.value("message",
        response.value("error", u8"���̽� ���� ���� ����"));
        response["data"] = { {"text", ""} };
        return response;
    }
    if (!py_res.contains("data") || !py_res["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"[JSON ����] data ����";
        response["data"] = { {"text", ""} };
        return response;
    }

    // [3] ��� ����
    string summary = py_res["data"].value("result", "");
    response["resp"] = "success";
    response["message"] = u8"��� �Ϸ�";
    response["data"] = { {"text", summary} };
    return response;
}


// ============================[�������� handler]================================

json ProtocolHandler::handle_ask_notice_list(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_notice_list";
   cout << u8"[ask_notice_list] ��û:\n" << root.dump(2) << endl;
    // [1] ��û �Ľ�
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    const json& data = root["data"];

    if (!data.contains("team_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
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
    cout << u8"[ask_notice_detail] ��û:\n" << root.dump(2) << endl;
    // [1] ��û �Ľ�
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    const json& data = root["data"];

    if (!data.contains("notice_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
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

// ============================[��ȸ handler]================================

json ProtocolHandler::handle_ask_user_info(const json & root, DBManager & db) {
    json response;
    response["protocol"] = "ask_user_info";
    cout << u8"[handle_ask_user_info] ��û:\n" << root.dump(2) << endl;
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
	}

    int team_uid = root["data"].value("team_uid", -1);
    int staff_uid = root["data"].value("staff_uid", -1);
    if (team_uid < 0 || staff_uid < 0) {
        response["resp"] = "fail"; response["message"] = u8"�ʼ� ���� ����"; return response;
    }

    UserInfo info; string err;
    if (!db.build_user_info_from_meta(team_uid, staff_uid, info, err)) {
        response["resp"] = "fail"; response["message"] = err; return response;
    }

    response["resp"] = "success";
    response["message"] = u8"���� ��ȸ�Ϸ�!";
    response["data"] = {
        {"id",            info.id},
        {"pw",            info.pw},             
        {"phone_number",  info.phone_number},
        {"company_name",  info.company_name},
        {"grade_name",    info.grade_name}
    };
    return response;
}

json ProtocolHandler::handle_ask_staff_list(const json & root, DBManager & db) {
    json response;
    response["protocol"] = "ask_staff_list";
    cout << u8"[ask_staff_list] ��û:\n" << root.dump(2) << endl;
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    const json& data = root["data"];
    if (!data.contains("team_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
        return response;
    }
    int team_uid = data["team_uid"];
    vector<StaffInfo> meta;
    string err_msg;
    if (!db.get_staff_list_by_team(team_uid, meta, err_msg)) {
        response["resp"] = "fail";
        response["message"] = err_msg;
        return response;
    }
    vector<StaffInfo> tmp_list;
    db.build_tmp_staff_from_meta(meta, tmp_list, /*tmp_flag=*/1);
    json arr = json::array();
    for (const auto& s : tmp_list) {
        arr.push_back({
            {"grade_level",  s.grade_level},
            {"grade_name",   s.grade_name},
            {"phone_num",    s.phone},
            {"temp_id",      s.id},
            {"temp_pw",      s.pw},                 
            {"total_hours",  s.monthly_workhour},
            {"staff_name",   s.name}
        });
    }
	response["resp"] = "success";
    response["message"] = u8"���� ��� ��ȸ �Ϸ�";
    response["data"] = {
        {"team_uid", team_uid},
        {"staff_list", arr}
    };
	return response;
}

json ProtocolHandler::handle_req_staff_list(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "req_staff_list";
    cout << u8"[req_staff_list] ��û:\n" << root.dump(2) << endl;
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    const json& data = root["data"];
    if (!data.contains("team_uid")) {
        response["resp"] = "fail";
        response["message"] = u8"�ʼ� �Ķ���� ����";
        return response;
    }
    int team_uid = data["team_uid"];
    vector<StaffInfo> staff_list;
    string err_msg;
    if (!db.get_staff_list_by_team(team_uid, staff_list, err_msg)) {
        response["resp"] = "fail";
        response["message"] = err_msg;
        return response;
    }
    json arr = json::array();
    for (const auto& s : staff_list) {
        arr.push_back({
            {"grade_level",  s.grade_level},
			{"grade_name",   s.grade_name},
            {"phone_num",    s.phone},
            {"total_hours",  s.monthly_workhour},
            {"staff_uid",    s.staff_uid},
            {"staff_name",   s.name}
        });
    }
    response["resp"] = "success";
    response["message"] = u8"���� ��� ��ȸ �Ϸ�";
    response["data"] = { {"team_uid", team_uid}, {"staff_list", arr} };
    return response;
}