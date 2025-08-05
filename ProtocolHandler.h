#pragma once
#include <nlohmann/json.hpp>
using json = nlohmann::json;

class DBManager;

class ProtocolHandler
{
public:
    //로그인
    static json handle_login                (const json& json, DBManager& db);
    static json handle_login_admin          (const json& root, DBManager& db);
    //근무 변경 요청 관련
    static json handle_shift_change_detail  (const json& root, DBManager& db);
    static json handle_ask_shift_change     (const json& root, DBManager& db);
    static json handle_cancel_shift_change  (const json& root, DBManager& db);
};

//“헤더로 길이 파악 → json 파싱 → 프로토콜 분기 → DBManager로 로직 실행
//→ 결과를 ProtocolHandler로 전달 → 응답 JSON 구성 → send로 클라이언트에 반환”