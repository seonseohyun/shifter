#include <iostream>
#include <string>
#include <vector>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdint.h>
#include <fstream>
#include <ctime>
#include <iomanip>
#include <sstream>
#include <thread>
#include <chrono>

const std::string SERVER_HOST = "127.0.0.1";
const int SERVER_PORT = 6004;

class NurseScheduleClient {
private:
    int sockfd;
    
public:
    NurseScheduleClient() : sockfd(-1) {}
    
    ~NurseScheduleClient() {
        disconnect();
    }
    
    bool connect_to_server() {
        // 소켓 생성
        sockfd = socket(AF_INET, SOCK_STREAM, 0);
        if (sockfd < 0) {
            std::cerr << "[ERROR] 소켓 생성 실패" << std::endl;
            return false;
        }
        
        // 서버 주소 설정
        struct sockaddr_in server_addr;
        memset(&server_addr, 0, sizeof(server_addr));
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(SERVER_PORT);
        server_addr.sin_addr.s_addr = inet_addr(SERVER_HOST.c_str());
        
        // 서버 연결
        if (connect(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            std::cerr << "[ERROR] 서버 연결 실패 (" << SERVER_HOST << ":" << SERVER_PORT << ")" << std::endl;
            close(sockfd);
            sockfd = -1;
            return false;
        }
        
        std::cout << "[INFO] 서버 연결 성공: " << SERVER_HOST << ":" << SERVER_PORT << std::endl;
        return true;
    }
    
    void disconnect() {
        if (sockfd >= 0) {
            close(sockfd);
            sockfd = -1;
        }
    }
    
    std::string send_request(const std::string& json_request) {
        if (sockfd < 0) {
            std::cerr << "[ERROR] 서버 연결되지 않음" << std::endl;
            return "";
        }
        
        // JSON 데이터 전송
        ssize_t sent_bytes = send(sockfd, json_request.c_str(), json_request.length(), 0);
        if (sent_bytes < 0) {
            std::cerr << "[ERROR] 데이터 전송 실패" << std::endl;
            return "";
        }
        
        std::cout << "[INFO] 요청 전송 완료: " << sent_bytes << " bytes" << std::endl;
        
        // 소켓 쓰기 종료
        shutdown(sockfd, SHUT_WR);
        
        // 응답 수신
        std::string response;
        char buffer[4096];
        ssize_t received;
        
        while ((received = recv(sockfd, buffer, sizeof(buffer) - 1, 0)) > 0) {
            buffer[received] = '\0';
            response += buffer;
        }
        
        if (received < 0) {
            std::cerr << "[ERROR] 응답 수신 실패" << std::endl;
            return "";
        }
        
        std::cout << "[INFO] 응답 수신 완료: " << response.length() << " bytes" << std::endl;
        return response;
    }
};

// 테스트 케이스별 간호사 데이터 생성
std::string create_test_case_data(int test_case) {
    switch(test_case) {
        case 1: // 표준 중형 병원 (15명, 베테랑 많음)
            return R"({"staff": [
                {"name": "김수련", "staff_id": 1001, "grade": 1, "grade_name": "수간호사", "total_monthly_work_hours": 200},
                {"name": "이영희", "staff_id": 1002, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 195},
                {"name": "박민정", "staff_id": 1003, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 190},
                {"name": "최은영", "staff_id": 1004, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 198},
                {"name": "정소희", "staff_id": 1005, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 192},
                {"name": "한미래", "staff_id": 1006, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 195},
                {"name": "윤서영", "staff_id": 1007, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 185},
                {"name": "강혜진", "staff_id": 1008, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 188},
                {"name": "오지은", "staff_id": 1009, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 190},
                {"name": "송나리", "staff_id": 1010, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 187},
                {"name": "임지현", "staff_id": 1011, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 189},
                {"name": "조은서", "staff_id": 1012, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 186},
                {"name": "김하늘", "staff_id": 1013, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 175},
                {"name": "이지원", "staff_id": 1014, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 170},
                {"name": "박소연", "staff_id": 1015, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 180}
            ]})";
        
        case 2: // 소규모 클리닉 (8명, 신규가 많음)
            return R"({"staff": [
                {"name": "김수련", "staff_id": 2001, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 200},
                {"name": "이영희", "staff_id": 2002, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 195},
                {"name": "박민정", "staff_id": 2003, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 185},
                {"name": "최은영", "staff_id": 2004, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 190},
                {"name": "정소희", "staff_id": 2005, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 170},
                {"name": "한미래", "staff_id": 2006, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 175},
                {"name": "윤서영", "staff_id": 2007, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 172},
                {"name": "강혜진", "staff_id": 2008, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 168}
            ]})";
            
        case 3: // 대형병원 (25명, 균등 분포)
            return R"({"staff": [
                {"name": "김수련", "staff_id": 3001, "grade": 1, "grade_name": "수간호사", "total_monthly_work_hours": 205},
                {"name": "이영희", "staff_id": 3002, "grade": 1, "grade_name": "수간호사", "total_monthly_work_hours": 200},
                {"name": "박민정", "staff_id": 3003, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 198},
                {"name": "최은영", "staff_id": 3004, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 195},
                {"name": "정소희", "staff_id": 3005, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 192},
                {"name": "한미래", "staff_id": 3006, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 197},
                {"name": "윤서영", "staff_id": 3007, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 193},
                {"name": "강혜진", "staff_id": 3008, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 190},
                {"name": "오지은", "staff_id": 3009, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 188},
                {"name": "송나리", "staff_id": 3010, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 191},
                {"name": "임지현", "staff_id": 3011, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 189},
                {"name": "조은서", "staff_id": 3012, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 194},
                {"name": "김하늘", "staff_id": 3013, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 185},
                {"name": "이지원", "staff_id": 3014, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 187},
                {"name": "박소연", "staff_id": 3015, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 186},
                {"name": "최하린", "staff_id": 3016, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 184},
                {"name": "정민수", "staff_id": 3017, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 188},
                {"name": "한지민", "staff_id": 3018, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 183},
                {"name": "윤채영", "staff_id": 3019, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 189},
                {"name": "강서준", "staff_id": 3020, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 175},
                {"name": "오예린", "staff_id": 3021, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 172},
                {"name": "송다은", "staff_id": 3022, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 178},
                {"name": "임수아", "staff_id": 3023, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 170},
                {"name": "조민준", "staff_id": 3024, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 174},
                {"name": "김예은", "staff_id": 3025, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 176}
            ]})";
            
        case 4: // 최소 인원 (6명, 경계 케이스)
            return R"({"staff": [
                {"name": "김수련", "staff_id": 4001, "grade": 1, "grade_name": "수간호사", "total_monthly_work_hours": 209},
                {"name": "이영희", "staff_id": 4002, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 208},
                {"name": "박민정", "staff_id": 4003, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 205},
                {"name": "최은영", "staff_id": 4004, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 200},
                {"name": "정소희", "staff_id": 4005, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 195},
                {"name": "한미래", "staff_id": 4006, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 180}
            ]})";
            
        case 5: // 2교대 시스템 (12명)
            return R"({"staff": [
                {"name": "김수련", "staff_id": 5001, "grade": 1, "grade_name": "수간호사", "total_monthly_work_hours": 200},
                {"name": "이영희", "staff_id": 5002, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 195},
                {"name": "박민정", "staff_id": 5003, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 190},
                {"name": "최은영", "staff_id": 5004, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 185},
                {"name": "정소희", "staff_id": 5005, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 188},
                {"name": "한미래", "staff_id": 5006, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 192},
                {"name": "윤서영", "staff_id": 5007, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 180},
                {"name": "강혜진", "staff_id": 5008, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 183},
                {"name": "오지은", "staff_id": 5009, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 187},
                {"name": "송나리", "staff_id": 5010, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 185},
                {"name": "임지현", "staff_id": 5011, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 175},
                {"name": "조은서", "staff_id": 5012, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 170}
            ]})";
            
        case 6: // 응급실 (18명, 고강도)
            return R"({"staff": [
                {"name": "김응급", "staff_id": 6001, "grade": 1, "grade_name": "수간호사", "total_monthly_work_hours": 195},
                {"name": "이응급", "staff_id": 6002, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 190},
                {"name": "박응급", "staff_id": 6003, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 188},
                {"name": "최응급", "staff_id": 6004, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 192},
                {"name": "정응급", "staff_id": 6005, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 185},
                {"name": "한응급", "staff_id": 6006, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 187},
                {"name": "윤응급", "staff_id": 6007, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 190},
                {"name": "강응급", "staff_id": 6008, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 186},
                {"name": "오응급", "staff_id": 6009, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 180},
                {"name": "송응급", "staff_id": 6010, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 182},
                {"name": "임응급", "staff_id": 6011, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 184},
                {"name": "조응급", "staff_id": 6012, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 183},
                {"name": "김신규", "staff_id": 6013, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 181},
                {"name": "이신규", "staff_id": 6014, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 179},
                {"name": "박신규", "staff_id": 6015, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 170},
                {"name": "최신규", "staff_id": 6016, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 175},
                {"name": "정신규", "staff_id": 6017, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 172},
                {"name": "한신규", "staff_id": 6018, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 168}
            ]})";
            
        case 7: // 중환자실 (10명, 전문성 위주)
            return R"({"staff": [
                {"name": "김중환", "staff_id": 7001, "grade": 1, "grade_name": "수간호사", "total_monthly_work_hours": 200},
                {"name": "이중환", "staff_id": 7002, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 195},
                {"name": "박중환", "staff_id": 7003, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 192},
                {"name": "최중환", "staff_id": 7004, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 190},
                {"name": "정중환", "staff_id": 7005, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 188},
                {"name": "한중환", "staff_id": 7006, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 193},
                {"name": "윤중환", "staff_id": 7007, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 185},
                {"name": "강중환", "staff_id": 7008, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 187},
                {"name": "오중환", "staff_id": 7009, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 180},
                {"name": "송중환", "staff_id": 7010, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 175}
            ]})";
            
        case 8: // 야간 전담 (14명, 야간 특화)
            return R"({"staff": [
                {"name": "김야간", "staff_id": 8001, "grade": 1, "grade_name": "수간호사", "total_monthly_work_hours": 190},
                {"name": "이야간", "staff_id": 8002, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 185},
                {"name": "박야간", "staff_id": 8003, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 188},
                {"name": "최야간", "staff_id": 8004, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 183},
                {"name": "정야간", "staff_id": 8005, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 180},
                {"name": "한야간", "staff_id": 8006, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 182},
                {"name": "윤야간", "staff_id": 8007, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 186},
                {"name": "강야간", "staff_id": 8008, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 175},
                {"name": "오야간", "staff_id": 8009, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 178},
                {"name": "송야간", "staff_id": 8010, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 177},
                {"name": "임야간", "staff_id": 8011, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 179},
                {"name": "조야간", "staff_id": 8012, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 176},
                {"name": "김전담", "staff_id": 8013, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 170},
                {"name": "이전담", "staff_id": 8014, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 172}
            ]})";
            
        case 9: // 부족 인력 (7명, 스트레스 테스트)
            return R"({"staff": [
                {"name": "김부족", "staff_id": 9001, "grade": 1, "grade_name": "수간호사", "total_monthly_work_hours": 209},
                {"name": "이부족", "staff_id": 9002, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 208},
                {"name": "박부족", "staff_id": 9003, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 205},
                {"name": "최부족", "staff_id": 9004, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 207},
                {"name": "정부족", "staff_id": 9005, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 200},
                {"name": "한부족", "staff_id": 9006, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 198},
                {"name": "윤부족", "staff_id": 9007, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 190}
            ]})";
            
        case 10: // 소방서 (20명, D24 시스템)
            return R"({"staff": [
                {"name": "김소방", "staff_id": 1001, "grade": 1, "grade_name": "소방관", "total_monthly_work_hours": 180},
                {"name": "이소방", "staff_id": 1002, "grade": 1, "grade_name": "소방관", "total_monthly_work_hours": 175},
                {"name": "박소방", "staff_id": 1003, "grade": 2, "grade_name": "소방교", "total_monthly_work_hours": 185},
                {"name": "최소방", "staff_id": 1004, "grade": 2, "grade_name": "소방교", "total_monthly_work_hours": 182},
                {"name": "정소방", "staff_id": 1005, "grade": 2, "grade_name": "소방교", "total_monthly_work_hours": 178},
                {"name": "한소방", "staff_id": 1006, "grade": 2, "grade_name": "소방교", "total_monthly_work_hours": 180},
                {"name": "윤소방", "staff_id": 1007, "grade": 3, "grade_name": "소방사", "total_monthly_work_hours": 170},
                {"name": "강소방", "staff_id": 1008, "grade": 3, "grade_name": "소방사", "total_monthly_work_hours": 172},
                {"name": "오소방", "staff_id": 1009, "grade": 3, "grade_name": "소방사", "total_monthly_work_hours": 175},
                {"name": "송소방", "staff_id": 1010, "grade": 3, "grade_name": "소방사", "total_monthly_work_hours": 173},
                {"name": "임소방", "staff_id": 1011, "grade": 3, "grade_name": "소방사", "total_monthly_work_hours": 174},
                {"name": "조소방", "staff_id": 1012, "grade": 3, "grade_name": "소방사", "total_monthly_work_hours": 171},
                {"name": "김소방2", "staff_id": 1013, "grade": 4, "grade_name": "소방위", "total_monthly_work_hours": 165},
                {"name": "이소방2", "staff_id": 1014, "grade": 4, "grade_name": "소방위", "total_monthly_work_hours": 168},
                {"name": "박소방2", "staff_id": 1015, "grade": 4, "grade_name": "소방위", "total_monthly_work_hours": 167},
                {"name": "최소방2", "staff_id": 1016, "grade": 4, "grade_name": "소방위", "total_monthly_work_hours": 169},
                {"name": "정소방2", "staff_id": 1017, "grade": 5, "grade_name": "소방장", "total_monthly_work_hours": 160},
                {"name": "한소방2", "staff_id": 1018, "grade": 5, "grade_name": "소방장", "total_monthly_work_hours": 162},
                {"name": "윤소방2", "staff_id": 1019, "grade": 5, "grade_name": "소방장", "total_monthly_work_hours": 158},
                {"name": "강소방2", "staff_id": 1020, "grade": 5, "grade_name": "소방장", "total_monthly_work_hours": 163}
            ]})";
            
        default: // 기본 케이스 (원래 12명 데이터)
            return R"({"staff": [
                {"name": "김수련", "staff_id": 1001, "grade": 1, "grade_name": "수간호사", "total_monthly_work_hours": 195},
                {"name": "이영희", "staff_id": 1002, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 190},
                {"name": "박민정", "staff_id": 1003, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 180},
                {"name": "최은영", "staff_id": 1004, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 200},
                {"name": "정소희", "staff_id": 1005, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 188},
                {"name": "한미래", "staff_id": 1006, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 205},
                {"name": "윤서영", "staff_id": 1007, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 192},
                {"name": "강혜진", "staff_id": 1008, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 198},
                {"name": "오지은", "staff_id": 1009, "grade": 5, "grade_name": "신규간호사", "total_monthly_work_hours": 175},
                {"name": "송나리", "staff_id": 1010, "grade": 4, "grade_name": "일반간호사", "total_monthly_work_hours": 185},
                {"name": "임지현", "staff_id": 1011, "grade": 2, "grade_name": "주임간호사", "total_monthly_work_hours": 208},
                {"name": "조은서", "staff_id": 1012, "grade": 3, "grade_name": "책임간호사", "total_monthly_work_hours": 195}
            ]})";
    }
}

