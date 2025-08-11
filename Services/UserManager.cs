using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using ShifterUser.Enums;
using ShifterUser.Helpers;
using ShifterUser.Models;
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
        private string? _serverPwPlain;         // 서버에서 내려온 현재 비밀번호

        // 생성자
        public UserManager(SocketManager socket, UserSession session)
        {
            Console.WriteLine("[UserManager] UserManager 인스턴스가 생성되었습니다.");
            _socket = socket;
            _session = session;
        }

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
                var data = jsonData["data"];
                int staffUid = data?["staff_uid"]?.ToObject<int>() ?? -1;
                string staffName = data?["staff_name"]?.ToString() ?? "";
                int teamUid = data?["team_uid"]?.ToObject<int>() ?? -1;
                string teamName = data?["team_name"]?.ToString() ?? "";
                string date = data?["date"]?.ToString() ?? "";

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


        public async Task<string[]> GetWeeklyShiftCodesAsync(DateTime monday)
        {
            var result = new string[7] { "-", "-", "-", "-", "-", "-", "-" };

            var req = new JObject
            {
                ["protocol"] = "ask_timetable_weekly",
                ["data"] = new JObject
                {
                    ["date"] = monday.ToString("yyyy-MM-dd"),
                    ["staff_uid"] = _session.GetUid()
                }
            };

            var sendItem = new WorkItem
            {
                json = JsonConvert.SerializeObject(req),
                payload = Array.Empty<byte>(),
                path = ""
            };

            _socket.Send(sendItem);

            WorkItem resItem = _socket.Receive();
            if (!string.IsNullOrEmpty(resItem.json))
            {
                var res = JObject.Parse(resItem.json);
                var arr = res?["data"]?["shift_type"] as JArray;
                if (arr != null)
                {
                    for (int i = 0; i < Math.Min(7, arr.Count); i++)
                    {
                        var raw = arr[i]?.ToString();
                        result[i] = string.IsNullOrWhiteSpace(raw) ? "-" : raw.Trim().ToUpperInvariant();
                    }
                }
            }

            return result;
        }

        public async Task<UserInfoModel?> GetUserInfoAsync()
        {
            var req = new JObject
            {
                ["protocol"] = "ask_user_info",
                ["data"] = new JObject
                {
                    ["team_uid"] = _session.GetTeamCode(),
                    ["staff_uid"] = _session.GetUid()
                }
            };

            var send = new WorkItem { json = JsonConvert.SerializeObject(req), payload = Array.Empty<byte>(), path = "" };
            _socket.Send(send);

            var resItem = _socket.Receive();
            if (string.IsNullOrWhiteSpace(resItem.json)) return null;

            var json = JObject.Parse(resItem.json);
            if (json["protocol"]?.ToString() != "ask_user_info" || json["resp"]?.ToString() != "success") return null;

            var data = json["data"];
            var pwRaw = data?["pw"]?.ToString() ?? "";

            // 평문 PW 보관 (클라 비교용)
            _serverPwPlain = string.IsNullOrWhiteSpace(pwRaw) ? null : pwRaw;

            return new UserInfoModel
            {
                Id = data?["id"]?.ToString() ?? "",
                PhoneNumber = data?["phone_number"]?.ToString() ?? "",
                CompanyName = data?["company_name"]?.ToString() ?? "",
                GradeName = data?["grade_name"]?.ToString() ?? "",
                HasPassword = !string.IsNullOrWhiteSpace(pwRaw)
            };
        }

        // 현재 비밀번호 로컬 비교 (평문 문자열 비교)
        public bool VerifyCurrentPassword(string currentPw)
            => _serverPwPlain is not null &&
               string.Equals(_serverPwPlain, currentPw, StringComparison.Ordinal);

        // 비밀번호 변경 호출 (스펙상 current_pw 없이 pw만 전송)
        public async Task<(bool ok, string? message)> ModifyPasswordAsync(string newPw)
        {
            var req = new JObject
            {
                ["protocol"] = "modify_user_info",
                ["data"] = new JObject
                {
                    ["staff_uid"] = _session.GetUid(),
                    ["pw"] = newPw
                }
            };

            var send = new WorkItem { json = JsonConvert.SerializeObject(req), payload = Array.Empty<byte>(), path = "" };
            _socket.Send(send);

            var resItem = _socket.Receive();
            if (string.IsNullOrWhiteSpace(resItem.json)) return (false, "서버 응답 없음");

            var json = JObject.Parse(resItem.json);
            if (json["protocol"]?.ToString() != "modify_user_info") return (false, "프로토콜 불일치");

            var resp = json["resp"]?.ToString();
            var msg = json["messege"]?.ToString() ?? json["message"]?.ToString(); // 철자 케이스 대비
            return (resp == "success", msg);
        }

    }

    public class UserInfoModel
    {
        public string Id { get; init; } = "";
        public string PhoneNumber { get; init; } = "";
        public string CompanyName { get; init; } = "";
        public string GradeName { get; init; } = "";
        public bool HasPassword { get; init; }
    }
}

