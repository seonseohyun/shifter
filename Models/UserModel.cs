using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Shifter.Services;
using Shifter.Structs;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.Models {
    public partial class UserModel {
        /** Constructor **/
        public UserModel(SocketManager socketManager, Session session) {
            Console.WriteLine("[UserModel] Allocated in Memory");
            _socket  = socketManager;
            _session = session;
        }

        /** Member Variables **/
        private readonly SocketManager _socket;
        private readonly Session _session;
        private int AdminUid    { get; set; }
        private int TeamUid     { get; set; }
        private string TeamName { get; set; }


        /** Member Methods **/
        /* LogIn Method */
        public async Task<bool> LogInAsync(string id, string pw) {
            /* [1] new json */
            JObject jsonData = new JObject {
                { "protocol", "login_admin" },
                { "data", new JObject {
                        { "id", id },
                        { "pw", pw }
                    }
                }
            };

            /* [2] Put json in WorkItem */
            WorkItem sendItem = new() {
                json = JsonConvert.SerializeObject(jsonData),
                payload = [],
                path = ""
            };

            /* [3] Send the created WorkItem */
            await _socket.SendAsync(sendItem);

            /* [4] Create WorkItem response & receive data from the socket. */
            WorkItem recvItem = await _socket.ReceiveAsync();
            JObject recvJson  = JObject.Parse(recvItem.json);
            byte[] payload    = recvItem.payload;
            string path       = recvItem.path;

            /* [5] Parse the data. */
            if(recvJson["resp"]!.ToString() == "success") {
                var data = recvJson["data"]!;

                AdminUid = data["admin_uid"]!.ToObject<int>();
                if ( data["team_uid"] is not null ) {
                    TeamUid  = data["team_uid"]!.ToObject<int>();
                    TeamName = data["team_name"]!.ToString();
                }
                else if (data["team_uid"] is null ) {
                    TeamUid  = 0;
                    TeamName = "no team"; 
                }

                /* Set Current Session */
                _session.SetCurrentAdminId(AdminUid);
                _session.SetCurrentTeamId(TeamUid);
                _session.SetCurrentTeamName(TeamName);
                return true;
            }

            return false;
        }
    }
}