// 테스트 케이스 메타데이터 생성
std::string get_test_case_info(int test_case) {
    switch(test_case) {
        case 1: return "표준 중형병원 (15명, 베테랑 많음)";
        case 2: return "소규모 클리닉 (8명, 신규 많음)";
        case 3: return "대형병원 (25명, 균등분포)";
        case 4: return "최소인원 (6명, 경계케이스)";
        case 5: return "2교대 시스템 (12명)";
        case 6: return "응급실 (18명, 고강도)";
        case 7: return "중환자실 (10명, 전문성 위주)";
        case 8: return "야간전담 (14명, 야간 특화)";
        case 9: return "부족인력 (7명, 스트레스 테스트)";
        case 10: return "소방서 (20명, D24 시스템)";
        default: return "기본케이스 (12명)";
    }
}

std::string get_position_for_case(int test_case) {
    return test_case == 10 ? "소방" : "간호";
}

// C++ 프로토콜 요청 생성 (테스트 케이스별)
std::string create_cpp_protocol_request(int test_case) {
    std::string staff_data = create_test_case_data(test_case);
    std::string position = get_position_for_case(test_case);
    
    // 소방서는 D24 시스템 사용
    std::string shifts_config;
    if (test_case == 10) {
        shifts_config = R"("shifts": ["D24", "Off"],
                "shift_hours": {
                    "D24": 24,
                    "Off": 0
                },
                "night_shifts": ["D24"],
                "off_shifts": ["Off"])";
    } else {
        shifts_config = R"("shifts": ["Day", "Evening", "Night", "Off"],
                "shift_hours": {
                    "Day": 8,
                    "Evening": 8,
                    "Night": 8,
                    "Off": 0
                },
                "night_shifts": ["Night"],
                "off_shifts": ["Off"])";
    }
    
    std::string request = R"({
        "protocol": "gen_schedule",
        "data": {
            "staff_data": )" + staff_data + R"(,
            "position": ")" + position + R"(",
            "target_month": "2025-09",
            "custom_rules": {
                )" + shifts_config + R"(
            }
        }
    })";
    
    return request;
}

