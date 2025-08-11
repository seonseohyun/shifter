#include "DBManager.h"
#include "DateUtil.h"
#include <iostream>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <random>
#include <string>
#include <algorithm>
#include <windows.h>

/*SELECT JSON_OBJECT('PROTOCOL','1','CLIENT_NUM',u.id,'IOT_INFO',JSON_ARRAYAGG(JSON_OBJECT('LOCATION_CODE',d.location_code,'DEVICE_TYPE_CODE',d.device_type,'POWER',d.power,'TEMP',d.temp))) FROM device d JOIN user u ON d.user_id = u.id WHERE u.addr_id = '{ADDR_ID}';*/
using namespace std;
using json = json;

DBManager::DBManager() {}
DBManager::~DBManager() {}

inline string to_std(const sql::SQLString& s) {
    return string(s.c_str(), s.length());  // 즉시 복사 (dangling 방지)
}

static string gen_temp_id(int team_uid, int rand_len = 4) {
    static const char alnum[] =
        "0123456789abcdefghijklmnopqrstuvwxyz";
    random_device rd; mt19937 gen(rd());
    uniform_int_distribution<int> dist(0, (int)sizeof(alnum) - 2);

    string r; r.reserve(rand_len);
    for (int i = 0; i < rand_len; ++i) r.push_back(alnum[dist(gen)]);
    return "T" + to_string(team_uid) + "-" + r;  
}

static string gen_temp_pw(int len = 5) {
    static const char chars[] =
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*?";
    random_device rd; mt19937 gen(rd());
    uniform_int_distribution<int> dist(0, (int)sizeof(chars) - 2);

    string pw; pw.reserve(len);
    for (int i = 0; i < len; ++i) pw.push_back(chars[dist(gen)]);
    return pw;  
}

//============ [DB 연결] ============
bool DBManager::connect() {
    try {
        sql::Driver* driver = sql::mariadb::get_driver_instance();
        sql::SQLString url("jdbc:mariadb://127.0.0.1:3306/shifter");

        sql::Properties properties;
        properties["user"] = "seonseo";
        properties["password"] = "1234";

        properties["useSsl"] = "true";
        properties["sslMode"] = "VERIFY_CA";
        properties["serverSslCert"] = "certs/ca.pem";  // 경로만 맞으면 OK

        conn_.reset(driver->connect(url, properties));
        unique_ptr<sql::Statement> s(conn_->createStatement());
        s->execute("SET NAMES utf8mb4 COLLATE utf8mb4_general_ci");
        s->execute("SET character_set_results = utf8mb4");
        s->execute("SET character_set_client   = utf8mb4");
        s->execute("SET character_set_connection = utf8mb4");
        return true;

    }
    catch (sql::SQLException& e) {
        cerr << u8" {{(>_<)}} DB 연결 실패: " << e.what() << endl;
        return false;
    }
}

//============ [로그인] ============
// meta 기반 로그인: id/pw 검증 후, 팀 메타를 로드해서 out_data 채움
bool DBManager::login(const string& id, const string& pw,
    nlohmann::json& out_data, string& out_err_msg)
{
    if (!conn_) { out_err_msg = u8"[DB 오류] DB 연결 실패"; return false; }
    if (id.empty() || pw.empty()) {
        out_err_msg = u8"[입력 오류] 아이디 또는 비밀번호가 비어 있습니다.";
        return false;
    }

    try {
        // 1) 자격 확인: 최소키만 가져옴 (이름/회사명은 meta에서)
        unique_ptr<sql::PreparedStatement> ps(conn_->prepareStatement(
            "SELECT s.staff_uid, s.team_uid "
            "FROM staff s "
            "WHERE s.id = ? AND s.pw = ? "
            "LIMIT 1"
        ));
        ps->setString(1, id);
        ps->setString(2, pw);
        unique_ptr<sql::ResultSet> rs(ps->executeQuery());
        if (!rs->next()) {
            out_err_msg = u8"아이디 또는 비밀번호가 일치하지 않습니다.";
            return false;
        }

        const int staff_uid = rs->getInt("staff_uid");
        const int team_uid = rs->getInt("team_uid");

        // 2) 팀 메타 로드
        vector<StaffInfo> meta;
        if (!get_staff_list_by_team(team_uid, meta, out_err_msg)) {
            return false; // 메타 로드 실패
        }

        // 3) 메타에서 내 행 찾기
        const StaffInfo* me = nullptr;
        for (const auto& m : meta) {
            if (m.staff_uid == staff_uid) { me = &m; break; }
        }
        if (!me) {
            out_err_msg = u8"대상 사용자를 메타에서 찾지 못했습니다.";
            return false;
        }

        // 4) 응답 채우기 (API 계약 키에 맞춰 매핑)
        out_data["date"] = DateUtil::get_today();
        out_data["staff_uid"] = staff_uid;
        out_data["team_uid"] = team_uid;
        out_data["team_name"] = me->team_name;   
        out_data["staff_name"] = me->name;
        out_data["grade_level"] = me->grade_level;
        out_data["grade_name"] = me->grade_name;
        out_data["is_tmp_id"] = me->is_tmp_id;      // (있으면 같이 내려도 유용)

        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string(u8"SQL 예외 발생: ") + e.what();
        return false;
    }
}

