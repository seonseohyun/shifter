using CommunityToolkit.Mvvm.ComponentModel;
using Newtonsoft.Json.Linq;
using ShifterUser.Enums;
using ShifterUser.Helpers;
using ShifterUser.Services;
using System;
using System.Net.Sockets;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using System.Web;
using static System.Runtime.InteropServices.JavaScript.JSType;

namespace ShifterUser.Models
{
    public partial class WorkRequestManager : ObservableObject
    {
        private readonly SocketManager _socket;
        private readonly UserSession _session;

        public WorkRequestManager(SocketManager socket, UserSession session)
        {
            Console.WriteLine("[WorkRequestManager] 인스턴스 생성됨");
            _socket = socket;
            _session = session;
        }

        public static class EnumHelper
        {
            public static ShiftType ParseShiftType(string value)
            {
                return value.ToLower() switch
                {
                    "day" => ShiftType.Day,
                    "night" => ShiftType.Night,
                    "evening" => ShiftType.Evening,
                    "off" => ShiftType.Off,
                    "d" => ShiftType.Day,
                    "n" => ShiftType.Night,
                    "e" => ShiftType.Evening,
                    "o" => ShiftType.Off,
                    _ => throw new ArgumentException($"Unknown shift type: {value}")
                };
            }

            public static WorkRequestStatus ParseWorkRequestStatus(string value)
            {
                return value.ToLower() switch
                {
                    "approved" => WorkRequestStatus.Approved,
                    "pending" => WorkRequestStatus.Pending,
                    "rejected" => WorkRequestStatus.Rejected,
                };
            }
        }

        // ▶ 날짜
        [ObservableProperty] private DateTime date;

        // ▶ 근무 스케줄 정보
        [ObservableProperty] private ConfirmedWorkScheModel? schedule;

        // ▶ 출퇴근 기록
        [ObservableProperty] private AttendanceModel? attendance;

        // ▶ 희망 근무 요청 여부 및 사유
        [ObservableProperty] private bool isRequested;
        [ObservableProperty] private string? requestReason;

        /// <summary>
        /// 서버로부터 특정 날짜의 근무 정보 로드
        /// </summary>
        public async Task LoadFromServerAsync(int uid, DateTime targetDate)
        {
            Date = targetDate;

            JObject requestJson = new()
            {
                ["PROTOCOL"] = "GET_DAY_WORK_INFO",
                ["UID"] = uid,
                ["DATE"] = targetDate.ToString("yyyy-MM-dd")
            };

            WorkItem sendItem = new()
            {
                json = requestJson.ToString(),
                payload = [],
                path = ""
            };

            _socket.Send(sendItem);
            WorkItem response = _socket.Receive();

            JObject res = JObject.Parse(response.json);
            string protocol = res["PROTOCOL"]?.ToString() ?? "";
            string resp = res["RESP"]?.ToString() ?? "FAIL";

            if (protocol == "GET_DAY_WORK_INFO" && resp == "SUCCESS")
            {
                Schedule = res["SCHEDULE"]?.ToObject<ConfirmedWorkScheModel>();
                Attendance = res["ATTENDANCE"]?.ToObject<AttendanceModel>();
                IsRequested = res["IS_REQUESTED"]?.ToObject<bool>() ?? false;
                RequestReason = res["REQUEST_REASON"]?.ToString();

                Console.WriteLine($"[WorkRequestManager] {Date:yyyy-MM-dd} 데이터 로드 성공");
            }
            else
            {
                Schedule = null;
                Attendance = null;
                IsRequested = false;
                RequestReason = null;

                Console.WriteLine($"[WorkRequestManager] {Date:yyyy-MM-dd} 데이터 로드 실패");
            }
        }

        // 진또배기 
        public async Task<List<WorkRequestModel>> LoadMonthRequestsAsync(int uid, int year, int month)
        {
            JObject requestJson = new()
            {
                ["protocol"] = "shift_change_detail",
                ["data"] = new JObject
                {
                    ["staff_uid"] = _session.GetUid(),
                    ["req_year"] = year.ToString(),
                    ["req_month"] = month.ToString()
                },
            };

            WorkItem sendItem = new()
            {
                json = requestJson.ToString(),
                payload = [],
                path = ""
            };

            _socket.Send(sendItem);
            WorkItem response = _socket.Receive();

            JObject res = JObject.Parse(response.json);
            string protocol = res["protocol"]?.ToString() ?? "";
            string result = res["resp"]?.ToString() ?? "";

            if (protocol == "shift_change_detail" && result == "success")
            {
                JArray? dataArray = res["data"]?.ToObject<JArray>();

                if (dataArray != null)
                {
                    List<WorkRequestModel> list = new();

                    foreach (var item in dataArray)
                    {
                        string dateStr = item["request_date"]?.ToString() ?? "";
                        string shiftStr = item["desire_shift"]?.ToString() ?? "";
                        string statusStr = item["status"]?.ToString() ?? "";
                        string reason = item["reason"]?.ToString() ?? "";
                        string adminMsg = item["admin_msg"]?.ToString() ?? "";

                        if (DateTime.TryParse(dateStr, out DateTime date))
                        {
                            list.Add(new WorkRequestModel
                            {
                                RequestDate = date,
                                ShiftType = EnumHelper.ParseShiftType(shiftStr),
                                Status = EnumHelper.ParseWorkRequestStatus(statusStr),
                                Reason = reason,
                                RejectionReason = adminMsg
                            });
                        }
                    }

                    Console.WriteLine($"[WorkRequestManager] {year}-{month} 근무 요청 {list.Count}건 수신됨");
                    return list;
                }
            }

            Console.WriteLine($"[WorkRequestManager] {year}-{month} 근무 요청 불러오기 실패");
            return new();
        }

        public bool SendRequest(DateTime date, ShiftType shiftType, string reason)
        {
            string shiftCode = shiftType switch
            {
                ShiftType.Day => "D",
                ShiftType.Night => "N",
                ShiftType.Evening => "E",
                ShiftType.Off => "O",
                _ => "?"
            };

            JObject requestJson = new()
            {
                ["protocol"] = "ask_shift_change",
                ["data"] = new JObject
                {
                    ["staff_uid"] = _session.GetUid(),
                    ["date"] = date.ToString("yyyy-MM-dd"),
                    ["duty_type"] = shiftCode,
                    ["message"] = reason
                }
            };

            WorkItem sendItem = new()
            {
                json = requestJson.ToString(),
                payload = [],
                path = ""
            };

            _socket.Send(sendItem);
            WorkItem response = _socket.Receive();

            JObject res = JObject.Parse(response.json);
            string protocol = res["protocol"]?.ToString() ?? "";
            string result = res["resp"]?.ToString() ?? "fail";

            if (protocol == "ask_shift_change" && result == "success")
            {
                Console.WriteLine($"[WorkRequestManager] {date:yyyy-MM-dd} 요청 성공");
                return true;
            }
            else
            {
                string error = res["error"]?.ToString() ?? "알 수 없는 오류";
                Console.WriteLine($"[WorkRequestManager] 요청 실패 - {error}");
                return false;
            }
        }
    }
}
