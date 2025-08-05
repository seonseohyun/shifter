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
                    "evening" => ShiftType.Evening,
                    "night" => ShiftType.Night,
                    "off" => ShiftType.Off,
                    
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



        //public async Task<List<WorkRequestModel>> LoadMonthRequestsAsync(int uid, int year, int month)
        //{
        //    try
        //    {
        //        JObject requestJson = new()
        //        {
        //            ["protocol"] = "shift_change_detail",
        //            ["data"] = new JObject
        //            {
        //                ["staff_uid"] = uid,
        //                ["req_year"] = year,
        //                ["req_month"] = month
        //            },
        //            ["resp"] = "",
        //            ["message"] = ""
        //        };

        //        WorkItem sendItem = new()
        //        {
        //            json = requestJson.ToString(),
        //            payload = [],
        //            path = ""
        //        };

        //        _socket.Send(sendItem);

        //        WorkItem response = _socket.Receive();

        //        JObject res = JObject.Parse(response.json);
        //        string protocol = res["protocol"]?.ToString() ?? "";

        //        if (protocol == "shift_change_detail")
        //        {
        //            Console.WriteLine("들어옴!!!");
        //            //return res["REQUESTS"]?.ToObject<List<WorkRequestModel>>() ?? new();
        //        }

        //        Console.WriteLine("[WorkRequestManager] 응답 실패. 임시 데이터로 대체함.");
        //        return GetDummyData(year, month);
        //    }
        //    catch (Exception ex)
        //    {
        //        Console.WriteLine("[WorkRequestManager] 서버 응답 실패. 예외 발생. 임시 데이터로 대체함.");
        //        Console.WriteLine(ex.Message);
        //        return GetDummyData(year, month);
        //    }
        //}

        //    private List<WorkRequestModel> GetDummyData(int year, int month)
        //    {
        //        return new List<WorkRequestModel>
        //{
        //    new WorkRequestModel
        //    {
        //        RequestDate = new DateTime(year, month == 0 ? 1 : month, 1),
        //        ShiftType = ShiftType.Day,
        //        Status = WorkRequestStatus.Approved,
        //        Reason = "결혼식 참석"
        //    },
        //    new WorkRequestModel
        //    {
        //        RequestDate = new DateTime(year, month == 0 ? 1 : month, 4),
        //        ShiftType = ShiftType.Off,
        //        Status = WorkRequestStatus.Rejected,
        //        Reason = "가족 여행",
        //        RejectionReason = "인력 부족"
        //    },
        //    new WorkRequestModel
        //    {
        //        RequestDate = new DateTime(year, month == 0 ? 1 : month, 7),
        //        ShiftType = ShiftType.Evening,
        //        Status = WorkRequestStatus.Pending,
        //        Reason = "학원 수업"
        //    }
        //};
        //    }

        //public async Task<List<WorkRequestModel>> LoadMonthRequestsAsync(int uid, int year, int month)
        //{
        //    try
        //    {
        //        JObject requestJson = new()
        //        {
        //            ["PROTOCOL"] = "GET_MONTH_REQUESTS",
        //            ["UID"] = uid,
        //            ["YEAR"] = year,
        //            ["MONTH"] = month
        //        };

        //        WorkItem sendItem = new()
        //        {
        //            json = requestJson.ToString(),
        //            payload = [],
        //            path = ""
        //        };

        //        _socket.Send(sendItem);
        //        WorkItem response = _socket.Receive();

        //        JObject res = JObject.Parse(response.json);
        //        string protocol = res["PROTOCOL"]?.ToString() ?? "";
        //        string resp = res["RESP"]?.ToString() ?? "FAIL";

        //        if (protocol == "GET_MONTH_REQUESTS" && resp == "SUCCESS")
        //        {
        //            return res["REQUESTS"]?.ToObject<List<WorkRequestModel>>() ?? new();
        //        }

        //        Console.WriteLine("[WorkRequestManager] 응답은 왔지만 실패 처리됨");
        //        return new(); // 빈 리스트 반환
        //    }
        //    catch (Exception ex)
        //    {
        //        Console.WriteLine("[WorkRequestManager] 서버 응답 실패. 임시 데이터로 대체함.");
        //        Console.WriteLine(ex.Message);

        //        // 임시 Mock 데이터 반환
        //        return new List<WorkRequestModel>
        //{
        //    new()
        //    {
        //        RequestDate = new DateTime(year, month == 0 ? 1 : month, 1),
        //        ShiftType = ShiftType.Day,
        //        Status = WorkRequestStatus.Approved,
        //        Reason = "결혼식 참석"
        //    },
        //    new()
        //    {
        //        RequestDate = new DateTime(year, month == 0 ? 1 : month, 4),
        //        ShiftType = ShiftType.Off,
        //        Status = WorkRequestStatus.Rejected,
        //        Reason = "가족 여행",
        //        RejectionReason = "인력 부족"
        //    },
        //    new()
        //    {
        //        RequestDate = new DateTime(year, month == 0 ? 1 : month, 7),
        //        ShiftType = ShiftType.Evening,
        //        Status = WorkRequestStatus.Pending,
        //        Reason = "학원 수업"
        //    }
        //};
        //    }
        //}


    }
}