bool DBManager::login_admin(const string& admin_id, const string& admin_pw, json& out_data, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
        return false;
    }
    try {
        // [1] 로그인 체크
        unique_ptr<sql::PreparedStatement> checklogin(
            conn_->prepareStatement("SELECT admin_uid, team_uid FROM admin WHERE admin_id = ? AND admin_pw = ?")
        );
        checklogin->setString(1, admin_id);
        checklogin->setString(2, admin_pw);

        unique_ptr<sql::ResultSet> res(checklogin->executeQuery());

        if (!res->next()) {
            out_err_msg = u8"아이디 또는 비밀번호가 일치하지 않습니다.";
            return false;
        }

        // [2] admin_uid, team_uid 저장
        out_data["admin_uid"] = res->getInt("admin_uid");
        int team_uid = res->isNull("team_uid") ? -1 : res->getInt("team_uid");
        out_data["team_uid"] = team_uid;

        // [3] team_name 조회 (team_uid가 있는 경우만)
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
                out_data["team_name"] = ""; // 팀 없음
            }
        }
        else {
            out_data["team_name"] = ""; // 팀 없음
        }

        return true;
    }
    catch (sql::SQLException& e) {
        out_err_msg = string(u8"SQL 예외 발생: ") + e.what();
        return false;
    }
}

bool DBManager::get_staff_info_by_uid(int staff_uid, StaffInfo& out_staff, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = "[DB 오류] DB 연결 실패";
        return false;
    }

    try {
        unique_ptr<sql::PreparedStatement> stmt(
            conn_->prepareStatement(R"SQL(
                SELECT 
                  s.staff_uid,
                  s.name,
                  s.grade_level,
                  COALESCE(g.grade_name, '')   AS grade_name,
                  COALESCE(s.monthly_workhour,0) AS monthly_workhour
                FROM staff s
                LEFT JOIN grade g
                  ON g.team_uid = s.team_uid
                 AND g.grade    = s.grade_level
                WHERE s.staff_uid = ?
                LIMIT 1
            )SQL"));

        stmt->setInt(1, staff_uid);

        unique_ptr<sql::ResultSet> res(stmt->executeQuery());

        if (res->next()) {
            out_staff.staff_uid = res->getInt("staff_uid");
            out_staff.name = res->getString("staff_name").c_str();
            out_staff.grade_level = res->getInt("grade");
            out_staff.monthly_workhour = res->getInt("monthly_workhour");
            return true;
        }
        else {
            out_err_msg = "[DB 오류] 해당 직원번호를 찾을 수 없습니다.";
            return false;
        }
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string("[DB 오류] ") + e.what();
        return false;
    }
}

//============ [정보등록] ============
bool DBManager::register_team_info(const string& company_name_in,const string& team_name_in,const string& job_category_in,
                                  const json& shift_info,json& out_json,string& out_err)
{
    out_json = json::object();
    if (!conn_) { out_err = u8"[DB 오류] DB 연결 실패"; return false; }

    auto norm_job = [](string s) {
        if (s == u8"간호사") return string(u8"간호");
        if (s == u8"소방관") return string(u8"소방");
        if (s == u8"경찰관") return string(u8"경찰");
        // 나머지는 그대로, 단 ENUM 미스매치시 '기타'로 폴백
        if (s != u8"소방" && s != u8"간호" && s != u8"경찰" && s != u8"기타") return string(u8"기타");
        return s;
        };

    const string company_name = company_name_in;
    const string team_name = team_name_in;
    const string job_category = norm_job(job_category_in);

    auto toHHMMSS = [](const string& hhmm) {
        return (hhmm.size() == 5) ? (hhmm + ":00") : hhmm; // "08:00" -> "08:00:00"
        };

    try {
        conn_->setAutoCommit(false);

        int team_uid = -1;
        {
            unique_ptr<sql::PreparedStatement> sel(
                conn_->prepareStatement(
                    "SELECT team_uid FROM team WHERE company_name=? AND team_name=? FOR UPDATE"
                )
            );
            sel->setString(1, company_name);
            sel->setString(2, team_name);
            unique_ptr<sql::ResultSet> rs(sel->executeQuery());
            if (rs->next()) {
                team_uid = rs->getInt("team_uid");
                // 필요 시 job_category 업데이트
                unique_ptr<sql::PreparedStatement> up(
                    conn_->prepareStatement(
                        "UPDATE team SET job_category=? WHERE team_uid=?"
                    )
                );
                up->setString(1, job_category);
                up->setInt(2, team_uid);
                up->executeUpdate();
            }
        }

        // [1] 없으면 MAX(team_uid)+1로 새로 채번해서 INSERT (COUNT+1 대신 MAX+1 권장)
        if (team_uid < 0) {
            int new_id = 0;
            {
                unique_ptr<sql::Statement> st(conn_->createStatement());
                // 삭제된 행이 있으면 COUNT+1은 중복 위험 → MAX+1을 FOR UPDATE로 잠금
                unique_ptr<sql::ResultSet> rs(
                    st->executeQuery("SELECT COALESCE(MAX(team_uid),0)+1 AS nid FROM team FOR UPDATE")
                );
                rs->next();
                new_id = rs->getInt("nid");
            }
            unique_ptr<sql::PreparedStatement> insTeam(
                conn_->prepareStatement(
                    "INSERT INTO team (team_uid, company_name, team_name, job_category) "
                    "VALUES (?, ?, ?, ?)"
                )
            );
            insTeam->setInt(1, new_id);
            insTeam->setString(2, company_name);
            insTeam->setString(3, team_name);
            insTeam->setString(4, job_category);
            insTeam->executeUpdate();
            team_uid = new_id;
        }

        // [2] 기존 교대코드 삭제(같은 팀/직무)
        {
            unique_ptr<sql::PreparedStatement> del(
                conn_->prepareStatement(
                    "DELETE FROM shift_code WHERE team_uid=? AND job_category=?"
                )
            );
            del->setInt(1, team_uid);
            del->setString(2, job_category);
            del->executeUpdate();
        }

        // [3] 새 교대코드 INSERT (클라 duty_hours 그대로 저장)
        unique_ptr<sql::PreparedStatement> insShift(
            conn_->prepareStatement(
                "INSERT INTO shift_code "
                "(team_uid, job_category, shift_type, shift_start, shift_end, duty_hours) "
                "VALUES (?, ?, ?, ?, ?, ?)"
            )
        );

        int saved = 0;
        for (const auto& row : shift_info) {
            if (!row.is_object()) continue;

            string duty_type = row.value("duty_type", "");
            string start_time = row.value("start_time", "");
            string end_time = row.value("end_time", "");
            int    duty_hours = row.value("duty_hours", 0);

            // 타입 대문자 정규화
            for (auto& c : duty_type) c = toupper(static_cast<unsigned char>(c));

            insShift->setInt(1, team_uid);
            insShift->setString(2, job_category);
            insShift->setString(3, duty_type);

            if (duty_type == "O") {
                insShift->setNull(4, 0);
                insShift->setNull(5, 0);
                insShift->setInt(6, 0);
            }
            else {
                insShift->setString(4, toHHMMSS(start_time));
                insShift->setString(5, toHHMMSS(end_time));
                insShift->setInt(6, duty_hours);     
            }

            saved += insShift->executeUpdate();
        }

        conn_->commit();
        conn_->setAutoCommit(true);

        out_json = {
            {"data", {
                {"team_uid",     team_uid},
                {"company_name", company_name},
                {"team_name",    team_name},
                {"job_category", job_category},
                {"shift_info",   shift_info}
            }}
        };
        return true;
    }
    catch (const sql::SQLException& e) {
        try { conn_->rollback(); conn_->setAutoCommit(true); }
        catch (...) {}
        out_err = string(u8"[SQL 예외] ") + e.what();
        return false;
    }
    catch (...) {
        try { conn_->rollback(); conn_->setAutoCommit(true); }
        catch (...) {}
        out_err = u8"[예외] 알 수 없는 오류";
        return false;
    }
}

