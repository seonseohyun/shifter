using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using ShifterUser.Enums;
using ShifterUser.Helpers;
using ShifterUser.Services;
using ShifterUser.Models;
using ShifterUser.ViewModels;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ShifterUser.Models
{
    using Newtonsoft.Json.Linq;
    using System;
    using System.Collections.Generic;

    public class NoticeManager
    {
        private readonly SocketManager _socket;
        private readonly UserSession _session;

        public NoticeManager(SocketManager socket, UserSession session)
        {
            _socket = socket;
            _session = session;
        }

        public List<NoticeModel> LoadNoticeList()
        {

            JObject request = new()
            {
                ["protocol"] = "ask_notice_list",
                ["data"] = new JObject
                {
                    ["team_uid"] = _session.GetTeamCode()
                }
            };

            var sendItem = new WorkItem
            {
                json = request.ToString(),
                payload = [],
                path = ""
            };

            _socket.Send(sendItem);
            WorkItem response = _socket.Receive();


            var list = new List<NoticeModel>();

            try
            {
                JObject json = JObject.Parse(response.json);
                string protocol = json["protocol"]?.ToString() ?? "";
                string result = json["resp"]?.ToString() ?? "";

                if (protocol == "ask_notice_list" && result == "success")
                {
                    JArray? arr = (JArray?)json["data"]?["list"];
                    if (arr != null)
                    {
                        foreach (JObject item in arr)
                        {
                            list.Add(new NoticeModel
                            {
                                NoticeUid = (int?)item["notice_uid"] ?? 0,
                                StaffName = item["staff_name"]?.ToString() ?? "",
                                NoticeDate = item["notice_date"]?.ToString() ?? "",
                                Title = item["title"]?.ToString() ?? ""
                            });
                        }
                    }
                }
                else
                {
                    Console.WriteLine($"[경고] 프로토콜/결과 불일치: {protocol}, {result}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[오류] JSON 파싱 오류: {ex.Message}");
            }

            return list;
        }
    }

}