// 파일명 생성 (타임스탬프 포함)
std::string generate_timestamp_filename(const std::string& prefix, const std::string& ext) {
    auto t = std::time(nullptr);
    auto tm = *std::localtime(&t);
    std::ostringstream oss;
    oss << "client_data/" << prefix << "_" 
        << std::put_time(&tm, "%Y%m%d_%H%M%S") << ext;
    return oss.str();
}

// 요청 데이터 파일 저장 (비활성화)
bool save_request_to_file(const std::string& request) {
    // 요청 데이터는 더 이상 저장하지 않음
    return true;
}

// 응답 데이터 파일 저장
bool save_response_to_file(const std::string& response) {
    std::string filename = generate_timestamp_filename("cpp_response", ".json");
    std::ofstream file(filename);
    if (!file.is_open()) {
        std::cerr << "[ERROR] 응답 파일 저장 실패: " << filename << std::endl;
        return false;
    }
    file << response;
    file.close();
    std::cout << "[INFO] 📝 응답 데이터 저장: " << filename << std::endl;
    return true;
}

// 응답 분석
void analyze_response(const std::string& response) {
    std::cout << "\n=== 응답 분석 ===" << std::endl;
    
    if (response.empty()) {
        std::cout << "❌ 응답이 비어있음" << std::endl;
        return;
    }
    
    std::cout << "📦 응답 크기: " << response.length() << " bytes" << std::endl;
    
    // 기본 응답 구조 확인
    if (response.find("\"protocol\"") != std::string::npos) {
        std::cout << "✅ C++ 프로토콜 응답 형식 확인됨" << std::endl;
        
        if (response.find("\"py_gen_schedule\"") != std::string::npos) {
            std::cout << "✅ 응답 프로토콜: py_gen_schedule" << std::endl;
        }
    } else {
        std::cout << "❌ C++ 프로토콜 응답 형식 누락" << std::endl;
    }
    
    // 성공 응답 확인
    if (response.find("\"status\": \"ok\"") != std::string::npos) {
        std::cout << "✅ 스케줄 생성 성공" << std::endl;
        
        // 스케줄 데이터 확인
        if (response.find("\"schedule\"") != std::string::npos) {
            std::cout << "✅ 스케줄 데이터 포함됨" << std::endl;
        }
        
        // 처리 시간 추출
        size_t time_pos = response.find("\"solve_time\": \"");
        if (time_pos != std::string::npos) {
            size_t start = time_pos + 15;
            size_t end = response.find("\"", start);
            if (end != std::string::npos) {
                std::string solve_time = response.substr(start, end - start);
                std::cout << "⏱️ 처리 시간: " << solve_time << std::endl;
            }
        }
        
        // 직원 수 확인
        size_t staff_pos = response.find("\"staff_count\": ");
        if (staff_pos != std::string::npos) {
            size_t start = staff_pos + 16;
            size_t end = response.find(",", start);
            if (end == std::string::npos) end = response.find("}", start);
            if (end != std::string::npos) {
                std::string staff_count = response.substr(start, end - start);
                std::cout << "👥 직원 수: " << staff_count << "명" << std::endl;
            }
        }
        
        // 시프트 식별 확인
        if (response.find("\"shifts_identified\"") != std::string::npos) {
            std::cout << "🔍 시프트 식별 정보 포함됨" << std::endl;
        }
        
    } else if (response.find("\"status\": \"error\"") != std::string::npos || response.find("\"result\": \"생성실패\"") != std::string::npos) {
        std::cout << "❌ 스케줄 생성 실패" << std::endl;
        
        // 오류 사유 추출
        size_t reason_pos = response.find("\"reason\": \"");
        if (reason_pos != std::string::npos) {
            size_t start = reason_pos + 11;
            size_t end = response.find("\"", start);
            if (end != std::string::npos) {
                std::string reason = response.substr(start, end - start);
                std::cout << "📝 오류 사유: " << reason << std::endl;
            }
        }
        
        // 해결 방안 확인
        if (response.find("\"suggestions\"") != std::string::npos) {
            std::cout << "💡 해결 방안 제시됨" << std::endl;
        }
    }
    
    // 신규간호사 야간 근무 확인
    size_t schedule_start = response.find("\"schedule\"");
    if (schedule_start != std::string::npos) {
        std::cout << "\n📊 신규간호사 야간 근무 분석:" << std::endl;
        
        // grade 5 (신규간호사) + Night 시프트 검색
        int newbie_night_count = 0;
        size_t pos = 0;
        
        while ((pos = response.find("\"grade\": 5", pos)) != std::string::npos) {
            // 해당 사람이 Night 시프트에 배정되었는지 확인
            size_t shift_start = response.rfind("\"shift\": \"Night\"", pos);
            size_t people_start = response.rfind("\"people\"", pos);
            
            if (shift_start != std::string::npos && people_start != std::string::npos && shift_start > people_start) {
                newbie_night_count++;
            }
            pos++;
        }
        
        if (newbie_night_count == 0) {
            std::cout << "✅ 신규간호사 야간 근무 금지 제약 정상 작동" << std::endl;
        } else {
            std::cout << "❌ 신규간호사 야간 근무 " << newbie_night_count << "건 발견" << std::endl;
        }
    }
}

