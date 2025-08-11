using CommunityToolkit.Mvvm.ComponentModel;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Shifter.Services;
using Shifter.Structs;
using Shifter.ViewModels;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel.Design.Serialization;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using static OpenCvSharp.Stitcher;
using static System.Runtime.InteropServices.JavaScript.JSType;

namespace Shifter.Models {
    public partial class ScdModel {

        /* Constructor*/
        public ScdModel(Session? session, SocketManager? socket) {
            _session = session!;
            _socket = socket!;
        }


        /** Member Variables **/
        readonly Session? _session;
        readonly SocketManager? _socket;
        readonly ObservableCollection<ShiftItem>? _shifts = [];
        readonly ObservableCollection<TodaysDutyInfo>? _todaysDuty = [];


        /** Member Method **/

        public ObservableCollection<ShiftItem> GetShifts() {
            return _shifts!;
        }

        public ObservableCollection<TodaysDutyInfo> GetTodaysDuty() {
            return _todaysDuty!;
        }

        public partial class ShiftChangeRequestInfo : ObservableObject
        {
            [ObservableProperty] public int dutyRequestUid;
            [ObservableProperty] public int staffUid = 0;
            [ObservableProperty] public string staffName = "";
            [ObservableProperty] public DateTime requestDate;
            [ObservableProperty] public string desireShift = "";
            [ObservableProperty] public string reason = "";

            // 서버가 주는 값: "approved" | "rejected" | "pending"
            [ObservableProperty] public string status = "";

            // UI 제어용 파생 속성
            public bool CanAct => string.Equals(Status, "pending", StringComparison.OrdinalIgnoreCase);
            public string StatusKo => Status switch
            {
                "approved" => "이미 승인됨",
                "rejected" => "이미 반려됨",
                "pending" => "대기중",
                _ => ""
            };
        }



        public async Task<ObservableCollection<ShiftChangeRequestInfo>> ShiftChangeList(int _currentYear, int _currentMonth)
        {
            
            JObject jsonData = new JObject {
                { "protocol", "shift_change_list" },
                { "data", new JObject {
                    //{ "team_uid", _session.GetCurrentTeamId() },
                        {"team_uid" , 1},
                        { "req_year", _currentYear.ToString() },
                        { "req_month", _currentMonth.ToString() },
                    }
                }
            };

            WorkItem sendItem = new()
            {
                json = JsonConvert.SerializeObject(jsonData),
                payload = [],
                path = ""
            };

            await _socket.SendAsync(sendItem);


            WorkItem recvItem = await _socket.ReceiveAsync();
            JObject recvJson = JObject.Parse(recvItem.json);
            byte[] payload = recvItem.payload;
            string path = recvItem.path;

            var result = new ObservableCollection<ShiftChangeRequestInfo>();

            if (recvJson["resp"]!.ToString() == "success")
            {
                var dataArray = recvJson["data"] as JArray;
                if (dataArray != null)
                {
                    foreach (var item in dataArray)
                    {
                        result.Add(new ShiftChangeRequestInfo
                        {
                            DutyRequestUid = item.Value<int>("duty_request_uid"),
                            StaffUid = item.Value<int>("staff_uid"),
                            RequestDate = item.Value<DateTime>("request_date"),
                            StaffName = item.Value<string>("staff_name") ?? string.Empty,
                            DesireShift = item.Value<string>("desire_shift") ?? string.Empty,
                            Reason = item.Value<string>("reason") ?? string.Empty,
                            Status = item.Value<string>("status") ?? ""  
                        });

                    }

                }

            }
            return result;
         }

