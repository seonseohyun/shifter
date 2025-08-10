#pragma once

#include <string>
#include <vector>
#include <map>

// 전체 교대 설정 정보
struct ShiftSetting {
    std::vector<std::string> shifts;
    std::map<std::string, int> shift_hours;
    std::vector<std::string> night_shifts;
    std::vector<std::string> off_shifts;
};

// 관리자별 전체 컨텍스트
struct AdminContext {
    int admin_uid = -1;
    int team_uid = -1;
    std::string team_name;
    std::string year_month;
    ShiftSetting shift_setting;
};

// 직원 정보 구조체
struct StaffInfo {
    int staff_uid = -1;
    std::string name;
    int grade = -1;
    int monthly_workhour = -1;
};

// 인수인계 정보 구조체
struct HandoverNoteInfo {
    int handover_uid = -1;
    int staff_uid = -1;
    int team_uid = -1;
    std::string staff_name;
    std::string handover_time;
    std::string shift_type;
    std::string note_type;
    std::string title;
    std::string text;
    std::string text_particular;
    std::string additional_info;
    std::string text_refine;
    int is_refined = -1;
    std::string file_name;

};

//근무 일정 구조체
struct ScheduleEntry {
    int schedule_uid = -1;
    int staff_uid = -1;
    int hours = -1;
    std::string duty_date;   // YYYY-MM-DD
    std::string shift_type;  // "Day", "Night", "Off" 등
};

struct DutyToday{
    std::string shift;
    std::vector<std::string> staff_names;
};

// 공지사항 구조체
struct NoticeSummary {
    int notice_uid = -1;
    std::string staff_name;
    std::string notice_date;   // "YYYY-MM-DD"
    std::string title;
};
// 공지사항 디테일 구조체 
struct NoticeDetail {
    int notice_uid = -1;
    std::string staff_name;
    std::string notice_date;
    std::string title;
    std::string content;
};

//정보 등록 구조체
struct ShiftInfo {
    std::string duty_type;
    std::string start_time;
    std::string end_time;
    int duty_hours = -1;
};

// 직급 등록 구조체
struct GradeInfo {
    int grade_level = -1;
    std::string grade_name;
};