bool DBManager::register_grade_info(int team_uid, const vector<GradeInfo>& grades, string& out_err) {
    if (!conn_) { out_err = u8"[DB 오류] DB 연결 실패"; return false; }
    try {
        conn_->setAutoCommit(false);

        unique_ptr<sql::PreparedStatement> ins(
            conn_->prepareStatement(
                "INSERT INTO team_grade (team_uid, grade_level, grade_name) "
                "VALUES (?,?,?)"
            )
        );

        for (const auto& g : grades) {
            if (g.grade_level <= 0 || g.grade_name.empty()) continue; 
            ins->setInt(1, team_uid);
            ins->setInt(2, g.grade_level);
            ins->setString(3, g.grade_name);
            ins->executeUpdate();  
        }

        conn_->commit();
        conn_->setAutoCommit(true);
        return true;
    }
    catch (const sql::SQLException& e) {
        try { conn_->rollback(); }
        catch (...) {}
        conn_->setAutoCommit(true);
        out_err = string(u8"[SQL 예외] ") + e.what();
        return false;
    }
}

bool DBManager::register_staff_info(
    int team_uid, int grade_level,
    const string& name, const string& phone,
    int monthly_workhour,
    string& out_id, string& out_pw,
    string& out_err)
{
    if (!conn_) { out_err = u8"DB 연결 없음"; return false; }

    try {
        // 1) 임시 ID 생성(충돌시 재시도)
        string tmp_id = gen_temp_id(team_uid);

        // 2) 임시 PW 생성
        string tmp_pw = gen_temp_pw(5);

        // 3) INSERT
        unique_ptr<sql::PreparedStatement> ins(
            conn_->prepareStatement(
                "INSERT INTO staff "
                "(team_uid, id, pw, grade_level, name, phone, monthly_workhour) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)"
            )
        );
        ins->setInt(1, team_uid);
        ins->setString(2, tmp_id);
        ins->setString(3, tmp_pw);
        ins->setInt(4, grade_level);
        ins->setString(5, name);
        ins->setString(6, phone);
        ins->setInt(7, monthly_workhour);
        ins->executeUpdate();
        return true;
    }
    catch (const sql::SQLException& e) {
        out_err = string(u8"[DB 오류] ") + e.what();
        return false;
    }
}

