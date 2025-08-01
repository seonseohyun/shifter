C++ 서버: 자연어 입력을 파싱하여 직원 ID, 날짜, 기존 근무, 변경 희망 근무를 추출하고, 이를 JSON 파일(change_requests.json)에 저장합니다. 이후 Python 스크립트를 실행합니다.
Python 스크립트: change_requests.json을 읽어 동적으로 제약 조건을 추가하고, OR-Tools를 사용해 근무표를 생성합니다.
안정성 보장: JSON 입력 검증, 원자적 파일 쓰기, 오류 처리 및 로깅을 포함하여 안정성과 보안을 강화합니다.



개선된 cpp코드 
#include <iostream>
#include <fstream>
#include <string>
#include <regex>
#include <cstdlib>
#include <stdexcept>
#include <nlohmann/json.hpp> // JSON 처리 라이브러리[](https://github.com/nlohmann/json)

using json = nlohmann::json;

struct ParsedData {
    std::string name;
    std::string date;
    std::string fromShift;
    std::string toShift;
};

ParsedData parseNaturalLanguage(const std::string& input) {
    std::regex pattern(R"((\S+)\s*(\d{4}-\d{2}-\d{2})\s*([A-Z])근무에서\s*([A-Z])근무로\s*변경을\s*희망합니다\.)");
    std::smatch matches;
    if (std::regex_match(input, matches, pattern)) {
        return {matches[1].str(), matches[2].str(), matches[3].str(), matches[4].str()};
    }
    throw std::invalid_argument("자연어 입력을 해석할 수 없습니다.");
}

