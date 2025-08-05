#pragma once
#include <mariadb/conncpp.hpp>
#include <memory>
#include <string>
#include <nlohmann/json.hpp>

using namespace std;
using json = nlohmann::json;

class DBManager
{
public:
    DBManager();
    ~DBManager();

    // DB 연결
    bool connect();

    // 로그인
    bool login      (const string& id, const string & pw, json& out_data, string& out_err_msg);
    bool login_admin(const string& admin_id, const string& admin_pw, json& out_data, string& out_err_msg);

    //근무 변경
    bool shift_change_detail (int staff_uid, const string& year_month, json& out_data, string& out_err_msg);
    bool ask_shift_change    (int staff_uid, const string& yyyymmdd, const string& duty_type,
                             const string& reason, string& out_err_msg);
    //bool cancel_shift_change(int& duty_request_uid, json& out_data, string& out_err_msg);
private:
    unique_ptr<sql::Connection> conn_;

};

