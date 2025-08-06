using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ShifterUser.Services;
using ShifterUser.Helpers;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace ShifterUser.Models
{
    public class UserManager
    {
        // Meber Variables
        private readonly SocketManager _socket;
        private readonly UserSession _session;

        // 생성자
        public UserManager(SocketManager socket, UserSession session)
        {
            Console.WriteLine("[UserManager] UserManager 인스턴스가 생성되었습니다.");
            _socket = socket;
            _session = session;
        }
        // 사용자 정보
        // 근무표 정보

        // 로그인
        public bool LogIn(string id, string password)
        {

            /* [1] new json */
            JObject jsonData = new()
            {
                { "protocol", "login" },
                {
                    "data", new JObject
                    {
                        { "id", id },
                        { "pw", password }
                    }
                }
            };

            var sendItem = new WorkItem
            {
                json = JsonConvert.SerializeObject(jsonData),
                payload = [],
                path = ""
            };

            _socket.Send(sendItem);

            WorkItem response = _socket.Receive();

            jsonData = JObject.Parse(response.json);
            string protocol = jsonData["protocol"]?.ToString() ?? "";
            string result = jsonData["resp"]?.ToString() ?? "";

            if (protocol == "login" && result == "success")
            {
                Console.WriteLine("Success Communication with Server");

                var data = jsonData["data"];
                int staffUid = data?["staff_uid"]?.ToObject<int>() ?? -1;
                int teamUid = data?["team_uid"]?.ToObject<int>() ?? -1;
                string teamName = data?["team_name"]?.ToString() ?? "";
                string date = data?["date"]?.ToString() ?? "";

                var status = data?["work_request_status"];
                int approved = status?["approved"]?.ToObject<int>() ?? 0;
                int pending = status?["pending"]?.ToObject<int>() ?? 0;
                int rejected = status?["rejected"]?.ToObject<int>() ?? 0;

                // UserSession에 정보 저장
                _session.SetUid(staffUid);
                _session.SetTeamCode(teamUid);
                _session.SetTeamName(teamName);
                _session.SetDate(date);
                _session.SetRequestStatus(approved, pending, rejected);

                Console.WriteLine($"로그인 정보 저장 완료: UID={staffUid}, 팀={teamName}({teamUid}), 날짜={date}");
                Console.WriteLine($"요청 현황 - 승인:{approved}, 대기:{pending}, 반려:{rejected}");

                return true;
            }

            else if (protocol == "login" && result == "fail")
            {
                return false;
            }
            else
            {
                Console.WriteLine($"[UserManager] 로그인 응답 오류: {result}");
                return false;
            }
        }

        // 출근
        public bool AskCheckIn()
        {
            JObject jsonData = new()
            {
                { "protocol", "ask_check_in" },
                {
                    "data", new JObject
                    {
                        {"staff_uid", _session.GetUid() },
                        {"team_uid", _session.GetTeamCode() }
                    }
                }
            };

            WorkItem sendItem = new()
            {
                json = JsonConvert.SerializeObject(jsonData),
                payload = [],
                path = ""
            };

            _socket.Send(sendItem);

            WorkItem response = _socket.Receive();
            JObject respJson = JObject.Parse(response.json);

            string protocol = respJson["protocol"]?.ToString() ?? "";
            string result = respJson["resp"]?.ToString() ?? "";
            int checkInUid = respJson["data"]?["check_in_uid"]?.Value<int>() ?? -1;

            //  응답 검증
            if (protocol == "ask_check_in" && result == "success")
            {
                // UID 저장
                _session.SetCheckInUid(checkInUid);
                return true;

            }
            else
            {   
                return false;
            }
        }
    }
}
