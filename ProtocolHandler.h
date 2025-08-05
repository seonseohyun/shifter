#pragma once
#include <nlohmann/json.hpp>
using json = nlohmann::json;

class DBManager;

class ProtocolHandler
{
public:
    //�α���
    static json handle_login                (const json& json, DBManager& db);
    static json handle_login_admin          (const json& root, DBManager& db);
    //�ٹ� ���� ��û ����
    static json handle_shift_change_detail  (const json& root, DBManager& db);
    static json handle_ask_shift_change     (const json& root, DBManager& db);
    static json handle_cancel_shift_change  (const json& root, DBManager& db);
};

//������� ���� �ľ� �� json �Ľ� �� �������� �б� �� DBManager�� ���� ����
//�� ����� ProtocolHandler�� ���� �� ���� JSON ���� �� send�� Ŭ���̾�Ʈ�� ��ȯ��