#pragma once
#include <mariadb/conncpp.hpp>
#include <memory>
#include <string>
#include <nlohmann/json.hpp>
#include "struct.h"

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
    bool login        (const string& id, const string & pw, json& out_data, string& out_err_msg);
    bool login_admin  (const string& admin_id, const string& admin_pw, json& out_data, string& out_err_msg);

    // 근무 변경
    bool ask_shift_change    (int staff_uid, const string& yyyymmdd, const string& duty_type,
                             const string& reason, string& out_err_msg);
    bool cancel_shift_change (int& duty_request_uid, json& out_data, string& out_err_msg);
    void get_request_status_count(int staff_uid, json& out_data, string& out_err_msg);
    bool shift_change_detail (int staff_uid, const string& year_month, json& out_data, string& out_err_msg);

    // 출퇴근
    bool ask_check_in        (int staff_uid, int team_uid, json& out_data, string& out_err_msg);
    bool ask_check_out       (int check_in_uid, string& out_err_msg);
    void get_today_attendance(int staff_uid, int team_uid, json& out_data, string& out_err_msg);

    // 근무표 생성
    bool get_staff_list_by_team  (int team_uid, vector<StaffInfo>& out_staffs, string& out_err_msg);
    bool get_admin_context_by_uid(int admin_uid, AdminContext& out_ctx, string& out_err_msg);
    bool insert_schedule         (const string& date, int staff_uid, const string& shift_type, string& out_err_msg);

    // 근무표 조회
    vector<ScheduleEntry> get_team_schedule(int team_uid, const std::string& target_month);
    vector<ScheduleEntry> get_staff_schedule(int team_uid, const std::string& target_month);

    // 인수인계
    bool get_handover_notes_by_team     (int team_uid, vector<HandoverNoteInfo>& out_notes, string& out_err_msg);
    bool get_handover_notes_by_uid      (int team_uid, HandoverNoteInfo& out_note, string& out_err_msg);
    bool ask_handover_list(int team_uid, vector<HandoverNoteInfo>& note_list, string& out_err_msg);


private:
    unique_ptr<sql::Connection> conn_;

};

