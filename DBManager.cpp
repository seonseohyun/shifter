#include "DBManager.h"
#include "DateUtil.h"
#include <iostream>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <windows.h>
/*SELECT JSON_OBJECT('PROTOCOL','1','CLIENT_NUM',u.id,'IOT_INFO',JSON_ARRAYAGG(JSON_OBJECT('LOCATION_CODE',d.location_code,'DEVICE_TYPE_CODE',d.device_type,'POWER',d.power,'TEMP',d.temp))) FROM device d JOIN user u ON d.user_id = u.id WHERE u.addr_id = '{ADDR_ID}';*/
using namespace std;
using json = nlohmann::json;

DBManager::DBManager() {}
DBManager::~DBManager() {}

//============ [DB ����] ============
bool DBManager::connect() {
    try {
        sql::Driver* driver = sql::mariadb::get_driver_instance();
        sql::SQLString url("jdbc:mariadb://127.0.0.1:3306/shifter");

        sql::Properties properties;
        properties["user"] = "seonseo";
        properties["password"] = "1234";

        properties["useSsl"] = "true";
        properties["sslMode"] = "VERIFY_CA";
        properties["serverSslCert"] = "certs/ca.pem";  // ��θ� ������ OK

        conn_.reset(driver->connect(url, properties));
        return true;

    }
    catch (sql::SQLException& e) {
        cerr << u8" {{(>_<)}} DB ���� ����: " << e.what() << endl;
        return false;
    }
}

//============ [�α��� - ����] ============
bool DBManager::login(const string& id, const string& pw, json& out_data, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB ����] DB ���� ����";
        return false;
    }

    if (id.empty() || pw.empty()) {
        out_err_msg = u8"[�Է� ����] ���̵� �Ǵ� ��й�ȣ�� ��� �ֽ��ϴ�.";
        return false;
    }

    try {
        string query =
            "SELECT s.staff_uid, s.team_uid, t.team_name "
            "FROM staff s "
            "JOIN team t ON s.team_uid = t.team_uid "
            "WHERE s.id = ? AND s.pw = ?";

        auto pstmt = conn_->prepareStatement(query);
        pstmt->setString(1, id);
        pstmt->setString(2, pw);
        auto res = pstmt->executeQuery();

        if (!res->next()) {
            out_err_msg = u8"���̵� �Ǵ� ��й�ȣ�� ��ġ���� �ʽ��ϴ�.";
            return false;
        }

        string today = DateUtil::get_today();
        out_data["date"] = today;
        out_data["staff_uid"] = res->getInt("staff_uid");
        out_data["team_uid"] = res->getInt("team_uid");
        out_data["team_name"] = res->getString("team_name");

        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string(u8"SQL ���� �߻�: ") + e.what();
        return false;
    }
}
//============ [�α��� - ������] ============
bool DBManager::login_admin(const string& admin_id, const string& admin_pw, json& out_data, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB ����] DB ���� ����";
        return false;
    }
    try {
        // [1] �α��� üũ
        unique_ptr<sql::PreparedStatement> checklogin(
            conn_->prepareStatement("SELECT admin_uid, team_uid FROM admin WHERE admin_id = ? AND admin_pw = ?")
        );
        checklogin->setString(1, admin_id);
        checklogin->setString(2, admin_pw);

        unique_ptr<sql::ResultSet> res(checklogin->executeQuery());

        if (!res->next()) {
            out_err_msg = u8"���̵� �Ǵ� ��й�ȣ�� ��ġ���� �ʽ��ϴ�.";
            return false;
        }

        // [2] admin_uid, team_uid ����
        out_data["admin_uid"] = res->getInt("admin_uid");
        int team_uid = res->isNull("team_uid") ? -1 : res->getInt("team_uid");
        out_data["team_uid"] = team_uid;

        // [3] team_name ��ȸ (team_uid�� �ִ� ��츸)
        if (team_uid != -1) {
            unique_ptr<sql::PreparedStatement> teamname(
                conn_->prepareStatement("SELECT team_name FROM team WHERE team_uid = ?")
            );
            teamname->setInt(1, team_uid);

            unique_ptr<sql::ResultSet> res_team(teamname->executeQuery());
            if (res_team->next()) {
                out_data["team_name"] = res_team->getString("team_name");
            }
            else {
                out_data["team_name"] = ""; // �� ����
            }
        }
        else {
            out_data["team_name"] = ""; // �� ����
        }

        return true;
    }
    catch (sql::SQLException& e) {
        out_err_msg = string(u8"SQL ���� �߻�: ") + e.what();
        return false;
    }
}

