#pragma once
#include <mariadb/conncpp.hpp>
#include <memory>
#include <string>
using namespace std;

class DBManager
{
public:
    DBManager();
    ~DBManager();

    // DB ����
    bool connect();

private:
    unique_ptr<sql::Connection> conn_;

};

