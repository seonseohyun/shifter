
#include <ortools/sat/cp_model.h>
#include <ortools/sat/cp_model_builder.h>
#include <ortools/sat/cp_model_solver.h>
#include <iostream>
#include <vector>
#include <string>

namespace operations_research::sat {

void CreateShiftSchedule() {
    // CP-SAT 모델 생성
    CpModelBuilder model;

    // 데이터 정의
    const int num_employees = 3;
    const int num_days = 7;
    const std::vector<std::string> shifts = {"D", "E", "N", "O"};
    const int num_shifts = shifts.size();

    // 변수: schedule[i][d]는 직원 i가 날짜 d에 배정된 근무 (0: D, 1: E, 2: N, 3: O)
    std::vector<std::vector<IntVar>> schedule(num_employees);
    for (int i = 0; i < num_employees; ++i) {
        for (int d = 0; d < num_days; ++d) {
            schedule[i].push_back(
                model.NewIntVar(0, num_shifts - 1, "emp" + std::to_string(i) + "_day" + std::to_string(d)));
        }
    }

    // 제약 조건 1: 각 날짜, 시간대별 최소 1명 배정
    for (int d = 0; d < num_days; ++d) {
        std::vector<IntVar> day_shifts;
        std::vector<IntVar> evening_shifts;
        std::vector<IntVar> night_shifts;
        for (int i = 0; i < num_employees; ++i) {
            day_shifts.push_back(model.NewBoolVar(""));
            evening_shifts.push_back(model.NewBoolVar(""));
            night_shifts.push_back(model.NewBoolVar(""));
            model.AddEquality(schedule[i][d], 0).OnlyEnforceIf(day_shifts.back());
            model.AddNotEqual(schedule[i][d], 0).OnlyEnforceIf(Not(day_shifts.back()));
            model.AddEquality(schedule[i][d], 1).OnlyEnforceIf(evening_shifts.back());
            model.AddNotEqual(schedule[i][d], 1).OnlyEnforceIf(Not(evening_shifts.back()));
            model.AddEquality(schedule[i][d], 2).OnlyEnforceIf(night_shifts.back());
            model.AddNotEqual(schedule[i][d], 2).OnlyEnforceIf(Not(night_shifts.back()));
        }
        model.AddGreaterOrEqual(LinearExpr::Sum(day_shifts), 1);     // 최소 1명 Day
        model.AddGreaterOrEqual(LinearExpr::Sum(evening_shifts), 1); // 최소 1명 Evening
        model.AddGreaterOrEqual(LinearExpr::Sum(night_shifts), 1);   // 최소 1명 Night
    }

    // 제약 조건 2: Night 근무 후 다음 날은 Off 또는 Evening만 가능
    for (int i = 0; i < num_employees; ++i) {
        for (int d = 0; d < num_days - 1; ++d) {
            BoolVar is_night = model.NewBoolVar("");
            BoolVar is_next_off = model.NewBoolVar("");
            BoolVar is_next_evening = model.NewBoolVar("");
            model.AddEquality(schedule[i][d], 2).OnlyEnforceIf(is_night);
            model.AddNotEqual(schedule[i][d], 2).OnlyEnforceIf(Not(is_night));
            model.AddEquality(schedule[i][d + 1], 3).OnlyEnforceIf(is_next_off);
            model.AddNotEqual(schedule[i][d + 1], 3).OnlyEnforceIf(Not(is_next_off));
            model.AddEquality(schedule[i][d + 1], 1).OnlyEnforceIf(is_next_evening);
            model.AddNotEqual(schedule[i][d + 1], 1).OnlyEnforceIf(Not(is_next_evening));
            model.AddBoolOr({Not(is_night), is_next_off, is_next_evening});
        }
    }

    // 제약 조건 3: 공정성 - Night 근무 수 편차 최소화
    std::vector<LinearExpr> night_counts;
    for (int i = 0; i < num_employees; ++i) {
        std::vector<IntVar> night_indicators;
        for (int d = 0; d < num_days; ++d) {
            IntVar is_night = model.NewBoolVar("");
            model.AddEquality(schedule[i][d], 2).OnlyEnforceIf(is_night);
            model.AddNotEqual(schedule[i][d], 2).OnlyEnforceIf(Not(is_night));
            night_indicators.push_back(is_night);
        }
        night_counts.push_back(LinearExpr::Sum(night_indicators));
    }
    IntVar max_nights = model.NewIntVar(0, num_days, "max_nights");
    IntVar min_nights = model.NewIntVar(0, num_days, "min_nights");
    model.AddMaxEquality(max_nights, night_counts);
    model.AddMinEquality(min_nights, night_counts);
    model.Minimize(max_nights - min_nights);

    // 솔버 실행
    CpSolverResponse response = Solve(model);
    if (response.status() == CpSolverStatus::OPTIMAL || response.status() == CpSolverStatus::FEASIBLE) {
        std::cout << "스케줄 생성 완료:\n";
        for (int d = 0; d < num_days; ++d) {
            std::cout << "Day " << d + 1 << ":\n";
            for (int i = 0; i < num_employees; ++i) {
                int shift_idx = response.SolutionValue(schedule[i][d]);
                std::cout << "  Employee " << i + 1 << ": " << shifts[shift_idx] << "\n";
            }
        }
    } else {
        std::cout << "해를 찾을 수 없습니다.\n";
    }
}

} // namespace operations_research::sat

int main() {
    operations_research::sat::CreateShiftSchedule();
    return 0;
}