//============ [근무 변경 디테일 조회 - 유저] ============
bool DBManager::shift_change_detail (int staff_uid, const string& year_month, json& out_data, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"→ [DB 오류] DB 연결 실패";
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
        out_err_msg = string(u8"SQL 예외 발생: ") + e.what();
        return false;
    }
}
//============ [근무 변경 요청 등록 - 유저] ============
bool DBManager::ask_shift_change(int staff_uid, const string& yyyymmdd, const string& duty_type, const string& reason, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
        return false;
    }

    try {
        // [1] staff_uid로 team_uid 조회"
        int team_uid = -1;
        {
            unique_ptr<sql::PreparedStatement> pstmt(
                conn_->prepareStatement("SELECT team_uid FROM staff WHERE staff_uid = ?")
            );
            pstmt->setInt(1, staff_uid);
            unique_ptr<sql::ResultSet> res(pstmt->executeQuery());

            if (!res->next()) {
                out_err_msg = u8"[오류] staff_uid가 존재하지 않습니다.";
                return false;
            }
            team_uid = res->getInt("team_uid");
        }

        // [2] 날짜 형식 확인 (예: "2025-08-05")
        if (yyyymmdd.size() != 10 || yyyymmdd[4] != '-' || yyyymmdd[7] != '-') {
            out_err_msg = u8"날짜 형식 오류 (예: 2025-08-05로 송신바랍니다.)";
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
        out_err_msg = string(u8"SQL 예외 발생: ") + e.what();
        return false;
    }
}
//============ [근무 변경 요청 삭제 - 유저] ============
bool DBManager::cancel_shift_change(int& duty_request_uid, json& out_data, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
        return false;
    }
    try {
        string query = "UPDATE duty_request SET is_deleted = 1 WHERE duty_request_uid = ?";
        unique_ptr<sql::PreparedStatement> cancel_duty(conn_->prepareStatement(query));
        cancel_duty->setInt(1, duty_request_uid);

        int rows_affected = cancel_duty->executeUpdate();
        if (rows_affected == 0) {
            out_err_msg = "해당 요청이 존재하지 않습니다.";
            return false;
        }
        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string("SQL 예외 발생: ") + e.what();
        return false;
    }
}


//============ [출근 요청 - 유저] ============
bool DBManager::ask_check_in(int staff_uid, int team_uid, json& out_data, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
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
            out_err_msg = u8"해당 요청을 처리할 수 없습니다.";
            return false;
        }
        //[2] checkin_uid 조회
        int checkin_uid = -1;
        unique_ptr<sql::PreparedStatement> get_id_stmt(
            conn_->prepareStatement("SELECT LAST_INSERT_ID()")
        );
        unique_ptr<sql::ResultSet> res(get_id_stmt->executeQuery());
        if (res->next()) {
            out_data["check_in_uid"] = res->getInt(1);
            return true;
        }
        else {
            out_err_msg = u8"check_in_uid 조회 실패";
            return false;
        }

        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string("SQL 예외 발생: ") + e.what();
        return false;
    }
}
//============ [퇴근 요청 - 유저] ============
bool DBManager::ask_check_out(int check_in_uid, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
        return false;
    }
    try {
        string query = "UPDATE check_in SET check_type = 'check_out', check_out_time = CURRENT_TIMESTAMP WHERE check_in_uid = ?";
        unique_ptr<sql::PreparedStatement> check_out(conn_->prepareStatement(query));
        check_out->setInt(1, check_in_uid);

        int rows_affected = check_out->executeUpdate();
        if (rows_affected == 0) {
            out_err_msg = "해당 출근 정보가 존재하지 않습니다.";
            return false;
        }
        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string("SQL 예외 발생: ") + e.what();
        return false;
    }
}
//============ [근태정보 요청 - 유저] ============
bool DBManager::get_today_attendance(int staff_uid, int team_uid,json& out_data, string& out_err_msg){
    out_data["attendance"] = {
        {"status", nullptr},
        {"check_in_time", nullptr},
        {"check_out_time", nullptr}
    };

    if (!conn_) { out_err_msg = u8"[DB 오류] DB 연결 실패"; return false; }

    try {
        static constexpr char SQL[] = R"SQL(
            SELECT
              check_type,
              DATE_FORMAT(check_in_time , '%Y-%m-%d %H:%i:%s') AS cin,
              DATE_FORMAT(check_out_time, '%Y-%m-%d %H:%i:%s') AS cout
            FROM check_in
            WHERE staff_uid=? AND team_uid=?
              AND DATE(COALESCE(check_in_time, check_out_time)) = CURDATE()
            ORDER BY COALESCE(check_out_time, check_in_time) DESC
            LIMIT 1
            )SQL";

        unique_ptr<sql::PreparedStatement> stmt(conn_->prepareStatement(SQL));
        stmt->setInt(1, staff_uid);
        stmt->setInt(2, team_uid);

        unique_ptr<sql::ResultSet> rs(stmt->executeQuery());
        if (!rs || !rs->next()) {
            out_err_msg = u8"해당 일자 근태 기록이 없습니다.";
            return false;
        }

        // SQLString → string (명시 변환)
        auto to_std = [](const sql::SQLString& s) {
            return string(s.c_str(), s.length());
            };

        string check_type, check_in, check_out;
        if (!rs->isNull("check_type")) check_type = to_std(rs->getString("check_type"));
        if (!rs->isNull("cin"))        check_in = to_std(rs->getString("cin"));
        if (!rs->isNull("cout"))       check_out = to_std(rs->getString("cout"));

        if (check_in.empty() && check_out.empty()) {
            out_err_msg = u8"해당 일자 근태 기록이 없습니다.";
            return false;
        }

        out_data["attendance"]["status"] = check_out.empty() ? u8"출근" : u8"퇴근";

        if (check_in.empty())
            out_data["attendance"]["check_in_time"] = nullptr;
        else
            out_data["attendance"]["check_in_time"] = check_in;

        if (check_out.empty())
            out_data["attendance"]["check_out_time"] = nullptr;
        else
            out_data["attendance"]["check_out_time"] = check_out;

        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string(u8"[SQL 예외] ") + e.what();
        return false;
    }
}
//============ [근태정보 날짜별 요청 - 유저] ============
bool DBManager::get_attendance_info(int staff_uid,const string& ymd, string& check_in,string& check_out,string& err)
{
    check_in.clear(); check_out.clear();
    if (!conn_) { err = "[DB 오류] DB 연결 실패"; return false; }

    try {
        static constexpr char SQL[] = R"SQL(
            SELECT
              DATE_FORMAT(check_in_time , '%Y-%m-%d %H:%i:%s') AS cin,
              DATE_FORMAT(check_out_time, '%Y-%m-%d %H:%i:%s') AS cout
            FROM check_in
            WHERE staff_uid = ?
              AND check_in_time >= DATE(?)
              AND check_in_time <  DATE_ADD(DATE(?), INTERVAL 1 DAY)
            ORDER BY check_in_time DESC
            LIMIT 1;
            )SQL";
        auto ps = unique_ptr<sql::PreparedStatement>(conn_->prepareStatement(SQL));
        ps->setInt(1, staff_uid);
        ps->setString(2, ymd);
        ps->setString(3, ymd);

        auto rs = unique_ptr<sql::ResultSet>(ps->executeQuery());
        if (rs && rs->next()) {
            if (!rs->isNull("cin"))  check_in = to_std(rs->getString("cin"));
            if (!rs->isNull("cout")) check_out = to_std(rs->getString("cout"));
        }
        return true; // 기록 없어도 success (둘 다 빈 문자열일 수 있음)
    }
    catch (const sql::SQLException& e) {
        err = string("[SQL 예외] ") + e.what();
        return false;
    }
}

