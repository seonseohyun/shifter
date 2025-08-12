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

    // 로그인 [유저/관리자]
    bool login                (const string& id, const string & pw, json& out_data, string& out_err_msg);
    bool login_admin          (const string& admin_id, const string& admin_pw, json& out_data, string& out_err_msg);
    bool get_staff_info_by_uid(int staff_uid, StaffInfo& out_staff, string& out_err_msg);
    
    // 개인정보 [등록/ 수정]
	bool register_grade_info    (int team_uid, int admin_uid, const vector<GradeInfo>& grades, string& out_err);
    bool register_team_info     (const string& company_name_in, const string& team_name_in, const string& job_category_in, const json& shift_info, json& out_json, string& out_err);
    bool register_staff_info    (int team_uid, int grade_level, const string& name, const string& phone, int monthly_workhour,
                                string& out_id, string& out_pw, string& out_err);
	bool modify_user_info       (int staff_uid, const string& new_pw, string& out_err_msg);

    // 근무 변경 [요청/취소/조회/상세]
    bool ask_shift_change           (int staff_uid, const string& yyyymmdd, const string& duty_type, const string& reason, string& out_err_msg);
    bool cancel_shift_change        (int& duty_request_uid, json& out_data, string& out_err_msg);
    void get_request_status_count   (int staff_uid, json& out_data, string& out_err_msg);
    bool shift_change_detail        (int staff_uid, const string& year_month, json& out_data, string& out_err_msg);
	bool shift_change_list          (int team_uid, const string& year_month, json& out_data, string& out_err_msg);
    bool answer_shift_change        (int duty_request_uid, string status, string date, const string& admin_msg, string& out_err_msg);
	bool modify_schedule            (const json& mdf_infos, string& out_err);
    
    
    // 조회
    bool req_shift_info_by_team              (int team_uid, vector<ShiftInfo>& out_list, string& out_err_msg);
    bool build_tmp_staff_from_meta           (const vector<StaffInfo>& meta, vector<StaffInfo>& out_list, int tmp_flag);
    bool get_tmp_staff_list_by_team_from_meta(int team_uid,  vector<StaffInfo>& out_list,  string& out_err_msg, int tmp_flag);
    bool build_user_info_from_meta           (int team_uid, int staff_uid, UserInfo& out_info, string& out_err);

    // 출퇴근
    bool ask_check_in             (int staff_uid, int team_uid, json& out_data, string& out_err_msg);
    bool ask_check_out            (int check_in_uid, string& out_err_msg);
    bool get_today_attendance     (int staff_uid, int team_uid, json& out_data, string& out_err_msg);
    bool get_attendance_info      (int staff_uid, const string& ymd,string& check_in, string& check_out,string& err);
	bool get_attendance_info_admin(int team_uid, const string& ymd, json& out_data, string& out_err_msg);

    // 근무표 생성
    bool get_staff_list_by_team  (int team_uid, vector<StaffInfo>& out_staffs, string& out_err_msg);
    bool get_admin_context_by_uid(int admin_uid, AdminContext& out_ctx, string& out_err_msg);
    bool insert_schedule         (const string& date, int staff_uid, const string& shift_type, int duty_hours, string& out_err_msg);
    bool load_timetable_admin    (int team_uid, const string& from_date, const string& to_date, json& out_array, string& out_err_msg);

    // 근무표 조회
    vector<ScheduleEntry> get_team_schedule (int team_uid, const string& target_month);
    vector<ScheduleEntry> get_staff_schedule(int team_uid, const string& target_month);
    bool check_today_duty_for_admin         (int team_uid, const string& date, json& out_json, string& out_err_msg);
    bool get_weekly_shift_mon_sun_compact   (int staff_uid, const string& date, json& out, string& err);
    bool chk_timeTable_can_generate         (int team_uid, const std::string& yyyy_mm, bool& out_can_generate, std::string& out_err);

    // 인수인계
    bool get_handover_notes_by_team (int team_uid, vector<HandoverNoteInfo>& out_notes, string& out_err_msg);
    bool get_handover_notes_by_uid  (int team_uid, HandoverNoteInfo& out_note, string& out_err_msg);

    bool reg_handover(int staff_uid, int team_uid, const string& title, const string& text, const string& text_particular,
                      const string& additional_info, int is_attached, const string& file_name, string& note_type, string& shift_type, json& out_json,  string& out_err_msg);
   
    // 공지사항
    bool get_notice_list_by_team (int team_uid, vector<NoticeSummary>& out_list, string& out_err_msg);
    bool get_notice_detail_by_uid(int notice_uid, NoticeDetail& out_detail, string& out_err_msg);

private:
    unique_ptr<sql::Connection> conn_;

};