std::string getStaffIdFromName(const std::string& name, const std::string& pythonFilePath) {
    std::ifstream fileIn(pythonFilePath);
    if (!fileIn.is_open()) {
        throw std::runtime_error("Python 파일을 열 수 없습니다: " + pythonFilePath);
    }
    std::string pythonContent((std::istreambuf_iterator<char>(fileIn)), std::istreambuf_iterator<char>());
    fileIn.close();

    std::regex staffPattern(R"(\{"name": "([^"]+)", "staff_id": (\d+),)");
    std::sregex_iterator iter(pythonContent.begin(), pythonContent.end(), staffPattern);
    std::sregex_iterator end;
    for (; iter != end; ++iter) {
        std::smatch match = *iter;
        if (match[1].str() == name) {
            return match[2].str();
        }
    }
    throw std::runtime_error("해당 이름을 가진 직원을 찾을 수 없습니다: " + name);
}

void updateAndExecuteShiftScheduler(const std::string& naturalLanguageInput, const std::string& pythonFilePath) {
    try {
        // 단계 1: 자연어 파싱
        ParsedData parsed = parseNaturalLanguage(naturalLanguageInput);

        // 단계 2: 직원 이름으로 staff_id 조회
        std::string staffId = getStaffIdFromName(parsed.name, pythonFilePath);

        // 단계 3: 날짜 유효성 검사 (2025-08-01 ~ 2025-08-31)
        int year, month, day;
        if (sscanf(parsed.date.c_str(), "%d-%d-%d", &year, &month, &day) != 3 ||
            year != 2025 || month != 8 || day < 1 || day > 31) {
            throw std::invalid_argument("유효하지 않은 날짜입니다. 2025-08-01 ~ 2025-08-31 범위여야 합니다.");
        }

        // 단계 4: JSON 요청 생성
        json request = {
            {"staff_id", staffId},
            {"date", parsed.date},
            {"original_shift", parsed.fromShift},
            {"desired_shift", parsed.toShift}
        };

        // 단계 5: JSON 파일 읽기 및 업데이트
        std::string jsonPath = "./data/change_requests.json";
        json requests;
        std::ifstream jsonIn(jsonPath);
        if (jsonIn.is_open()) {
            jsonIn >> requests;
            jsonIn.close();
        } else {
            requests = json::array();
        }
        requests.push_back(request);

        // 단계 6: JSON 파일 저장 (원자적 쓰기)
        std::string tempPath = jsonPath + ".tmp";
        std::ofstream jsonOut(tempPath);
        if (!jsonOut.is_open()) {
            throw std::runtime_error("JSON 파일을 저장할 수 없습니다: " + tempPath);
        }
        jsonOut << requests.dump(2);
        jsonOut.close();
        std::rename(tempPath.c_str(), jsonPath.c_str());

        // 단계 7: Python 스크립트 실행
        std::string command = "python " + pythonFilePath;
        int result = std::system(command.c_str());
        if (result != 0) {
            throw std::runtime_error("Python 실행 오류: 반환 코드 " + std::to_string(result));
        }

        std::cout << "근무표 생성이 완료되었습니다. 변경 요청이 반영되었습니다." << std::endl;
    } catch (const std::exception& ex) {
        std::cerr << "오류 발생: " << ex.what() << std::endl;
    }
}

int main() {
    std::string input = "박주영 2025-08-05 D근무에서 E근무로 변경을 희망합니다.";
    std::string pythonPath = "shift_scheduler.py";
    updateAndExecuteShiftScheduler(input, pythonPath);
    return 0;
}

개선된 python코드
from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import os
import json

def create_individual_shift_schedule(staff_data, shift_type):
    if shift_type not in [2, 3, 4]:
        raise ValueError("shift_type must be 2, 3, or 4")

    model = cp_model.CpModel()

    # Define shifts based on shift_type
    if shift_type == 2:
        shifts = ['D', 'N', 'O']
        night_shift = 'N'
    elif shift_type == 3:
        shifts = ['D', 'E', 'N', 'O']
        night_shift = 'N'
    elif shift_type == 4:
        shifts = ['M', 'D', 'E', 'N', 'O']
        night_shift = 'N'

    shift_hours = {s: 8 if s != 'O' else 0 for s in shifts}
    num_days = 31
    days = range(num_days)
    start_date = datetime(2025, 8, 1)
    num_weeks = (num_days + 6) // 7

    all_people = staff_data["staff"]
    unique_grades = set(person["grade"] for person in all_people)
    if len(unique_grades) > 5:
        raise ValueError("Up to 5 unique grades are supported.")

    schedule = {}
    for person in all_people:
        sid = str(person["staff_id"])
        for d in days:
            for s in shifts:
                schedule[(sid, d, s)] = model.NewBoolVar(f"{sid}_d{d}_{s}")

    # Load and apply change requests from JSON
    change_requests_path = "./data/change_requests.json"
    change_requests = []
    if os.path.exists(change_requests_path):
        try:
            with open(change_requests_path, "r", encoding="utf-8") as f:
                change_requests = json.load(f)
        except Exception as e:
            print(f"[WARNING] JSON 파일 읽기 오류: {e}")

    for req in change_requests:
        try:
            sid = str(req["staff_id"])
            req_date = datetime.strptime(req["date"], '%Y-%m-%d')
            d = (req_date - start_date).days
            s = req["desired_shift"]
            if 0 <= d < num_days and s in shifts and sid in [str(p["staff_id"]) for p in all_people]:
                model.Add(schedule[(sid, d, s)] == 1)
                print(f"[INFO] {sid}의 {req['date']} 근무를 {s}로 고정")
            else:
                print(f"[WARNING] 유효하지 않은 요청: staff_id={sid}, date={req['date']}, shift={s}")
        except Exception as e:
            print(f"[WARNING] 요청 처리 오류: {e}")

    # 기존 제약 조건들 (이하 동일)
    # Each individual has exactly one shift per day
    for person in all_people:
        sid = str(person["staff_id"])
        for d in days:
            model.AddExactlyOne([schedule[(sid, d, s)] for s in shifts])

    # ... (나머지 코드는 기존과 동일)

    