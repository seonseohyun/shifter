using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Shifter.Services;
using Shifter.Structs;
using System;
using System.Collections.Generic;
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
        Session? _session;
        SocketManager? _socket;


        /** Member Method **/
        async Task Gen_TimeTable(int year, int month) {
            int admin_uid = _session.GetCurrentAdminId();
            int team_uid = _session.GetCurrentTeamId();

            /* [1] new json */
            JObject sendJson = new JObject {
            { "protocol", "gen_timeTable" },
            { "data", new JObject {
                { "admin_uid", admin_uid },
                { "team_uid", team_uid },
                { "req_year", year },
                { "req_month", month }
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

        
        async Task CheckTodayDuty() {
            /* [1] new json */
            JObject sendJson = new JObject {
                { "protocol", "check_today_duty" },
                { "data", new JObject {
                    { "date", DateTime.Now.Date },
                    { "team_uid", _session.GetCurrentTeamId() }
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

            if (protocol == "check_today_duty" && resp == "success") {
                // 오늘의 근무가 확인됨
                Console.WriteLine("Today's duty checked successfully.");
            } else {
                // 실패 처리
                Console.WriteLine("Failed to check today's duty: {0}", recvJson["message"]!.ToString());
            }
        }


        async Task ReqShiftInfo() {
            /* [1] new json */
            JObject sendJson = new JObject {
                { "protocol", "req_shift_info" },
                { "data", new JObject {
                    { "team_uid", _session.GetCurrentTeamId() }
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

            if (protocol == "req_shift_info" && resp == "success") {
                // Shift 정보 요청 성공
                Console.WriteLine("Shift information requested successfully.");
                // 추가적인 데이터 처리 로직 필요
            } else {
                // 실패 처리
                Console.WriteLine("Failed to request shift information: {0}", recvJson["message"]!.ToString());
            }
        }
    }
}
