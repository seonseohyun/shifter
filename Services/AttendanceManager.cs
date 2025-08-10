// Services/AttendanceManager.cs
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using ShifterUser.Helpers;
using ShifterUser.Models;
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

                // "HH:mm" -> DateTime? (기본은 같은 날짜, 퇴근이 새벽이면 +1일 보정)
                static DateTime? ToDateTime(DateTime baseDate, string? hhmm, bool isOut)
                {
                    if (string.IsNullOrWhiteSpace(hhmm)) return null;

                    var d = baseDate;
                    if (isOut && TimeSpan.TryParse(hhmm, out var t) && t < TimeSpan.FromHours(6))
                        d = d.AddDays(1);

                    return DateTime.TryParse($"{d:yyyy-MM-dd} {hhmm}", out var dt)
                        ? dt : (DateTime?)null;
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