//============ [�ٹ� ���� ������ ��ȸ - ����] ============
bool DBManager::shift_change_detail (int staff_uid, const string& year_month, json& out_data, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"�� [DB ����] DB ���� ����";
        return false;
    }
    try {
        // [1] INSERT 
        string query =
            "SELECT duty_request_uid, request_date, desire_shift, status, reason, admin_msg "
            "FROM duty_request "
            "WHERE staff_uid = ? AND DATE_FORMAT(request_date, '%Y-%m') = ? AND is_deleted = 0 "
            "ORDER BY request_date ASC";

        unique_ptr<sql::PreparedStatement> get_shift_detail(conn_->prepareStatement(query));

        get_shift_detail->setInt(1, staff_uid);
        get_shift_detail->setString(2, year_month);

        unique_ptr<sql::ResultSet> res(get_shift_detail->executeQuery());
        json result = json::array();

        while (res->next()) {
            json row;
            row["duty_request_uid"] = res->getInt("duty_request_uid");
            row["request_date"] = res->getString("request_date");
            row["desire_shift"] = res->getString("desire_shift");
            row["status"] = res->getString("status");
            row["reason"] = res->getString("reason");

            if (res->isNull("admin_msg"))
                row["admin_msg"] = nullptr;
            else
                row["admin_msg"] = res->getString("admin_msg");
            result.push_back(row);
        }
        out_data = result;
        return true;
    }
    catch (sql::SQLException& e) {
        out_err_msg = string(u8"SQL ���� �߻�: ") + e.what();
        return false;
    }
}
//============ [�ٹ� ���� ��û ��� - ����] ============
bool DBManager::ask_shift_change(int staff_uid, const string& yyyymmdd, const string& duty_type, const string& reason, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB ����] DB ���� ����";
        return false;
    }

    try {
        // [1] staff_uid�� team_uid ��ȸ"
        int team_uid = -1;
        {
            unique_ptr<sql::PreparedStatement> pstmt(
                conn_->prepareStatement("SELECT team_uid FROM staff WHERE staff_uid = ?")
            );
            pstmt->setInt(1, staff_uid);
            unique_ptr<sql::ResultSet> res(pstmt->executeQuery());

            if (!res->next()) {
                out_err_msg = u8"[����] staff_uid�� �������� �ʽ��ϴ�.";
                return false;
            }
            team_uid = res->getInt("team_uid");
        }

        // [2] ��¥ ���� Ȯ�� (��: "2025-08-05")
        if (yyyymmdd.size() != 10 || yyyymmdd[4] != '-' || yyyymmdd[7] != '-') {
            out_err_msg = u8"��¥ ���� ���� (��: 2025-08-05�� �۽Źٶ��ϴ�.)";
            return false;
        }

        // [3] INSERT
        unique_ptr<sql::PreparedStatement> insert_stmt(
            conn_->prepareStatement(
                "INSERT INTO duty_request (staff_uid, team_uid, request_date, desire_shift, status, reason) "
                "VALUES (?, ?, ?, ?, 'pending', ?)"
            )
        );
        insert_stmt->setInt(1, staff_uid);
        insert_stmt->setInt(2, team_uid);
        insert_stmt->setString(3, yyyymmdd); 
        insert_stmt->setString(4, duty_type);
        insert_stmt->setString(5, reason);

        insert_stmt->executeUpdate();

        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string(u8"SQL ���� �߻�: ") + e.what();
        return false;
    }
}
//============ [�ٹ� ���� ��û ���� - ����] ============
bool DBManager::cancel_shift_change(int& duty_request_uid, json& out_data, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB ����] DB ���� ����";
        return false;
    }
    try {
        string query = "UPDATE duty_request SET is_deleted = 1 WHERE duty_request_uid = ?";
        unique_ptr<sql::PreparedStatement> cancel_duty(conn_->prepareStatement(query));
        cancel_duty->setInt(1, duty_request_uid);

        int rows_affected = cancel_duty->executeUpdate();
        if (rows_affected == 0) {
            out_err_msg = "�ش� ��û�� �������� �ʽ��ϴ�.";
            return false;
        }
        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string("SQL ���� �߻�: ") + e.what();
        return false;
    }
}

