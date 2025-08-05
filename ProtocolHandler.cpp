#include "ProtocolHandler.h"
#include "DBManager.h"
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
        response["message"] = u8"��ȸ ����!";
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
        response["message"] = u8"��ȸ ����!";
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

    int duty_request_uid = data[duty_request_uid];
    if (db.cancel_shift_change(duty_request_uid)) {
        response["resp"] = "success";
        response["data"] = result_data;
        response["message"] = u8"��ȸ ����!";
    }
}