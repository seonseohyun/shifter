using System;
using System.Collections.Generic;

namespace ShifterUser.Models
{
    public class UserSession
    {
        /** Member Variables **/
        public Stack<string> NavigationHistory { get; set; } = new Stack<string>(); // 페이지 이동 기록 스택

        private string currentUid = string.Empty;       // 현재 로그인한 사용자 UID
        private string currentTeamCode = string.Empty;  // 소속 팀 코드
        private string currentUserName = string.Empty;  // 사용자 이름

        /** Member Methods **/

        // UID
        public void SetUid(string uid) => currentUid = uid;
        public string GetUid() => currentUid;

        // 팀 코드
        public void SetTeamCode(string code) => currentTeamCode = code;
        public string GetTeamCode() => currentTeamCode;

        // 사용자 이름
        public void SetUserName(string name) => currentUserName = name;
        public string GetUserName() => currentUserName;
    }
}