//============ [��� ��û - ����] ============
bool DBManager::ask_check_in(int staff_uid, int team_uid, json& out_data, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB ����] DB ���� ����";
        return false;
    }
    try {
        //[1] INSERT
        string query = "INSERT INTO check_in (staff_uid, team_uid) VALUES (?,?)";
        unique_ptr<sql::PreparedStatement> check_in(conn_->prepareStatement(query));
        check_in->setInt(1,staff_uid);
        check_in->setInt(2,team_uid);

        int rows_affected = check_in->executeUpdate();
        if (rows_affected == 0) {
            out_err_msg = u8"�ش� ��û�� ó���� �� �����ϴ�.";
            return false;
        }
        //[2] checkin_uid ��ȸ
        int checkin_uid = -1;
        unique_ptr<sql::PreparedStatement> get_id_stmt(
            conn_->prepareStatement("SELECT LAST_INSERT_ID()")
        );
        std::unique_ptr<sql::ResultSet> res(get_id_stmt->executeQuery());
        if (res->next()) {
            out_data["check_in_uid"] = res->getInt(1);
            return true;
        }
        else {
            out_err_msg = u8"check_in_uid ��ȸ ����";
            return false;
        }

        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string("SQL ���� �߻�: ") + e.what();
        return false;
    }
}
//============ [��� ��û - ����] ============
bool DBManager::ask_check_out(int check_in_uid, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB ����] DB ���� ����";
        return false;
    }
    try {
        string query = "UPDATE check_in SET check_type = 'check_out', check_out_time = CURRENT_TIMESTAMP WHERE check_in_uid = ?";
        unique_ptr<sql::PreparedStatement> check_out(conn_->prepareStatement(query));
        check_out->setInt(1, check_in_uid);

        int rows_affected = check_out->executeUpdate();
        if (rows_affected == 0) {
            out_err_msg = "�ش� ��� ������ �������� �ʽ��ϴ�.";
            return false;
        }
        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string("SQL ���� �߻�: ") + e.what();
        return false;
    }
}
//============ [�������� ��û - ����] ============
void DBManager::get_today_attendance(int staff_uid, int team_uid, json& out_data, string& out_err_msg) {
    json attendance = {
        {"status", nullptr},
        {"check_in_time", nullptr},
        {"check_out_time", nullptr}
    };

    if (!conn_) {
        out_err_msg = u8"[DB ����] DB ���� ����";
        out_data["attendance"] = attendance;
        return;
    }

    try {
        unique_ptr<sql::PreparedStatement> checkin(
            conn_->prepareStatement(R"(
        SELECT check_type, check_in_time, check_out_time
        FROM check_in
        WHERE staff_uid = ? AND team_uid = ?
          AND DATE(check_in_time) = CURDATE()
        ORDER BY check_in_time DESC
        LIMIT 1
    )")
        );
        checkin->setInt(1, staff_uid);
        checkin->setInt(2, team_uid);
        unique_ptr<sql::ResultSet> res(checkin->executeQuery());

        if (res && res->next()) {
            sql::SQLString sqlStatus = res->getString("check_type");
            sql::SQLString sqlInTime = res->getString("check_in_time");
            sql::SQLString sqlOutTime = res->isNull("check_out_time") ? "" : res->getString("check_out_time");

            std::string status = sqlStatus.c_str();
            std::string checkIn = sqlInTime.c_str();
            std::string checkOut = sqlOutTime.c_str();

            if (status == "check_in") {
                attendance["status"] = u8"���";
            }
            else if (status == "check_out") {
                attendance["status"] = u8"���";
            }
            else {
                attendance["status"] = nullptr;
            }

            attendance["check_in_time"] = checkIn;
            attendance["check_out_time"] = nlohmann::json(checkOut.empty() ? nullptr : checkOut);
        }
        else {
            std::cout << u8"[DEBUG] ��� ������ ����" << std::endl;
        }
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string(u8"SQL ���� �߻�: ") + e.what();
    }

    // �������� �� �ֱ�
    out_data["attendance"] = attendance;
}
//============ [�ٹ� ���� ���� ��û - ����] ============
void DBManager::get_request_status_count(int staff_uid, json& out_data, string& out_err_msg) {
    json status_count = {
        {"approved", 0},
        {"pending", 0},
        {"rejected", 0}
    };

    if (!conn_) {
        out_err_msg = u8"[DB ����] DB ���� ����";
        out_data["work_request_status"] = status_count;
        return;
    }

    try {
        string query =
            "SELECT status, COUNT(*) as cnt "
            "FROM duty_request "
            "WHERE staff_uid = ? AND request_date >= CURRENT_DATE AND is_deleted = 0 "
            "GROUP BY status";

        unique_ptr<sql::PreparedStatement> stmt(conn_->prepareStatement(query));
        stmt->setInt(1, staff_uid);
        unique_ptr<sql::ResultSet> res(stmt->executeQuery());

        while (res->next()) {
            string status = string(res->getString("status").c_str());
            int count = res->getInt("cnt");

            if (status_count.contains(status)) {
                status_count[status] = count;
            }
        }
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string(u8"SQL ���� �߻�: ") + e.what();
    }

    out_data["work_request_status"] = status_count;
}

