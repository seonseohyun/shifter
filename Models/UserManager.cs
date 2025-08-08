using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using ShifterUser.Enums;
using ShifterUser.Helpers;
using ShifterUser.Services;
using ShifterUser.ViewModels;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

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
                string staffName = data?["staff_name"]?.ToString() ?? "";
                int teamUid = data?["team_uid"]?.ToObject<int>() ?? -1;
                string teamName = data?["team_name"]?.ToString() ?? "";
                string date = data?["date"]?.ToString() ?? "";

                Console.WriteLine($"$$$$$$$$$$$$${staffName}");

                var status = data?["work_request_status"];
                int approved = status?["approved"]?.ToObject<int>() ?? 0;
                int pending = status?["pending"]?.ToObject<int>() ?? 0;
                int rejected = status?["rejected"]?.ToObject<int>() ?? 0;

                var attendance = data?["attendance"];
                if (attendance != null)
                {
                    string att_status = attendance["status"]?.ToString() ?? "";
                    string? checkInStr = attendance["check_in_time"]?.ToString();
                    string? checkOutStr = attendance["check_out_time"]?.ToString();

                    DateTime? checkIn = null;
                    DateTime? checkOut = null;

                    if (DateTime.TryParse(checkInStr, out DateTime inTime))
                        checkIn = inTime;

                    if (DateTime.TryParse(checkOutStr, out DateTime outTime))
                        checkOut = outTime;

                    AttendanceModel model = new()
                    {
                        ClockInTime = checkIn,
                        ClockInStatus = att_status == "출근" ? "출근 완료" : null,
                        ClockOutTime = checkOut,
                        ClockOutStatus = (att_status == "퇴근" || checkOut != null) ? "퇴근 완료" : null,
                    };

                    _session.SetAttendance(model);
                }


                // UserSession에 정보 저장
                _session.SetName(staffName);
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
        public bool AskCheckIn(HomeViewModel homeViewModel)
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

            if (protocol == "ask_check_in" && result == "success")
            {
                // 상태 반영!
                _session.SetCheckInUid(checkInUid);
                // HomeViewModel 상태 갱신
                homeViewModel.AttendanceStatus = AttendanceStatus.출근완료;

                return true;
            }

            return false;
        }



        public bool AskCheckOut(HomeViewModel homeVM)
        {
            JObject jsonData = new()
            {
                { "protocol", "ask_check_out" },
                {
                    "data", new JObject
                    {
                        { "check_in_uid", _session.GetCheckInUid() }
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
            string message = respJson["message"]?.ToString() ?? "";

            if (protocol == "ask_check_out" && result == "success")
            {
                //  상태 반영
                homeVM.UpdateAttendanceStatusFromMessage(message);
                // HomeViewModel 상태 갱신
                homeVM.AttendanceStatus = AttendanceStatus.퇴근완료;
                return true;
            }
            else
            {
                return false;
            }
        }


    }
}


