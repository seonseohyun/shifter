using CommunityToolkit.Mvvm.ComponentModel;
using Newtonsoft.Json.Linq;
using Shifter.Services;
using Shifter.Structs;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Controls;

namespace Shifter.Models {
    public partial class EmpModel {

        /** Constructor **/
        public EmpModel(Session? session, SocketManager? socket) {
            _session = session!;
            _socket  = socket!;
        }

        
        /** Member Variables **/
        private readonly Session _session;
        private readonly SocketManager _socket;


        /** Member Methods **/
        public async Task RgsTeamInfoAsync(string company_name, string teamname, string job_cate, ObservableCollection<ShiftItem> ?shiftitems) {


            /* [0] new jArray */
            JArray jArray = new JArray();
            for( int i = 0; i < shiftitems!.Count; i++ ) {

                Console.WriteLine("[Empmodel] i: " + i.ToString());

                var startStr = shiftitems![i].StartTime[..2];
                var endStr = shiftitems![i].EndTime[..2];

                int duty_hour_int = 0;

                duty_hour_int = int.Parse(endStr) - int.Parse(startStr);

                if( duty_hour_int < 0 ) {
                    duty_hour_int += 24; // 시간 차이가 음수일 경우, 24시간을 더해줌
                }

                Console.WriteLine("[EmpModel] duty_hour_int: " + duty_hour_int.ToString());

                JObject shiftiem = new ()
                {
                    ["duty_type"] = shiftitems[i].ShiftType,
                    ["start_time"] = shiftitems[i].StartTime,
                    ["end_time"] = shiftitems[i].EndTime,
                    ["duty_hours"] = duty_hour_int
                };
                jArray.Add(shiftiem);
            }

            Console.WriteLine("[EmpModel] jArray: " + jArray.ToString());

            /* [1] new json */
            var sendJson = new {
                protocol = "rgs_team_info",

                data = new {
                    company = company_name,
                    team_name = teamname,
                    job_category = job_cate,
                    shift_info = jArray
                }
            };

            /* [2] put json in WorkItem */
            WorkItem sendItem = new WorkItem {
                json = JObject.FromObject(sendJson).ToString(),
                payload = [],
                path = ""
            };

            /* [3] send the created WorkItem */
            await _socket.SendAsync(sendItem);

            /* [4] create WorkItem response & receive data from the socket. */
            WorkItem recvItem = await _socket.ReceiveAsync();
            JObject recvJson = JObject.Parse(recvItem.json);

            /* [5] parse the data. */
            string protocol = recvJson["protocol"]!.ToString();
            string resp = recvJson["resp"]!.ToString();

            if( protocol == "rgs_team_info" && resp == "success" ) {
                int TeamUid = recvJson["data"]!["team_id"]!.ToObject<int>();
                _session.SetCurrentTeamId(TeamUid);
            }
            else {
                return;
            }
        }


        /* Protocol rgs_staff_info */
        /*{
          "protocol": "rgs_staff_info",
          "data": {
            "team_uid": 0,
            "staff": [
              {
                "grade_level": 0,
                "staff_name": "",
                "phone_num": "",
                "total_hours": 0
              }
            ]
          }
        }
        */
        public async Task<bool> RgsEmpInfoAsync(ObservableCollection<Employee> employees) {

            Console.WriteLine("[EmpModel] RgsStaffInfoAsync Executed");

            /* [0] new jArray */
            JArray jArray = new JArray();
            for( int i = 0; i < employees.Count; i++ ) {
                Console.WriteLine("[EmpModel] i: " + i.ToString());
                JObject staff = new ()
                {
                    ["grade_level"] = employees[i].GradeItem!.GradeNum,
                    ["staff_name"] = employees[i].EmpName,
                    ["phone_num"] = employees[i].PhoneNum,
                    ["total_hours"] = employees[i].TotalHours
                };
                jArray.Add(staff);
            }

            /* [1] new json */
            var sendJson = new {
                protocol = "rgs_staff_info",
                data = new {
                    team_uid = _session.GetCurrentTeamId()
                }
            };

            /* [2] put json in WorkItem */
            WorkItem sendItem = new WorkItem {
                json = JObject.FromObject(sendJson).ToString(),
                payload = [],
                path = ""
            };

            /* [3] send the created WorkItem */
            await _socket.SendAsync(sendItem);

            /* [4] create WorkItem response & receive data from the socket. */
            WorkItem recvItem = await _socket.ReceiveAsync();
            JObject recvJson = JObject.Parse(recvItem.json);

            /* [5] parse the data. */
            string protocol = recvJson["protocol"]!.ToString();
            string resp = recvJson["resp"]!.ToString();

            if( protocol == "rgs_staff_info" && resp == "success" ) {
                // Handle success case
                Console.WriteLine("[EmpModel] Staff info received successfully.");
                return true;
            }
            else {
                // Handle error case
                Console.WriteLine("[EmpModel] Failed to receive staff info.");
                return false;
            }
        }
    }


    public partial class ShiftItem : ObservableObject {
        [ObservableProperty] public string? shiftType;
        [ObservableProperty] public string? startTime;
        [ObservableProperty] public string? endTime;
        [ObservableProperty] public int dutyHours;
    }
}