int main() {
    std::cout << "=== C++ 더미 클라이언트 - 10개 실무 케이스 테스트 ===" << std::endl;
    std::cout << "대상: Python 서버 (" << SERVER_HOST << ":" << SERVER_PORT << ")" << std::endl;
    std::cout << "실행: 10가지 실무 시나리오 테스트" << std::endl;
    
    int total_success = 0;
    int total_failed = 0;
    
    for (int test_case = 1; test_case <= 10; test_case++) {
        std::cout << "\n" << std::string(80, '=') << std::endl;
        std::cout << "🧪 테스트 케이스 " << test_case << ": " << get_test_case_info(test_case) << std::endl;
        std::cout << std::string(80, '=') << std::endl;
        
        NurseScheduleClient client;
        
        // 서버 연결
        if (!client.connect_to_server()) {
            std::cerr << "❌ 서버 연결 실패. 서버가 실행 중인지 확인하세요." << std::endl;
            total_failed++;
            continue;
        }
        
        // 테스트 케이스별 요청 생성
        std::string request = create_cpp_protocol_request(test_case);
        std::cout << "📤 요청 크기: " << request.length() << " bytes" << std::endl;
        std::cout << "📤 직군: " << get_position_for_case(test_case) << std::endl;
        
        // 요청 전송 및 응답 수신
        std::string response = client.send_request(request);
        
        // 연결 종료
        client.disconnect();
        
        // 응답 분석
        if (!response.empty()) {
            // 응답 데이터 파일 저장 (케이스별)
            auto t = std::time(nullptr);
            auto tm = *std::localtime(&t);
            std::ostringstream filename;
            filename << "client_data/test_case_" << std::setfill('0') << std::setw(2) << test_case 
                     << "_" << std::put_time(&tm, "%Y%m%d_%H%M%S") << ".json";
            
            std::ofstream file(filename.str());
            if (file.is_open()) {
                file << response;
                file.close();
                std::cout << "📝 결과 저장: " << filename.str() << std::endl;
            }
            
            analyze_response(response);
            total_success++;
        } else {
            std::cout << "❌ 응답을 받지 못했습니다." << std::endl;
            total_failed++;
        }
        
        // 케이스간 짧은 대기
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }
    
    // 전체 결과 요약
    std::cout << "\n" << std::string(80, '=') << std::endl;
    std::cout << "📊 전체 테스트 결과 요약" << std::endl;
    std::cout << std::string(80, '=') << std::endl;
    std::cout << "✅ 성공: " << total_success << "/10" << std::endl;
    std::cout << "❌ 실패: " << total_failed << "/10" << std::endl;
    std::cout << "📁 결과 파일: client_data/ 디렉토리 확인" << std::endl;
    
    if (total_success == 10) {
        std::cout << "🎉 모든 테스트 케이스 성공!" << std::endl;
    } else if (total_success > 5) {
        std::cout << "⚠️ 일부 케이스 실패, 검토 필요" << std::endl;
    } else {
        std::cout << "🚨 다수 케이스 실패, 시스템 점검 필요" << std::endl;
    }
    
    return total_failed > 0 ? 1 : 0;
}