//============ [** ������ ctx ä���] ============
bool DBManager::get_admin_context_by_uid(int admin_uid, AdminContext& out_ctx, std::string& out_err_msg) {
    if (!conn_) {
        out_err_msg = "[DB ����] DB ���� ����";
        return false;
    }

    try {
        // [1] ������ ���� ��ȸ (team_uid, team_name)
        std::unique_ptr<sql::PreparedStatement> stmt1(
            conn_->prepareStatement("SELECT team_uid, team_name FROM admin INNER JOIN team USING (team_uid) WHERE admin_uid = ?")
        );
        stmt1->setInt(1, admin_uid);
        std::unique_ptr<sql::ResultSet> res1(stmt1->executeQuery());

        if (!res1->next()) {
            out_err_msg = "�ش� admin_uid�� ã�� �� �����ϴ�.";
            return false;
        }

        out_ctx.admin_uid = admin_uid;
        out_ctx.team_uid = res1->getInt("team_uid");
        out_ctx.team_name = res1->getString("team_name").c_str();

        // [2] shift_code ���̺� ��ȸ�Ͽ� ShiftSetting ä���
        std::unique_ptr<sql::PreparedStatement> stmt2(
            conn_->prepareStatement("SELECT shift_type, shift_start, shift_end FROM shift_code ORDER BY seq ASC")
        );
        std::unique_ptr<sql::ResultSet> res2(stmt2->executeQuery());

        out_ctx.shift_setting.shifts.clear();
        out_ctx.shift_setting.shift_hours.clear();

        while (res2->next()) {
            std::string type = res2->getString("shift_type").c_str(); // ex: "Day", "Night", "Off"
            out_ctx.shift_setting.shifts.push_back(type);

            int hours = 0;
            if (!res2->isNull("shift_start") && !res2->isNull("shift_end")) {
                std::string start = res2->getString("shift_start").c_str();
                std::string end = res2->getString("shift_end").c_str();
                int h_start = std::stoi(start.substr(0, 2));
                int h_end = std::stoi(end.substr(0, 2));
                hours = (h_end - h_start + 24) % 24;
            }

            out_ctx.shift_setting.shift_hours[type] = hours;
        }

        // [3] night_shifts / off_shifts �ϵ��ڵ� �Ǵ� ���� DBȭ ����
        out_ctx.shift_setting.night_shifts = { "Night" };
        out_ctx.shift_setting.off_shifts = { "Off" };

        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = std::string("[DB ����] ") + e.what();
        return false;
    }
}

