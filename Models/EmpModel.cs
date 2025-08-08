using CommunityToolkit.Mvvm.ComponentModel;
using Newtonsoft.Json.Linq;
using Shifter.Services;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

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
        async Task RgsTeamInfo(string company_name, string teamname, string job_cate, ObservableCollection<ShiftItem> shiftitems) {

            JArray jArray = new JArray();
            for( int i = 0; i < shiftitems.Count; i++ ) {
                JObject shiftiem = new ()
                {
                    ["duty_type"] = shiftitems[i].ShiftType,
                    ["start_time"] = shiftitems[i].StartTime,
                    ["end_time"] = shiftitems[i].EndTime,
                    ["duty_hours"] = shiftitems[i].EndTime != "00:00" ?
                    (DateTime.Parse(shiftitems[i].EndTime) - DateTime.Parse(shiftitems[i].StartTime)).TotalHours : 0
                };
                jArray.Add(shiftiem);
            }

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
        }
    }


    public partial class ShiftItem : ObservableObject {
        [ObservableProperty]
        public string? shiftType;

        [ObservableProperty]
        public string? startTime;

        [ObservableProperty]
        public string? endTime;
    }
}