//============ [근무 변경 개수 요청 - 유저] ============
void DBManager::get_request_status_count(int staff_uid, json& out_data, string& out_err_msg) {
    json status_count = {
        {"approved", 0},
        {"pending", 0},
        {"rejected", 0}
    };

    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
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
        out_err_msg = string(u8"SQL 예외 발생: ") + e.what();
    }

    out_data["work_request_status"] = status_count;
}

//============ [** 관리자 ctx 채우기] ============
bool DBManager::get_admin_context_by_uid(int admin_uid, AdminContext& out_ctx, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
        return false;
    }

    try {
        // [1] 관리자 정보 조회 (team_uid, team_name)
        unique_ptr<sql::PreparedStatement> stmt1(
            conn_->prepareStatement("SELECT a.team_uid, t.team_name "
                "FROM admin a INNER JOIN team t USING (team_uid) "
                "WHERE a.admin_uid = ?")
        );
        stmt1->setInt(1, admin_uid);
        unique_ptr<sql::ResultSet> res1(stmt1->executeQuery());

        if (!res1->next()) {
            out_err_msg = u8"해당 admin_uid를 찾을 수 없습니다.";
            return false;
        }

        out_ctx.admin_uid = admin_uid;
        out_ctx.team_uid = res1->getInt("team_uid");
#if defined(HAVE_SQLSTRING_ASSTDSTRING)
        out_ctx.team_name = res1->getString("team_name").asStdString();
#else
        out_ctx.team_name =string(res1->getString("team_name").c_str());
#endif

        // [2] shift_code 테이블 조회하여 ShiftSetting 채우기
        unique_ptr<sql::PreparedStatement> stmt2(
            conn_->prepareStatement(
                "SELECT shift_type, shift_start, shift_end, job_category "
                "FROM shift_code "
                "WHERE team_uid = ? "
                "ORDER BY shift_code_uid")
        );
        stmt2->setInt(1, out_ctx.team_uid);
        unique_ptr<sql::ResultSet> res2(stmt2->executeQuery());

        out_ctx.shift_setting.shifts.clear();
        out_ctx.shift_setting.shift_hours.clear();
        out_ctx.shift_setting.night_shifts.clear();
        out_ctx.shift_setting.off_shifts.clear();


        while (res2->next()) {
#if defined(HAVE_SQLSTRING_ASSTDSTRING)
           string type = res2->getString("shift_type").asStdString();
           string start = res2->isNull("shift_start") ? "" : res2->getString("shift_start").asStdString();
           string end = res2->isNull("shift_end") ? "" : res2->getString("shift_end").asStdString();
#else
           string type =string(res2->getString("shift_type").c_str());
           string start = res2->isNull("shift_start") ? "" :string(res2->getString("shift_start").c_str());
           string end = res2->isNull("shift_end") ? "" :string(res2->getString("shift_end").c_str());
           string job_category = string(res1->getString("job_category").c_str());
#endif
            out_ctx.shift_setting.shifts.push_back(type);

            int hours = 0;
            if (!start.empty() && !end.empty() && start.size() >= 2 && end.size() >= 2) {
                int h_start =stoi(start.substr(0, 2));
                int h_end =stoi(end.substr(0, 2));
                hours = (h_end - h_start + 24) % 24;
            }
            out_ctx.shift_setting.shift_hours[type] = hours;
        }

        out_ctx.shift_setting.night_shifts = { "Night" };
        out_ctx.shift_setting.off_shifts = { "Off" };

        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string("[DB 오류] ") + e.what();
        return false;
    }
}

//============ [근무표 DB 삽입] ============
bool DBManager::insert_schedule(const string& date, int staff_uid, const string& shift_type, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
        return false;
    }
    try {
        unique_ptr<sql::PreparedStatement> stmt(
            conn_->prepareStatement(R"(
                INSERT INTO schedule (staff_uid, duty_date, shift_type)
                VALUES (?, ?, ?)
                ON DUPLICATE KEY UPDATE shift_type = VALUES(shift_type)
            )")
        );

        stmt->setInt(1, staff_uid);
        stmt->setString(2, date);          // "YYYY-MM-DD"
        stmt->setString(3, shift_type);    // "Day", "Night", "Off" 등

        stmt->executeUpdate();
        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string("[DB 오류] ") + e.what();
        return false;
    }
}