//============ [�ٹ�ǥ DB ����] ============
bool DBManager::insert_schedule(const string& date, int staff_uid, const string& shift_type, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB ����] DB ���� ����";
        return false;
    }
    try {
        std::unique_ptr<sql::PreparedStatement> stmt(
            conn_->prepareStatement(R"(
                INSERT INTO duty_schedule (staff_uid, duty_date, shift_type)
                VALUES (?, ?, ?)
                ON DUPLICATE KEY UPDATE shift_type = VALUES(shift_type)
            )")
        );

        stmt->setInt(1, staff_uid);
        stmt->setString(2, date);          // "YYYY-MM-DD"
        stmt->setString(3, shift_type);    // "Day", "Night", "Off" ��

        stmt->executeUpdate();
        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = std::string("[DB ����] ") + e.what();
        return false;
    }
}

//============ [** �ٹ��� ���� ��������] ============
bool DBManager::get_staff_list_by_team(int team_uid, vector<StaffInfo>& out_staffs, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = "[DB ����] DB ���� ����";
        return false;
    }

    try {
        std::unique_ptr<sql::PreparedStatement> stmt(
            conn_->prepareStatement(R"(
                SELECT staff_uid, name, grade, monthly_workhour
                FROM staff
                WHERE team_uid = ?
                ORDER BY grade ASC, name ASC
            )")
        );
        stmt->setInt(1, team_uid);
        std::unique_ptr<sql::ResultSet> res(stmt->executeQuery());

        out_staffs.clear();
        while (res->next()) {
            StaffInfo s;
            s.staff_uid = res->getInt("staff_uid");
            s.name = res->getString("name").c_str();
            s.grade = res->getInt("grade");
            s.monthly_workhour = res->getInt("monthly_workhour");
            out_staffs.push_back(s);
        }

        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = std::string("[DB ����] ") + e.what();
        return false;
    }
}

//============ [** �μ��ΰ� ����ü ���� ��������] ============
//team_uid ��� ��ȸ
bool DBManager::get_handover_notes_by_team(int team_uid, vector<HandoverNoteInfo>& out_notes, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = "[DB ����] DB ���� ����";
        return false;
    }

    try {
        std::unique_ptr<sql::PreparedStatement> stmt(
            conn_->prepareStatement(R"(
                SELECT 
                    h.handover_uid,
                    h.staff_uid,
                    h.team_uid,
                    h.handover_time,
                    h.shift_type,
                    h.note_type,
                    h.title,
                    h.text,
                    h.text_particular,
                    h.additional_info,
                    h.text_refine,
                    h.is_refined,
                    s.name AS staff_name
                FROM 
                    handover_note h
                JOIN 
                    staff s ON h.staff_uid = s.staff_uid
                WHERE 
                    h.team_uid = ?
                ORDER BY 
                    h.handover_time DESC
            )")
        );

        stmt->setInt(1, team_uid);
        std::unique_ptr<sql::ResultSet> res(stmt->executeQuery());

        out_notes.clear();

        while (res->next()) {
            HandoverNoteInfo note;

            note.handover_uid = res->getInt("handover_uid");
            note.staff_uid = res->getInt("staff_uid");
            note.team_uid = res->getInt("team_uid");
            note.handover_time = res->getString("handover_time").c_str();
            note.shift_type = res->getString("shift_type").c_str();
            note.note_type = res->getString("note_type").c_str();
            note.title = res->getString("title").c_str();
            note.text = res->getString("text").c_str();
            note.text_particular = res->getString("text_particular").c_str();
            note.additional_info = res->getString("additional_info").c_str();
            note.text_refine = res->getString("text_refine").c_str();
            note.is_refined = res->getInt("is_refined");
            note.staff_name = res->getString("staff_name").c_str();

            out_notes.push_back(note);
        }

        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = std::string("[DB ����] ") + e.what();
        return false;
    }
}
//note_uid ��� ��ȸ
bool DBManager::get_handover_notes_by_uid(int handover_uid, HandoverNoteInfo& out_note, std::string& out_err_msg) {
    if (!conn_) {
        out_err_msg = "[DB ����] DB ���� ����";
        return false;
    }

    try {
        std::unique_ptr<sql::PreparedStatement> stmt(
            conn_->prepareStatement(R"(
                SELECT 
                    h.handover_uid,
                    h.staff_uid,
                    s.name AS staff_name,
                    h.team_uid,
                    h.handover_time,
                    h.shift_type,
                    h.note_type,
                    h.title,
                    h.text,
                    h.text_particular,
                    h.additional_info,
                    h.text_refine,
                    h.is_refined
                FROM handover_note h
                LEFT JOIN staff s ON h.staff_uid = s.staff_uid
                WHERE h.handover_uid = ?
            )")
        );

        stmt->setInt(1, handover_uid);

        std::unique_ptr<sql::ResultSet> res(stmt->executeQuery());
        if (!res->next()) {
            out_err_msg = u8"�ش� �μ��ΰ� ������ ã�� �� �����ϴ�.";
            return false;
        }

        out_note.handover_uid = res->getInt("handover_uid");
        out_note.staff_uid = res->getInt("staff_uid");
        out_note.staff_name = res->getString("staff_name").c_str();
        out_note.team_uid = res->getInt("team_uid");
        out_note.handover_time = res->getString("handover_time").c_str();
        out_note.shift_type = res->getString("shift_type").c_str();
        out_note.note_type = res->getString("note_type").c_str();
        out_note.title = res->getString("title").c_str();
        out_note.text = res->getString("text").c_str();
        out_note.text_particular = res->getString("text_particular").c_str();
        out_note.additional_info = res->getString("additional_info").c_str();
        out_note.text_refine = res->getString("text_refine").c_str();
        out_note.is_refined = res->getInt("is_refined");

        return true;
    }
    catch (sql::SQLException& e) {
        out_err_msg = std::string(u8"[DB ����] ") + e.what();
        return false;
    }
}

