#include "DateUtil.h"
#include <ctime>
#include <sstream>
#include <iomanip>

namespace DateUtil {
    std::string get_today() {
        std::time_t t = std::time(nullptr);
        std::tm tm;
        localtime_s(&tm, &t);  // 안전한 방식

        std::ostringstream oss;
        oss << std::put_time(&tm, "%Y-%m-%d");
        return oss.str();
    }
}