        public async Task<(bool ok, string? message)> AnswerShiftChangeAsync(
            int dutyRequestUid, string status, DateTime date, string dutyType, string adminMsg)
        {
            try
            {
                var data = new JObject
                {
                    ["duty_request_uid"] = dutyRequestUid,
                    ["status"] = status,
                    ["date"] = date.ToString("yyyy-MM-dd"),
                    ["duty_type"] = dutyType,
                    ["admin_msg"] = adminMsg ?? ""
                };

                var req = new JObject
                {
                    ["protocol"] = "answer_shift_change",
                    ["data"] = data
                };

                var sendItem = new WorkItem
                {
                    json = JsonConvert.SerializeObject(req),
                    payload = Array.Empty<byte>(),
                    path = ""
                };

                await _socket!.SendAsync(sendItem);

                // 한 번만 받기
                var resItem = await _socket.ReceiveAsync();
                if (string.IsNullOrWhiteSpace(resItem.json))
                    return (false, "empty response");

                var jo = JObject.Parse(resItem.json);
                var protocol = (string?)jo["protocol"];
                var resp = (string?)jo["resp"];
                var message = (string?)jo["message"];

                if (protocol == "answer_shift_change" && resp =="success")
                {
                    return (true, message);
                }

                // 실패 케이스
                return (false, message ?? "request failed");
            }
            catch (Exception ex)
            {
                return (false, ex.Message);
            }
        }

        public async Task<ObservableCollection<StaffSchedule>> GenTimeTableAsync(int? year, int? month) {
            int admin_uid = _session!.GetCurrentAdminId();
            int team_uid = _session!.GetCurrentTeamId();

            /* [1] new json */
            JObject sendJson = new JObject {
            { "protocol", "gen_timeTable" },
            { "data", new JObject {
                { "admin_uid", admin_uid },
                { "team_uid",  team_uid },
                { "req_year",  year.ToString() },
                { "req_month", month.ToString() }
                }
                }
            };

            /* [2] Put json in WorkItem */
            WorkItem sendItem = new WorkItem
            {
                json = JsonConvert.SerializeObject(sendJson),
                payload = [],
                path = ""
            };

            /* [3] Send the created WorkItem */
            await _socket!.SendAsync(sendItem);

            /* [4] Create WorkItem response & receive data from the socket. */
            WorkItem recvItem = await _socket.ReceiveAsync();


            JObject recvJson = JObject.Parse(recvItem.json);
            byte[] payload = recvItem.payload;
            string path = recvItem.path;

            /* [5] Parse the data. */
            string protocol = recvJson["protocol"]!.ToString();
            string resp = recvJson["resp"]!.ToString();

            if (protocol == "gen_timeTable" && resp == "success") {
                // 성공적으로 테이블 생성됨
                Console.WriteLine("TimeTable generated successfully for {0}-{1}.", year, month);

                var result = new ObservableCollection<StaffSchedule>();
                var byId = new Dictionary<int, StaffSchedule>();
                int daysInMonth = DateTime.DaysInMonth(year!.Value, month!.Value);

                JToken dataTok = recvJson["data"]!;
                var items = dataTok is JArray arr ? arr
                          : dataTok["schedules"] is JArray arr2 ? arr2
                          : new JArray();

                foreach (var item in items) {
                    var dateStr = (string)item["date"]!;
                    var shift = (string)item["shift"]!;
                    int day = DateTime.Parse(dateStr).Day;

                    foreach (var p in (JArray)item["people"]!) {
                        int staffId = (int)p["staff_id"]!;
                        string name = (string)p["name"]!;

                        if (!byId.TryGetValue(staffId, out var staff)) {
                            staff = new StaffSchedule { StaffId = staffId, Name = name };
                            for (int d = 1; d <= daysInMonth; d++)
                                staff.DailyShifts.Add(new ScheduleCell { Day = d });
                            byId[staffId] = staff;
                            result.Add(staff);
                        }
                        staff.DailyShifts[day - 1].ShiftCode = shift; // "D/E/N/O"
                    }
                }
                return result;
            }
            else {
                // 실패 처리
                Console.WriteLine("Failed to generate TimeTable: {0}", recvJson["message"]!.ToString());
                return [];
            }
        }