//============ [** �ٹ����� ����ü ���� ��������] ============
vector<ScheduleEntry> DBManager::get_team_schedule(int team_uid, const std::string& target_month) {
    vector<ScheduleEntry> schedule_list;

    try {
        auto stmt = conn_->prepareStatement(R"(
            SELECT s.schedule_uid, s.staff_uid, s.duty_date, s.shift_type
            FROM schedule s
            JOIN staff st ON s.staff_uid = st.staff_uid
            WHERE st.team_uid = ? AND DATE_FORMAT(s.duty_date, '%Y-%m') = ?
            ORDER BY s.duty_date ASC
        )");
        stmt->setInt(1, team_uid);
        stmt->setString(2, target_month);

        auto res = stmt->executeQuery();
        while (res->next()) {
            ScheduleEntry entry;
            entry.schedule_uid = res->getInt("schedule_uid");
            entry.staff_uid = res->getInt("staff_uid");
            entry.duty_date = res->getString("duty_date");
            entry.shift_type = res->getString("shift_type");

            schedule_list.push_back(entry);
        }
    }
    catch (const sql::SQLException& e) {
        std::cerr << "[DB ����] ������ �ҷ����� ����: " << e.what() << std::endl;
    }
    return schedule_list;
}


vector<ScheduleEntry> DBManager::get_staff_schedule(int team_uid, const string& target_month) {
    vector<ScheduleEntry> schedule_list;

    try {
        auto stmt = conn_->prepareStatement(R"(
            SELECT schedule_uid, staff_uid, duty_date, shift_type, hours 
            FROM schedule
            WHERE staff_uid = ? AND DATE_FORMAT(duty_date, '%Y-%m') = ?
            ORDER BY duty_date ASC

        )");
        stmt->setInt(1, team_uid);
        stmt->setString(2, target_month);

        auto res = stmt->executeQuery();
        while (res->next()) {
            ScheduleEntry entry;
            entry.schedule_uid = res->getInt("schedule_uid");
            entry.staff_uid = res->getInt("staff_uid");
            entry.hours = res->getInt("hours");
            entry.duty_date = res->getString("duty_date");
            entry.shift_type = res->getString("shift_type");

            schedule_list.push_back(entry);
        }
    }
    catch (const sql::SQLException& e) {
        std::cerr << "[DB ����] ������ �ҷ����� ����: " << e.what() << std::endl;
    }
    return schedule_list;
}
