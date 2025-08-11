#pragma once
#include "struct.h"
#include "DateUtil.h"
#include <nlohmann/json.hpp>

using json = nlohmann::json;

class DBManager;

class ProtocolHandler
{
public:
    //�α���
    static json handle_login                (const json& json, DBManager& db);
    static json handle_login_admin          (const json& root, DBManager& db);

    //��� ��û
    static json handle_rgs_team_info        (const json& root, DBManager& db);
    static json handle_rgs_grade_info       (const json& root, DBManager& db);
    static json handle_rgs_shift_info       (const json& root, DBManager& db);
    static json handle_rgs_staff_info       (const json& root, DBManager& db);

    //�ٹ� ���� ��û ����
    static json handle_shift_change_detail  (const json& root, DBManager& db);
    static json handle_ask_shift_change     (const json& root, DBManager& db);
    static json handle_cancel_shift_change  (const json& root, DBManager& db);

    //����� ����
    static json handle_check_in             (const json& root, DBManager& db);
    static json handle_check_out            (const json& root, DBManager& db);
    static json handle_attendance_info      (const json& root, DBManager& db);

    //�ٹ�ǥ ����
    static json handle_gen_schedule         (const json& root, DBManager& db);
    static json handle_ask_timetable_user   (const json& root, DBManager& db);
    static json handle_ask_timetable_admin  (const json& root, DBManager& db);
    static json handle_ask_timetable_weekly(const json& root, DBManager& db);
    static json handle_check_today_duty     (const json& root, DBManager& db);

    //�μ��ΰ� ����
    static json handle_ask_handover_list    (const json& root, DBManager& db);
    static json handle_ask_handover_detail  (const json& root, DBManager& db);
    static json handle_reg_handover         (const json& root, DBManager& db);
    static json handle_summary_journal      (const json& json, DBManager& db);

    //�������� ����
    static json handle_ask_notice_list      (const json& root, DBManager& db);
    static json handle_ask_notice_detail    (const json& root, DBManager& db);

    //��ȸ ����
	static json handle_ask_user_info        (const json& root, DBManager& db);
	static json handle_ask_staff_list       (const json& root, DBManager& db);
};

//������� ���� �ľ� �� json �Ľ� �� �������� �б� �� DBManager�� ���� ����
//�� ����� ProtocolHandler�� ���� �� ���� JSON ���� �� send�� Ŭ���̾�Ʈ�� ��ȯ��