        /* Protocol - check_today_duty */
        public async Task<List<TodaysDutyInfo>> CheckTodayDutyAsync() {
            Console.WriteLine("[ScdModel] Executed CheckTodayDutyAsync()");

            /* [1] new json */
            JObject sendJson = new JObject {
                { "protocol", "check_today_duty" },
                { "data", new JObject {
                    { "date", DateTime.Now.Date.ToString()[..10] },
                    { "team_uid", _session!.GetCurrentTeamId() }
                }}
            };

            /* [2] Put json in WorkItem */
            WorkItem sendItem = new WorkItem
            {
                json = JsonConvert.SerializeObject(sendJson),
                payload = [],
                path = ""
            };

            /* [3] Send the created WorkItem */
            await _socket!.SendAsync(sendItem);

            /* [4] Create WorkItem response & receive data from the socket. */
            WorkItem recvItem = await _socket.ReceiveAsync();
            JObject recvJson = JObject.Parse(recvItem.json);
            byte[] payload = recvItem.payload;
            string path = recvItem.path;

            /* [5] Parse the data. */
            string protocol = recvJson["protocol"]!.ToString();
            string resp = recvJson["resp"]!.ToString();

            var result = new List<TodaysDutyInfo>();
            if (protocol == "check_today_duty" && resp == "success") {

                if ((string)recvJson["protocol"]! == "check_today_duty" &&
                    (string)recvJson["resp"]! == "success") {
                    foreach (JObject duty in (JArray)recvJson["data"]!) {
                        result.Add(new TodaysDutyInfo
                        {
                            Shift = duty.Value<string>("shift") ?? "",
                            StaffName = duty["staff"]?.ToObject<string[]>() ?? Array.Empty<string>()
                        });
                    }
                }
            }
            return result;
        }


        /* protocol req_shift_info */
        public async Task ReqShiftInfo() {
            Console.WriteLine("[ScdModel] Executed ReqShiftInfo()");

            /* [1] new json */
            JObject sendJson = new JObject {
                { "protocol", "req_shift_info" },
                { "data", new JObject {
                    { "team_uid", _session!.GetCurrentTeamId() }
                }}
            };

            /* [2] Put json in WorkItem */
            WorkItem sendItem = new WorkItem
            {
                json = JsonConvert.SerializeObject(sendJson),
                payload = [],
                path = ""
            };

            /* [3] Send the created WorkItem */
            await _socket!.SendAsync(sendItem);

            /* [4] Create WorkItem response & receive data from the socket. */
            WorkItem recvItem = await _socket.ReceiveAsync();

            /* [5] Parse the data. */
            JObject recvJson = JObject.Parse(recvItem.json);

            string protocol = recvJson["protocol"]!.ToString();
            string resp = recvJson["resp"]!.ToString();
            var data = recvJson["data"]!;

            if (protocol == "req_shift_info" && resp == "success") {
                Console.WriteLine("Shift information requested successfully.");

                _shifts!.Clear(); // Clear existing shifts before adding new ones
                foreach (var shift in data["shift_info"]!) {
                    ShiftItem shiftItem = new ShiftItem()
                    {
                        ShiftType = shift["duty_type"]!.ToString(),
                        StartTime = shift["start_time"]!.ToString(),
                        EndTime = shift["end_time"]!.ToString(),
                        DutyHours = shift["duty_hours"]!.ToObject<int>()
                    };
                    _shifts.Add(shiftItem);
                }
            }
            else {
                // 실패 처리
                Console.WriteLine("Failed to request shift information: {0}", recvJson["message"]!.ToString());

            }
        }

        public async Task AskTimeTableAdminAsync(int year, int month) {
            Console.WriteLine("[ScdModel] Executed AskTimeTableAdminAsync()");

            /* [1] new json */
            JObject sendJson = new JObject {
                { "protocol", "ask_timetable_admin" },
                { "data", new JObject {
                    { "req_year", year.ToString() },
                    { "req_month", month.ToString() },
                    { "team_uid", _session!.GetCurrentTeamId() }
                }}
            };

            /* [2] Put json in WorkItem */
            WorkItem sendItem = new WorkItem
            {
                json = JsonConvert.SerializeObject(sendJson),
                payload = [],
                path = ""
            };

            /* [3] Send the created WorkItem */
            await _socket!.SendAsync(sendItem);

            /* [4] Create WorkItem response & receive data from the socket. */
            WorkItem recvItem = await _socket.ReceiveAsync();
            JObject recvJson = JObject.Parse(recvItem.json);
            byte[] payload = recvItem.payload;
            string path = recvItem.path;

            /* [5] Parse the data. */
            string protocol = recvJson["protocol"]!.ToString();
            string resp = recvJson["resp"]!.ToString();

            if (protocol == "ask_timetable_admin" && resp == "success") {

            }
            else {
                // 실패 처리
                Console.WriteLine("Failed to request TimeTable: {0}", recvJson["message"]!.ToString());
            }
        }
    }