//============ [근무자 정보 가져오기] ============
//팀 uid 기준으로 전체 팀원을 메타 구조체에 채우삼
bool DBManager::get_staff_list_by_team(int team_uid, vector<StaffInfo>& out_staffs, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
        return false;
    }

    try {
        unique_ptr<sql::PreparedStatement> stmt(conn_->prepareStatement(R"SQL(
            SELECT
              s.staff_uid,
              s.team_uid,
              s.name,
              s.id,
              s.pw,
              s.phone,
              s.is_tmp_id,
              s.grade_level,                          
              COALESCE(g.grade_name, '')      AS grade_name,          
              COALESCE(s.monthly_workhour, 0) AS monthly_workhour,
              COALESCE(t.company_name, '')    AS company_name,
              COALESCE(t.team_name, '')       AS team_name,
              COALESCE(t.job_category, '')    AS job_category
            FROM staff s
            JOIN team  t
              ON t.team_uid = s.team_uid
            LEFT JOIN grade g
              ON g.team_uid = s.team_uid
             AND g.grade    = s.grade_level
            WHERE s.team_uid = ?
            ORDER BY s.name ASC; )SQL"));

        stmt->setInt(1, team_uid);
        unique_ptr<sql::ResultSet> res(stmt->executeQuery());

        out_staffs.clear();
        while (res->next()) {
            StaffInfo info;
            info.staff_uid   = res->getInt("staff_uid");
            info.team_uid    = res->getInt("team_uid");
            info.name        = res->getString("name").c_str();
            info.id          = res->getString("id").c_str();
            info.pw          = res->getString("pw").c_str();
            info.phone       = res->getString("phone").c_str();
            info.is_tmp_id   = res->getInt("is_tmp_id");
            info.grade_level = res->getInt("grade_level");
            info.grade_name  = res->getString("grade_name").c_str();
            info.monthly_workhour = res->getInt("monthly_workhour");
            info.company_name = res->getString("company_name").c_str();
			info.team_name = res->getString("team_name").c_str();
			info.job_category = res->getString("job_category").c_str();
            out_staffs.push_back(move(info));
        }
        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string(u8"[DB 오류] ") + e.what();
        return false;
    }
}
//임시 아이디인 직원만 메타 구조체에서 복사, 반환하기
bool DBManager::build_tmp_staff_from_meta(const vector<StaffInfo>& meta, vector<StaffInfo>& out_list, int tmp_flag){
    out_list.clear();
    out_list.reserve(meta.size());

    for (const auto& m : meta) {
        if (m.is_tmp_id != tmp_flag) continue;      // tmp만!

        StaffInfo info;                            
        // 필요 필드만 복사 (요구 스펙)
        info.grade_level = m.grade_level;
        info.grade_name = m.grade_name;
        info.phone = m.phone;                 // phone_num
        info.id = m.id;                    // temp_id
        info.pw = m.pw;                    // temp_pw 
        info.monthly_workhour = m.monthly_workhour;
        out_list.push_back(move(info));
    }
    return true;
}
// [최종~]팀 uid를 기준으로 메타 로드 하고 임시 아이디인 녀석만 반환하는 녀석
bool DBManager::get_tmp_staff_list_by_team_from_meta( int team_uid, vector<StaffInfo>& out_list, string& out_err_msg, int tmp_flag){
    vector<StaffInfo> meta;
    if (!get_staff_list_by_team(team_uid, meta, out_err_msg))  //전체 팀원 로드
        return false;

    return build_tmp_staff_from_meta(meta, out_list, tmp_flag =1); //임시 직원만 로드
}
// 직원 uid가 일치하는 정보만 메타 구조체에서 복사, 반환하기
bool DBManager::build_user_info_from_meta(int team_uid, int staff_uid, UserInfo& out_info, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
        return false;
    }
	vector<StaffInfo> meta;
    if (!get_staff_list_by_team(team_uid, meta, out_err_msg)) {
        return false;  // 메타 로드 실패
    }
    for (const auto& m : meta) {
        if (m.staff_uid == staff_uid) {  // 직원 uid가 일치하는지 확인
            out_info.id = m.id;
            out_info.pw = m.pw;
            out_info.phone_number = m.phone;
            out_info.company_name = m.company_name;
			out_info.grade_name = m.grade_name;
            return true;  
        }
	}
}

//============ [인수인계] ============
bool DBManager::get_handover_notes_by_team(int team_uid, vector<HandoverNoteInfo>& out_notes, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
        return false;
    }

    try {
        unique_ptr<sql::PreparedStatement> stmt(
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
        unique_ptr<sql::ResultSet> res(stmt->executeQuery());

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
        out_err_msg = string("[DB 오류] ") + e.what();
        return false;
    }
}

bool DBManager::get_handover_notes_by_uid(int handover_uid, HandoverNoteInfo& out_note, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
        return false;
    }

    try {
        unique_ptr<sql::PreparedStatement> stmt(
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
                    h.is_refined,
                    h.file_name
                FROM handover_note h
                LEFT JOIN staff s ON h.staff_uid = s.staff_uid
                WHERE h.handover_uid = ?
            )")
        );

        stmt->setInt(1, handover_uid);

        unique_ptr<sql::ResultSet> res(stmt->executeQuery());
        if (!res->next()) {
            out_err_msg = u8"해당 인수인계 정보를 찾을 수 없습니다.";
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
        out_note.file_name = res->getString("file_name").c_str();

        return true;
    }
    catch (sql::SQLException& e) {
        out_err_msg = string(u8"[DB 예외] ") + e.what();
        return false;
    }
}

