#include "DBManager.h"
#include "DateUtil.h"
#include <iostream>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <windows.h>

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

//============ [�α���] ============

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
        // [1] �α��� üũ
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

        int staff_uid = res->getInt("staff_uid");
        out_data["staff_uid"] = res->getInt("staff_uid");

        out_data["team_uid"] = res->getInt("team_uid");
        out_data["team_name"] = res->getString("team_name");

        // [2] ���º� ��û �� ī��Ʈ ���� (���� ����)
        string stat_query =
            "SELECT status, COUNT(*) as cnt "
            "FROM duty_request "
            "WHERE staff_uid = ? AND request_date >= CURRENT_DATE AND is_deleted = 0 "
            "GROUP BY status";

        auto stat_stmt = conn_->prepareStatement(stat_query);
        stat_stmt->setInt(1, staff_uid);
        auto stat_res = stat_stmt->executeQuery();
        json status_count = {
            {"approved", 0},
            {"pending", 0},
            {"rejected", 0}
        };
        while (stat_res->next()) {
            std::string status = stat_res->getString("status").c_str();
            int count = stat_res->getInt("cnt");

            if (status_count.contains(status)) {
                status_count[status] = count;
            }
        }
        out_data["work_request_status"] = status_count;
        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string(u8"SQL ���� �߻�: ") + e.what();
        return false;
    }
}

bool DBManager::login_admin(const string& admin_id, const string& admin_pw, json& out_data, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB ����] DB ���� ����";
        return false;
    }
    try {
        //[1] �α��� üũ
        std::unique_ptr<sql::PreparedStatement> checklogin(
            conn_->prepareStatement("SELECT admin_uid FROM admin WHERE admin_id = ? AND admin_pw = ?")
        );
        checklogin->setString(1, admin_id);
        checklogin->setString(2, admin_pw);
        std::unique_ptr<sql::ResultSet> res(checklogin->executeQuery());

        if (!res->next()) {
            out_err_msg = u8"���̵� �Ǵ� ��й�ȣ�� ��ġ���� �ʽ��ϴ�.";
            return false;
        }
        // [2] uid ��������
        out_data["admin_uid"] = res->getInt("admin_uid");
        return true;
    }
    catch (sql::SQLException& e) {
        out_err_msg = std::string(u8"SQL ���� �߻�: ") + e.what();
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
        std::string query =
            "SELECT duty_request_uid, request_date, desire_shift, status, reason, admin_msg "
            "FROM duty_request "
            "WHERE staff_uid = ? AND DATE_FORMAT(request_date, '%Y-%m') = ? "
            "ORDER BY request_date ASC";

        std::unique_ptr<sql::PreparedStatement> get_shift_detail(conn_->prepareStatement(query));

        get_shift_detail->setInt(1, staff_uid);
        get_shift_detail->setString(2, year_month);

        std::unique_ptr<sql::ResultSet> res(get_shift_detail->executeQuery());
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
        out_err_msg = std::string(u8"SQL ���� �߻�: ") + e.what();
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
            std::unique_ptr<sql::PreparedStatement> pstmt(
                conn_->prepareStatement("SELECT team_uid FROM staff WHERE staff_uid = ?")
            );
            pstmt->setInt(1, staff_uid);
            std::unique_ptr<sql::ResultSet> res(pstmt->executeQuery());

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
        std::unique_ptr<sql::PreparedStatement> insert_stmt(
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
        out_err_msg = std::string(u8"SQL ���� �߻�: ") + e.what();
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
        std::unique_ptr<sql::PreparedStatement> cancel_duty(conn_->prepareStatement(query));
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