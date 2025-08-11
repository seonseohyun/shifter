#pragma once
#include "struct.h"
#include "DateUtil.h"
#include <nlohmann/json.hpp>

using json = nlohmann::json;

class DBManager;

class ProtocolHandler
{
public:
    //로그인
    static json handle_login                (const json& json, DBManager& db);
    static json handle_login_admin          (const json& root, DBManager& db);

    //등록 요청
    static json handle_rgs_team_info        (const json& root, DBManager& db);
    static json handle_rgs_grade_info       (const json& root, DBManager& db);
    static json handle_rgs_shift_info       (const json& root, DBManager& db);
    static json handle_rgs_staff_info       (const json& root, DBManager& db);

    //근무 변경 요청 관련
    static json handle_shift_change_detail  (const json& root, DBManager& db);
    static json handle_ask_shift_change     (const json& root, DBManager& db);
    static json handle_cancel_shift_change  (const json& root, DBManager& db);

    //출퇴근 관련
    static json handle_check_in             (const json& root, DBManager& db);
    static json handle_check_out            (const json& root, DBManager& db);
    static json handle_attendance_info      (const json& root, DBManager& db);

    //근무표 관련
    static json handle_gen_schedule         (const json& root, DBManager& db);
    static json handle_ask_timetable_user   (const json& root, DBManager& db);
    static json handle_ask_timetable_admin  (const json& root, DBManager& db);
    static json handle_ask_timetable_weekly(const json& root, DBManager& db);
    static json handle_check_today_duty     (const json& root, DBManager& db);

    //인수인계 관련
    static json handle_ask_handover_list    (const json& root, DBManager& db);
    static json handle_ask_handover_detail  (const json& root, DBManager& db);
    static json handle_reg_handover         (const json& root, DBManager& db);
    static json handle_summary_journal      (const json& json, DBManager& db);

    //공지사항 관련
    static json handle_ask_notice_list      (const json& root, DBManager& db);
    static json handle_ask_notice_detail    (const json& root, DBManager& db);

    //조회 관련
	static json handle_ask_user_info        (const json& root, DBManager& db);
	static json handle_ask_staff_list       (const json& root, DBManager& db);
};

//“헤더로 길이 파악 → json 파싱 → 프로토콜 분기 → DBManager로 로직 실행
//→ 결과를 ProtocolHandler로 전달 → 응답 JSON 구성 → send로 클라이언트에 반환”