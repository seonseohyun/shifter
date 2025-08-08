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

// ============================[�α��� handler]================================
json ProtocolHandler::handle_login(const json& root, DBManager& db) {
    nlohmann::json response;
    response["protocol"] = "login";
    cout << u8"[login] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = "��û ������ ���� ����";
        return response;
    }

    const nlohmann::json& data = root["data"];

    std::string id = data.value("id", "");
    std::string pw = data.value("pw", "");

    if (id.empty() || pw.empty()) {
        response["resp"] = "fail";
        response["message"] = u8"���̵� �Ǵ� ��й�ȣ ����";
        return response;
    }

    json result_data;
    string out_err_msg;

    if (db.login(id, pw, result_data, out_err_msg)) {
        int staff_uid = result_data.value("staff_uid", -1);
        int team_uid = result_data.value("team_uid", -1);

        string att_err;
        string req_err;
        db.get_today_attendance(staff_uid, team_uid, result_data, att_err);
        db.get_request_status_count(staff_uid, result_data, req_err);

        response["resp"] = "success";
        response["data"] = result_data;
        response["message"] = u8"�α��� ����";

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
    cout << u8"[login_admin] ��û:\n" << root.dump(2) << endl;
    //[1] �ʼ� ���� üũ
    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    //[2] Ŭ���̾�Ʈ���� ���� data ���� �� ����
    const nlohmann::json& data = root["data"];

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
    const nlohmann::json& data = root["data"];

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

json ProtocolHandler::handle_ask_shift_change(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "ask_shift_change";
    cout << u8"[ask_shift_change] ��û:\n" << root.dump(2) << endl;

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = u8"��û ������ ���� ����";
        return response;
    }
    const nlohmann::json& data = root["data"];

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
    const nlohmann::json& data = root["data"];

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

    const nlohmann::json& data = root["data"];

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

    const nlohmann::json& data = root["data"];

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

// ============================[�ٹ�ǥ ���� handler]================================

json ProtocolHandler::handle_gen_schedule(const json& root, DBManager& db) {
    json response;
    response["protocol"] = "gen_timeTable";

    if (!root.contains("data") || !root["data"].is_object()) {
        response["resp"] = "fail";
        response["message"] = "��û ������ ���� ����";
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

    ctx.admin_uid = admin_uid;
    ctx.year_month = year_month;

    if (!db.get_admin_context_by_uid(admin_uid, ctx, err_msg)) {
        response["resp"] = "fail";
        response["message"] = err_msg;
        return response;
    }

    // [2] �� �Ҽ� ���� ��� ��ȸ
    vector<StaffInfo> staff_list;
    if (!db.get_staff_list_by_team(ctx.team_uid, staff_list, err_msg)) {
        response["resp"] = "fail";
        response["message"] = err_msg;
        return response;
    }

    // [3] JSON �迭 ����
    json staff_array = json::array();
    for (const auto& s : staff_list) {
        staff_array.push_back({
            {"name", s.name},
            {"staff_id", s.staff_uid},
            {"grade", s.grade},
            {"total_monthly_work_hours", s.monthly_workhour}
            });
    }
    //-------------------------------------------------------------------
    // [4] ���̽� ��û Json ����� ��.��
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
    // [5] ���̽� ���� ȣ���ϱ�
    json py_response;
    if (!TcpServer::connectToPythonServer(py_request, py_response, err_msg)) {
        response["resp"] = "fail";
        response["message"] = err_msg;
        return response;
    }
    // [6] ���� �� �Ľ��ϰ� DB INSERT
    if (py_response.value("status", "") != "ok") {
        response["resp"] = "fail";
        response["message"] = "���̽� ���� ���� ����";
        return response;
    }

    const json& schedule = py_response["schedule"];

    // [7] DB ����
    for (const auto& item : schedule.items()) {
        const std::string& date = item.key();
        const json& shift_list = item.value();

        for (const auto& shift_entry : shift_list) {
            std::string shift_type = shift_entry["shift"];
            const auto& people = shift_entry["people"];

            for (const auto& person : people) {
                int staff_uid = person.value("������ȣ", -1);
                if (staff_uid == -1) continue;

                std::string err;
                if (!db.insert_schedule(date, staff_uid, shift_type, err)) {
                    std::cerr << "[DB ���� ����] ��¥: " << date << ", UID: " << staff_uid << ", ����: " << err << "\n";
                }
            }
        }
    }

    // [8] ���� ���� ����
    response["resp"] = "success";
    response["message"] = "�ٹ�ǥ ���� �Ϸ�";
    return py_response;
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
    const nlohmann::json& data = root["data"];
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

    const nlohmann::json& data = root["data"];

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

    const nlohmann::json& data = root["data"];

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
       {"shift_type", note.shift_type},
       {"note_type", note.note_type},
       {"title", note.title},
       {"text", note.text},
       {"text_particular", note.text_particular},
       {"additional_info", note.additional_info},
       {"is_attached", note.is_refined},
       {"file_name", ""}  // ÷�� ������ ����
    };
    response["resp"] = "success";
    return response;
}