bool DBManager::reg_handover(int staff_uid, int team_uid, const string& title, const string& text, const string& text_particular,  const string& additional_info, int is_attached, const string& file_name,
                              string& note_type, string& shift_type, json& out_json, string& out_err_msg)
{
    out_json = json::object();

    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
        return false;
    }

    try {
        // 필요한 컬럼만 정확히 나열 (테이블 정의와 일치해야 함)
        const string q =
            "INSERT INTO handover_note "
            "(staff_uid, team_uid, title, text, text_particular, additional_info, is_attached, file_name, note_type, shift_type) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)";

        unique_ptr<sql::PreparedStatement> stmt(conn_->prepareStatement(q));
        stmt->setInt(1, staff_uid);
        stmt->setInt(2, team_uid);
        stmt->setString(3, title);
        stmt->setString(4, text);
        stmt->setString(5, text_particular);
        stmt->setString(6, additional_info);
        stmt->setInt(7, is_attached);
        stmt->setString(8, file_name);
        stmt->setString(9, note_type);
        stmt->setString(10, shift_type);

        int affected = stmt->executeUpdate();
        if (affected != 1) {
            out_err_msg = u8"[DB 오류] 등록 실패(영향 행 0)";
            return false;
        }

        // PK 조회
        unique_ptr<sql::Statement> keyStmt(conn_->createStatement());
        unique_ptr<sql::ResultSet> rs(keyStmt->executeQuery("SELECT LAST_INSERT_ID()"));
        if (!rs || !rs->next()) {
            out_err_msg = u8"[DB 오류] LAST_INSERT_ID 조회 실패";
            return false;
        }
        int handover_uid = rs->getInt(1);

        // (선택) 방금 INSERT한 행의 시간 등 부가정보를 함께 반환하고 싶다면 조회
        unique_ptr<sql::PreparedStatement> sel(
            conn_->prepareStatement(
                "SELECT DATE_FORMAT(handover_time, '%Y-%m-%d %H:%i:%s') AS handover_time "
                "FROM handover_note WHERE handover_uid=? LIMIT 1"
            )
        );
        sel->setInt(1, handover_uid);
        unique_ptr<sql::ResultSet> rs2(sel->executeQuery());
        string handover_time;
        if (rs2 && rs2->next()) {
            handover_time = rs2->getString("handover_time");
        }

        //  JSON으로 래핑해서 반환
        out_json = {
            { "data", {
                { "handover_uid",   handover_uid },
            }}
        };

        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string(u8"[SQL 예외] ") + e.what();
        return false;
    }
    catch (const exception& e) {
        out_err_msg = string(u8"[예외] ") + e.what();
        return false;
    }
}

//============ [** 근무정보 구조체 정보 가져오기] ============
vector<ScheduleEntry> DBManager::get_team_schedule(int team_uid, const string& target_month) {
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
        cerr << "[DB 오류] 스케줄 불러오기 실패: " << e.what() << endl;
    }
    return schedule_list;
}

vector<ScheduleEntry> DBManager::get_staff_schedule(int staff_uid, const string& target_month) {
    vector<ScheduleEntry> schedule_list;

    try {
        auto stmt = conn_->prepareStatement(R"(
            SELECT schedule_uid, staff_uid, duty_date, shift_type, hours 
            FROM schedule
            WHERE staff_uid = ? AND DATE_FORMAT(duty_date, '%Y-%m') = ?
            ORDER BY duty_date ASC

        )");
        stmt->setInt(1, staff_uid);
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
        cerr << "[DB 오류] 스케줄 불러오기 실패: " << e.what() << endl;
    }
    return schedule_list;
}

//오늘의 근무
bool DBManager::check_today_duty_for_admin(int team_uid,const string& date,json& out_json,string& out_err_msg) {
    if (!conn_) {
        out_err_msg = "[DB 오류] DB 연결 실패";
        return false;
    }

    try {
       unique_ptr<sql::PreparedStatement> stmt(
            conn_->prepareStatement(
                "SELECT scd.shift_type AS shift, "
                "       COALESCE(st.name, '') AS staff_name "
                "  FROM schedule scd "
                "  JOIN staff st ON scd.staff_uid = st.staff_uid "
                " WHERE scd.duty_date = ? "
                "   AND st.team_uid = ? "
                " ORDER BY scd.shift_type, st.name"
            )
        );
        stmt->setString(1, date);
        stmt->setInt(2, team_uid);

       unique_ptr<sql::ResultSet> res(stmt->executeQuery());

       map<string,vector<string>> shift_map;

        while (res->next()) {

#if defined(HAVE_SQLSTRING_ASSTDSTRING)
           string shift = res->getString("shift").asStdString();
           string name = res->getString("staff_name").asStdString();
#else
           string shift =string(res->getString("shift").c_str());
           string name =string(res->getString("staff_name").c_str());
#endif
            shift_map[shift].emplace_back(move(name));
        }

        // JSON 배열 생성
        out_json = json::array();
        for (auto& kv : shift_map) {
            out_json.push_back({
                {"shift", kv.first},
                {"staff", kv.second}
                });
        }
        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg =string("[DB 오류] ") + e.what();
        return false;
    }
}
//이번주 근무
bool DBManager::get_weekly_shift_mon_sun_compact(int staff_uid,const string& date,json& out,string& err)
{
    out = json::object();
    if (!conn_) {
        err = u8"[DB 오류] DB 연결 실패";
        return false;
    }

    try {
        static constexpr char SQL[] = R"SQL(
            SELECT
              t.i AS widx,  -- 0=월 ... 6=일
              s.shift_type AS sh
            FROM
              (SELECT 0 i UNION ALL SELECT 1 UNION ALL SELECT 2
               UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6) t
            CROSS JOIN
              (SELECT DATE_SUB(DATE(?), INTERVAL WEEKDAY(DATE(?)) DAY) AS ws) w
            LEFT JOIN schedule s
              ON s.staff_uid = ?
             AND DATE(s.duty_date) = DATE_ADD(w.ws, INTERVAL t.i DAY)
            ORDER BY t.i;
        )SQL";

        unique_ptr<sql::PreparedStatement> ps(conn_->prepareStatement(SQL));
        ps->setString(1, date);
        ps->setString(2, date);
        ps->setInt(3, staff_uid);

        unique_ptr<sql::ResultSet> rs(ps->executeQuery());

        array<string, 7> week; week.fill("-");
        while (rs && rs->next()) {
            int widx = rs->getInt("widx");
            if (widx < 0 || widx > 6) continue;
            if (!rs->isNull("sh")) {
                sql::SQLString ssh = rs->getString("sh");
                string sh(ssh.c_str(), ssh.length());
                if (!sh.empty()) week[widx] = sh;
            }
        }

        // JSON 포장
        json arr = json::array();
        for (const auto& s : week) arr.push_back(s);
        out["shift_type"] = arr;   // 예: ["D","E","-","O","-","-","N"]

        return true;
    }
    catch (const sql::SQLException& e) {
        err = string(u8"[SQL 예외] ") + e.what();
        return false;
    }
}

