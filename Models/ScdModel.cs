using CommunityToolkit.Mvvm.ComponentModel;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Shifter.Services;
using Shifter.Structs;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel.Design.Serialization;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.Models {
    public partial class ScdModel {

        /* Constructor*/
        public ScdModel(Session? session, SocketManager? socket) {
            _session = session!;
            _socket  = socket!;
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


        /* Protocol - gen_timeTable */
        public async Task Gen_TimeTableAsync(int? year, int? month) {
            int admin_uid = _session!.GetCurrentAdminId();
            int team_uid  = _session!.GetCurrentTeamId();

            /* [1] new json */
            JObject sendJson = new JObject {
            { "protocol", "gen_timeTable" },
            { "data", new JObject {
                { "admin_uid", admin_uid },
                { "team_uid", team_uid },
                { "req_year", year.ToString() },
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

            if( protocol == "gen_timeTable" && resp == "success" ) {
                // 성공적으로 테이블 생성됨
                Console.WriteLine("TimeTable generated successfully for {0}-{1}.", year, month);
            } else {
                // 실패 처리
                Console.WriteLine("Failed to generate TimeTable: {0}", recvJson["message"]!.ToString());
            }
        }

        
        /* Protocol - check_today_duty */
        public async Task<List<TodaysDutyInfo>> CheckTodayDutyAsync() {
            /* [1] new json */
            JObject sendJson = new JObject {
                { "protocol", "check_today_duty" },
                { "data", new JObject {
                    { "date", DateTime.Now.Date.ToString()[..10] },
                    { "team_uid", _session!.GetCurrentTeamId() }
                }}
            };

            /* [2] Put json in WorkItem */
            WorkItem sendItem = new WorkItem {
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

            /* [1] new json */
            JObject sendJson = new JObject {
                { "protocol", "req_shift_info" },
                { "data", new JObject {
                    { "team_uid", _session!.GetCurrentTeamId() }
                }}
            };

            /* [2] Put json in WorkItem */
            WorkItem sendItem = new WorkItem {
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
                        EndTime   = shift["end_time"]!.ToString(),
                        DutyHours = shift["duty_hours"]!.ToObject<int>()
                    };
                    _shifts.Add(shiftItem);
                }
            } else {
                // 실패 처리
                Console.WriteLine("Failed to request shift information: {0}", recvJson["message"]!.ToString());

            }
        }
    }



    /*** Today's Duty Info ***/
    public partial class TodaysDutyInfo : ObservableObject {
        [ObservableProperty] private string? shift;          // 근무조
        [ObservableProperty] private string[]? staffName;     // 직원명
    }
}
