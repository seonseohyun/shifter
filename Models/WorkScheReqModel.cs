using CommunityToolkit.Mvvm.ComponentModel;
using Newtonsoft.Json.Linq;
using ShifterUser.Helpers;
using ShifterUser.Services;
using System;
using System.Net.Sockets;
using System.Threading.Tasks;
using static System.Runtime.InteropServices.JavaScript.JSType;

namespace ShifterUser.Models
{
    public partial class WorkScheReqModel : ObservableObject
    {
        private readonly SocketManager _socket;
        private readonly UserSession _session;

        public WorkScheReqModel(SocketManager socket, UserSession session)
        {
            Console.WriteLine("[WorkScheReqModel] 인스턴스 생성됨");
            _socket = socket;
            _session = session;
        }

        // ▶ 날짜
        [ObservableProperty] private DateTime date;

        // ▶ 근무 스케줄 정보
        [ObservableProperty] private WorkScheduleModel? schedule;

        // ▶ 출퇴근 기록
        [ObservableProperty] private AttendanceModel? attendance;

        // ▶ 희망 근무 요청 여부 및 사유
        [ObservableProperty] private bool isRequested;
        [ObservableProperty] private string? requestReason;

        /// <summary>
        /// 서버로부터 특정 날짜의 근무 정보 로드
        /// </summary>
        public async Task LoadFromServerAsync(string uid, DateTime targetDate)
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
                Schedule = res["SCHEDULE"]?.ToObject<WorkScheduleModel>();
                Attendance = res["ATTENDANCE"]?.ToObject<AttendanceModel>();
                IsRequested = res["IS_REQUESTED"]?.ToObject<bool>() ?? false;
                RequestReason = res["REQUEST_REASON"]?.ToString();

                Console.WriteLine($"[WorkScheReqModel] {Date:yyyy-MM-dd} 데이터 로드 성공");
            }
            else
            {
                Schedule = null;
                Attendance = null;
                IsRequested = false;
                RequestReason = null;

                Console.WriteLine($"[WorkScheReqModel] {Date:yyyy-MM-dd} 데이터 로드 실패");
            }
        }
    }
}
