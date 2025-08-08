#pragma once

#include <string>
#include <vector>
#include <map>

// ��ü ���� ���� ����
struct ShiftSetting {
    std::vector<std::string> shifts;
    std::map<std::string, int> shift_hours;
    std::vector<std::string> night_shifts;
    std::vector<std::string> off_shifts;
};

// �����ں� ��ü ���ؽ�Ʈ
struct AdminContext {
    int admin_uid = -1;
    int team_uid = -1;
    std::string team_name;
    std::string year_month;
    ShiftSetting shift_setting;
};

// ���� ���� ����ü
struct StaffInfo {
    int staff_uid = -1;
    std::string name;
    int grade = -1;
    int monthly_workhour = -1;
};

// �μ��ΰ� ���� ����ü
struct HandoverNoteInfo {
    int handover_uid;
    int staff_uid;
    int team_uid;
    std::string staff_name;
    std::string handover_time;
    std::string shift_type;
    std::string note_type;
    std::string title;
    std::string text;
    std::string text_particular;
    std::string additional_info;
    std::string text_refine;
    int is_refined;
};

//�ٹ� ���� ����ü
struct ScheduleEntry {
    int schedule_uid;
    int staff_uid;
    int hours;
    std::string duty_date;   // YYYY-MM-DD
    std::string shift_type;  // "Day", "Night", "Off" ��
};
