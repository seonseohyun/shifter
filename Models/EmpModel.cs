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
            _socket = socket!;
        }


        /** Member Variables **/
        private readonly Session _session;
        private readonly SocketManager _socket;


        /** Member Methods **/

        /* Protocol - rgs_team_info */
        public async Task RgsTeamInfoAsync(string company_name, string teamname, string job_cate, ObservableCollection<ShiftItem>? shiftitems) {


            /* [0] new jArray */
            JArray jArray = new JArray();
            for (int i = 0; i < shiftitems!.Count; i++) {

                if (shiftitems[i].StartTime == null || shiftitems[i].EndTime == null) {
                    Console.WriteLine("[EmpModel] ShiftItem StartTime or EndTime is null. Skipping this item.");
                    continue; // Skip if StartTime or EndTime is null
                }

                var startStr = shiftitems![i].StartTime![..2];
                var endStr = shiftitems![i].EndTime![..2];

                int duty_hour_int = 0;

                duty_hour_int = int.Parse(endStr) - int.Parse(startStr);

                if (duty_hour_int < 0) {
                    duty_hour_int += 24; // 시간 차이가 음수일 경우, 24시간을 더해줌
                }

                JObject shiftiem = new()
                {
                    ["duty_type"] = shiftitems[i].ShiftType,
                    ["start_time"] = shiftitems[i].StartTime,
                    ["end_time"] = shiftitems[i].EndTime,
                    ["duty_hours"] = duty_hour_int
                };
                jArray.Add(shiftiem);
            }

            /* [1] new json */
            var sendJson = new
            {
                protocol = "rgs_team_info",

                data = new
                {
                    company_name = company_name,
                    team_name = teamname,
                    job_category = job_cate,
                    shift_info = jArray
                }
            };

            /* [2] put json in WorkItem */
            WorkItem sendItem = new WorkItem
            {
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

            if (protocol == "rgs_team_info" && resp == "success") {
                int TeamUid = recvJson["data"]!["team_id"]!.ToObject<int>();
                _session.SetCurrentTeamId(TeamUid);
            }
            else {
                return;
            }
        }


        /* Protocol - rgs_staff_info */
        public async Task<bool> RgsEmpInfoAsync(ObservableCollection<Employee> employees) {

            Console.WriteLine("[EmpModel] RgsStaffInfoAsync Executed");

            /* [0] new jArray */
            JArray jArray = new JArray();
            for (int i = 0; i < employees.Count; i++) {
                Console.WriteLine("[EmpModel] i: " + i.ToString());
                Console.WriteLine("[EmpModel] grade_level: " + employees[i].GradeItem!.GradeNum);
                Console.WriteLine("[EmpModel] staff_name: " + employees[i].EmpName);
                Console.WriteLine("[EmpModel] phone_num: " + employees[i].PhoneNum);
                Console.WriteLine("[EmpModel] total_hours: " + employees[i].TotalHours);
                JObject staff = new()
                {
                    ["grade_level"] = employees[i].GradeItem!.GradeNum,
                    ["staff_name"] = employees[i].EmpName,
                    ["phone_num"] = employees[i].PhoneNum,
                    ["total_hours"] = employees[i].TotalHours
                };
                jArray.Add(staff);
            }

            /* [1] new json */
            var sendJson = new
            {
                protocol = "rgs_staff_info",
                data = new
                {
                    team_uid = _session.GetCurrentTeamId(),
                    staff = jArray
                }
            };

            /* [2] put json in WorkItem */
            WorkItem sendItem = new WorkItem
            {
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

            if (protocol == "rgs_staff_info" && resp == "success") {
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


        /* Protocol - rgs_grade_info */
        public async Task<bool> RgsEmpGradeAsync(ObservableCollection<GradeItem> grades) {
            Console.WriteLine("[EmpModel] RgsEmpGradeAsync Executed");

            /* [0] new jArray */
            JArray jArray = new JArray();
            for (int i = 0; i < grades.Count; i++) {
                JObject grade = new()
                {
                    ["grade_level"] = grades[i].GradeNum,
                    ["grade_name"] = grades[i].GradeName
                };
                jArray.Add(grade);
            }

            /* [1] new json */
            var sendJson = new
            {
                protocol = "rgs_grade_info",
                data = new
                {
                    team_uid = _session.GetCurrentTeamId(),
                    grades = jArray
                }
            };

            /* [2] put json in WorkItem */
            WorkItem sendItem = new WorkItem
            {
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
            if (protocol == "rgs_grade_info" && resp == "success") {
                // Handle success case
                Console.WriteLine("[EmpModel] Employee grade received successfully.");
                return true;
            }
            else {
                // Handle error case
                Console.WriteLine("[EmpModel] Failed to receive employee grade.");
                return false;
            }

        }


        /* Protocol - chk_temp_staff_info */
        /* {
        "protocol": "chk_temp_staff_info",
            "data": {
                "team_uid": 0
            }
        }*/

        public async Task<ObservableCollection<Employee>> ChkTempStaffInfoAsync() {
            Console.WriteLine("[EmpModel] ChkTempStaffInfoAsync Executed");

            /* [0] new json */
            var sendJson = new
            {
                protocol = "chk_temp_staff_info",
                data = new
                {
                    team_uid = _session.GetCurrentTeamId()
                }
            };

            /* [1] put json in WorkItem */
            WorkItem sendItem = new WorkItem
            {
                json = JObject.FromObject(sendJson).ToString(),
                payload = [],
                path = ""
            };

            /* [2] send the created WorkItem */
            await _socket.SendAsync(sendItem);

            /* [3] create WorkItem response & receive data from the socket. */
            WorkItem recvItem = await _socket.ReceiveAsync();
            JObject recvJson = JObject.Parse(recvItem.json);

            /* [4] parse the data. */
            string protocol = recvJson["protocol"]!.ToString();
            string resp = recvJson["resp"]!.ToString();

            if (protocol == "chk_temp_staff_info" && resp == "success") {
                // Handle success case
                Console.WriteLine("[EmpModel] Temporary staff info received successfully.");
                ObservableCollection<Employee> tempStaffList = new ObservableCollection<Employee>();
                JArray staffArray = (JArray)recvJson["data"]!["staff"]!;
                foreach (var staff in staffArray) {
                    Employee emp = new Employee
                    {
                        GradeItem = new GradeItem
                        {
                            GradeNum  = (int)staff["grade_level"]!,
                            GradeName = (string)staff["grade_name"]!
                        },
                        EmpName     = (string)staff["staff_name"]!,
                        PhoneNum    = (string)staff["phone_num"]!,
                        TotalHours  = (int)staff["total_hours"]!,
                        TempId      = (string)staff["temp_id"]!,
                        TempPw      = (string)staff["temp_pw"]!
                    };
                    tempStaffList.Add(emp);
                }
                return tempStaffList;
            }
            else {
                // Handle error case
                Console.WriteLine("[EmpModel] Failed to receive temporary staff info.");
                return [];
            }
        }
    }


    public partial class ShiftItem : ObservableObject {
        [ObservableProperty] public string? shiftType;    // Ex) "day", "night", "holiday"
        [ObservableProperty] public string? startTime;    // Ex) "08:00", "20:00"
        [ObservableProperty] public string? endTime;      // Ex) "17:00", "05:00"
        [ObservableProperty] public int dutyHours;        // Ex) 8
    }


    public partial class Employee : ObservableObject {
        [ObservableProperty] private GradeItem? gradeItem;     // grade_level, grade_name
        [ObservableProperty] private string?    empName;       // staff_name
        [ObservableProperty] private string?    phoneNum;      // phone_num
        [ObservableProperty] private int?       totalHours;    // total_hours
        [ObservableProperty] private string?    tempId;        // temp_id
        [ObservableProperty] private string?    tempPw;        // temp_pw
    }
}
