#include "DBManager.h"
#include <iostream>

#include <windows.h>

using namespace std;

DBManager::DBManager() {}
DBManager::~DBManager() {}

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

        std::cout << "user: " << properties["user"].c_str() << "\n";
        std::cout << "pw: " << properties["password"].c_str() << "\n";

        conn_.reset(driver->connect(url, properties));
        return true;

    }
    catch (sql::SQLException& e) {
        cerr << " {{(>_<)}} DB 연결 실패: " << e.what() << endl;
        return false;
    }
}