    /*** Today's Duty Info ***/
    public partial class TodaysDutyInfo : ObservableObject {
        [ObservableProperty] private string? shift;          // 근무조
        [ObservableProperty] private string[]? staffName;     // 직원명
    }


    /*** Class Staff Schedule ***/
    public partial class StaffSchedule : ObservableObject {

        /** Constructor **/
        public StaffSchedule() {
            DailyShifts.CollectionChanged += (s, e) => {
                if (e.NewItems != null)
                    foreach (ScheduleCell cell in e.NewItems)
                        cell.ShiftCodeChanged += OnCellShiftChanged;
                if (e.OldItems != null)
                    foreach (ScheduleCell cell in e.OldItems)
                        cell.ShiftCodeChanged -= OnCellShiftChanged;
            };
        }

        /* Member Variables */
        public string Name { get; set; } = string.Empty;
        public ObservableCollection<ScheduleCell> DailyShifts { get; set; } = new();
        // 동적 통계용 딕셔너리
        public ObservableCollection<KeyValuePair<string, int>> ShiftCodeCounts { get; set; } = new();
        public event EventHandler? ShiftChanged;
        public Action? UpdateDailyStatsCallback { get; set; }


        private void OnCellShiftChanged(object? sender, EventArgs e) {
            UpdateShiftCounts();
            OnPropertyChanged(nameof(TotalWorkingHours));
            OnPropertyChanged(nameof(TotalEmptyDays));
            UpdateDailyStatsCallback?.Invoke(); // ViewModel에 직접 요청
        }


        public void UpdateShiftCounts() {
            // 1. 임시 Dictionary로 그룹핑된 카운트 계산
            var tempDict = DailyShifts
                .GroupBy(c => c.ShiftCode)
                .Where(g => !string.IsNullOrWhiteSpace(g.Key))
                .ToDictionary(g => g.Key!, g => g.Count());

            // 2. 순서 맞춰 다시 채우기
            ShiftCodeCounts.Clear();

            foreach (var shift in MdfScdViewModel.ShiftCodes) {
                tempDict.TryGetValue(shift, out int count);
                ShiftCodeCounts.Add(new KeyValuePair<string, int>(shift, count));
            }

            OnPropertyChanged(nameof(ShiftCodeCounts));
        }

        public int TotalWorkingHours =>
            DailyShifts.Sum(c =>
                MdfScdViewModel.ShiftWorkingHoursMap.TryGetValue(c.ShiftCode ?? "", out int hours) ? hours : 0);

        public int TotalEmptyDays =>
            DailyShifts.Count(c => string.IsNullOrWhiteSpace(c.ShiftCode));

        public int StaffId { get; internal set; }
    }


    /*** Class Schedule Cell ***/
    public partial class ScheduleCell : ObservableObject {

        /** Member Variables **/
        [ObservableProperty] private int day;
        private string shiftCode = "";
        public string ShiftCode {
            get => shiftCode;
            set {
                if (SetProperty(ref shiftCode, value)) {
                    ShiftCodeChanged?.Invoke(this, EventArgs.Empty);
                }
            }
        }
        public event EventHandler? ShiftCodeChanged;
    }


    /*** Class ShiftHeader ***/
    public class ShiftHeader {
        public string DisplayName { get; set; } = "";   // 예: "Total D"
        public string ShiftCode { get; set; } = "";     // 예: "D"
    }


    /*** Class Daily Shift Status ***/
    public class DailyShiftStats : ObservableObject {
        public int Day { get; set; }

        // shift 코드 → 해당 일에 몇 명이 이 교대를 했는지
        public Dictionary<string, int> ShiftCounts { get; set; } = new();
    }

}
