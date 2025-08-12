// Services/AttendanceManager.cs
using CommunityToolkit.Mvvm.Messaging;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using ShifterUser.Enums;
using ShifterUser.Helpers;
using ShifterUser.Messages;
using ShifterUser.Models;
using ShifterUser.ViewModels;
using System;
using System.Threading.Tasks;

namespace ShifterUser.Services
{
    public class AttendanceManager
    {
        private readonly SocketManager _socket;
        private readonly UserSession _session;

        public AttendanceManager(SocketManager socket, UserSession session)
        {
            _socket = socket;
            _session = session;
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

            // Services/AttendanceManager.cs
            if (protocol == "ask_check_in" && result == "success")
            {
                _session.SetCheckInUid(checkInUid);

                // 세션 출근 상태 반영
                var now = DateTime.Now;
                var att = _session.GetAttendance() ?? new AttendanceModel();
                att.ClockInTime = att.ClockInTime ?? now;
                att.ClockInStatus = "출근 완료";
                _session.SetAttendance(att);

                // (현재 화면의 VM도 갱신 — 같은 인스턴스면 즉시 반영)
                homeViewModel.AttendanceStatus = AttendanceStatus.출근완료;

                //  메시지 브로드캐스트로 다른 홈 인스턴스도 갱신
                WeakReferenceMessenger.Default.Send(new AttendanceChangedMessage());

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
                // 🔹 세션 퇴근 상태 반영
                var att = _session.GetAttendance() ?? new AttendanceModel();
                att.ClockOutTime = att.ClockOutTime ?? DateTime.Now;
                att.ClockOutStatus = "퇴근 완료";
                _session.SetAttendance(att);

                // 현재 VM도 갱신
                homeVM.AttendanceStatus = AttendanceStatus.퇴근완료;

                // (선택) 브로드캐스트
                WeakReferenceMessenger.Default.Send(new AttendanceChangedMessage());

                return true;
            }

            else
            {
                return false;
            }
        }
        public Task<AttendanceModel?> GetByDateAsync(DateTime date)
        {
            // 요청 JSON
            var req = new JObject
            {
                //attendance_info
                ["protocol"] = "attendance_info",
                ["data"] = new JObject
                {
                    ["staff_uid"] = _session.GetUid(),
                    ["date"] = date.ToString("yyyy-MM-dd")
                }
            };

            var sendItem = new WorkItem
            {
                json = JsonConvert.SerializeObject(req),
                payload = Array.Empty<byte>(),
                path = string.Empty
            };

            // 송신/수신
            _socket.Send(sendItem);
            WorkItem res = _socket.Receive();

            // 응답 파싱
            var root = JObject.Parse(res.json);
            string protocol = root["protocol"]?.ToString() ?? "";
            string result = root["resp"]?.ToString() ?? "";

            if (protocol == "attendance_info" && result == "success")
            {
                var att = root["data"]?["attendance"] as JObject;
                if (att == null) return Task.FromResult<AttendanceModel?>(null);
          
                var cinStr = att["check_in_time"]?.ToString();   
                var coutStr = att["check_out_time"]?.ToString();

                // "yyyy-MM-dd HH:mm[:ss]" / "HH:mm[:ss]" 모두 지원
                static DateTime? ToDateTime(DateTime baseDate, string? value, bool isOut)
                {
                    if (string.IsNullOrWhiteSpace(value)) return null;

                    // 먼저 전체 날짜+시각 시도
                    var fmtsFull = new[] { "yyyy-MM-dd HH:mm:ss", "yyyy-MM-dd HH:mm" };
                    if (DateTime.TryParseExact(value.Trim(), fmtsFull,
                        System.Globalization.CultureInfo.InvariantCulture,
                        System.Globalization.DateTimeStyles.None, out var dtFull))
                    {
                        return dtFull;
                    }

                    // 시간만 온 경우(HH:mm or HH:mm:ss)
                    var fmtsTime = new[] { "HH:mm:ss", "HH:mm" };
                    if (DateTime.TryParseExact(value.Trim(), fmtsTime,
                        System.Globalization.CultureInfo.InvariantCulture,
                        System.Globalization.DateTimeStyles.None, out var tOnly))
                    {
                        // 퇴근이 새벽이면 +1일
                        var date = baseDate;
                        if (isOut && tOnly.TimeOfDay < TimeSpan.FromHours(6))
                            date = date.AddDays(1);

                        return date.Date + tOnly.TimeOfDay;
                    }

                    // 마지막으로 일반 파서
                    if (DateTime.TryParse(value, out var any))
                        return any;

                    return null;
                }

                var model = new AttendanceModel
                {
                    ClockInTime = ToDateTime(date, cinStr, isOut: false),
                    ClockOutTime = ToDateTime(date, coutStr, isOut: true),
                    ClockInStatus = null,
                    ClockOutStatus = null
                };

                return Task.FromResult<AttendanceModel?>(model);
            }

            // 프로토콜/결과 불일치
            return Task.FromResult<AttendanceModel?>(null);
        }
    }
}
