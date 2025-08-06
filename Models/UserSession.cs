using System;
using System.Collections.Generic;

namespace ShifterUser.Models
{
    public class UserSession
    {
        /** Member Variables **/
        public Stack<string> NavigationHistory { get; set; } = new Stack<string>(); // 페이지 이동 기록 스택

        private int currentUid = 0;                      // 현재 로그인한 사용자 UID
        private int currentTeamCode = 0;                 // 소속 팀 코드 (team_uid)
        private string currentTeamName = string.Empty;   // 소속 팀 이름 (team_name)
        private string currentDate = string.Empty;       // 금일 날짜

        private int approvedCount = 0;                   // 승인 요청 수
        private int pendingCount = 0;                    // 대기 요청 수
        private int rejectedCount = 0;                   // 반려 요청 수

        private int _checkInUid;                         // 출퇴근 UID

        /** Member Methods **/

        // UID
        public void SetUid(int uid) => currentUid = uid;
        public int GetUid() => currentUid;

        // 팀 코드 (UID)
        public void SetTeamCode(int code) => currentTeamCode = code;
        public int GetTeamCode() => currentTeamCode;

        // 팀 이름
        public void SetTeamName(string name) => currentTeamName = name;
        public string GetTeamName() => currentTeamName;

        // 날짜
        public void SetDate(string date) => currentDate = date;
        public string GetDate() => currentDate;

        // 요청 상태들 (approved, pending, rejected)
        public void SetRequestStatus(int approved, int pending, int rejected)
        {
            approvedCount = approved;
            pendingCount = pending;
            rejectedCount = rejected;
        }

        public (int approved, int pending, int rejected) GetRequestStatus()
        {
            return (approvedCount, pendingCount, rejectedCount);
        }

        public void SetCheckInUid(int uid) => _checkInUid = uid;
        public int GetCheckInUid() => _checkInUid;

    }
}