//============ [** 공지사항 구조체 정보 가져오기] ============
bool DBManager::get_notice_list_by_team(int team_uid, vector<NoticeSummary>& out_list, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
        return false;
    }
    try {
        // staff_uid 통해 이름을 조인
        unique_ptr<sql::PreparedStatement> stmt(
            conn_->prepareStatement(R"(
                SELECT n.notice_uid,
                       s.name AS staff_name,
                       DATE_FORMAT(n.notice_date, '%Y-%m-%d') AS notice_date,
                       n.title
                  FROM notice n
                  JOIN staff s ON n.staff_uid = s.staff_uid
                 WHERE s.team_uid = ?
              ORDER BY n.notice_date DESC, n.notice_uid DESC
            )")
        );
        stmt->setInt(1, team_uid);

        unique_ptr<sql::ResultSet> rs(stmt->executeQuery());
        out_list.clear();
        while (rs->next()) {
            NoticeSummary x;
            x.notice_uid = rs->getInt("notice_uid");
            x.staff_name = rs->getString("staff_name").c_str();
            x.notice_date = rs->getString("notice_date").c_str();
            x.title = rs->getString("title").c_str();
            out_list.push_back(move(x));
        }
        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string(u8"[DB 오류] ") + e.what();
        return false;
    }
}

bool DBManager::get_notice_detail_by_uid(int notice_uid, NoticeDetail& out_detail, string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] DB 연결 실패";
        return false;
    }
    try {
        unique_ptr<sql::PreparedStatement> stmt(
            conn_->prepareStatement(R"(
                SELECT n.notice_uid,
                       s.name AS staff_name,
                       DATE_FORMAT(n.notice_date, '%Y-%m-%d %H:%i:%s') AS notice_date,
                       n.title,
                       n.content
                  FROM notice n
                  JOIN staff s ON n.staff_uid = s.staff_uid
                 WHERE n.notice_uid = ?
                 LIMIT 1
            )")
        );
        stmt->setInt(1, notice_uid);
        unique_ptr<sql::ResultSet> res(stmt->executeQuery());

        if (!res->next()) {
            out_err_msg = u8"해당 공지사항을 찾을 수 없습니다.";
            return false;
        }

        out_detail.notice_uid = res->getInt("notice_uid");
        //out_detail.staff_name = res->getString("staff_name").c_str();
        out_detail.notice_date = res->getString("notice_date").c_str();
        out_detail.title = res->getString("title").c_str();
        out_detail.content = res->getString("content").c_str();
        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = string(u8"[DB 오류] ") + e.what();
        return false;
    }
}

//============ [교대 정보 요청] ============
bool DBManager::req_shift_info_by_team(int team_uid,vector<ShiftInfo>& out_list,string& out_err_msg) {
    if (!conn_) {
        out_err_msg = u8"[DB 오류] 연결 안됨";
        return false;
    }

    try {
       unique_ptr<sql::PreparedStatement> stmt(
            conn_->prepareStatement(R"(
                SELECT shift_type, 
                       COALESCE(DATE_FORMAT(shift_start, '%H:%i'), '00:00') AS start_time,
                       COALESCE(DATE_FORMAT(shift_end, '%H:%i'), '00:00')   AS end_time,
                       CASE 
                           WHEN shift_start IS NULL OR shift_end IS NULL THEN 0
                           ELSE TIMESTAMPDIFF(HOUR, shift_start, shift_end)
                       END AS duty_hours
                  FROM shift_code
                 WHERE team_uid = ?
                 ORDER BY shift_code_uid
            )")
        );
        stmt->setInt(1, team_uid);
       unique_ptr<sql::ResultSet> rs(stmt->executeQuery());

        out_list.clear();
        while (rs->next()) {
            ShiftInfo info;
            info.duty_type = rs->getString("shift_type");
            info.start_time = rs->getString("start_time");
            info.end_time = rs->getString("end_time");
            info.duty_hours = rs->getInt("duty_hours");
            out_list.push_back(info);
        }
        return true;
    }
    catch (const sql::SQLException& e) {
        out_err_msg = e.what();
        return false;
    }
}

