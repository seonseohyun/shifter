using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using ShifterUser.Enums;
using ShifterUser.Helpers;
using ShifterUser.Models;
using ShifterUser.Services;
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
    using System.Reflection;
    using System.Windows.Controls;

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

        public async Task<NoticeModel?> GetNoticeDetailAsync(int noticeUid)
        {
            JObject request = new()
            {
                ["protocol"] = "ask_notice_detail",
                ["data"] = new JObject
                {
                    ["notice_uid"] = noticeUid
                }
            };

            var sendItem = new WorkItem
            {
                json = request.ToString(),
                payload = [], 
                path = ""
            };

            // 2) 송/수신
            _socket.Send(sendItem);
            WorkItem response = _socket.Receive();

            // 3) 파싱
            JObject json = JObject.Parse(response.json);
            string protocol = json["protocol"]?.ToString() ?? "";
            string result = json["resp"]?.ToString() ?? "";

            if (protocol == "ask_notice_detail" && result == "success")
            {
                var data = json["data"] as JObject;
                if (data == null) return null;

                // 모델 생성해서 매핑
                var model = new NoticeModel
                {
                    NoticeUid = data.Value<int?>("notice_uid") ?? noticeUid,
                    StaffName = data.Value<string>("staff_name") ?? string.Empty,
                    NoticeDate = data.Value<string>("notice_date") ?? string.Empty,  
                    Title = data.Value<string>("title") ?? string.Empty,
                    Content = data.Value<string>("content") ?? string.Empty
                };

                return model; // 반환
            }

            // 실패 케이스
            Console.WriteLine($"[공지 상세] 실패: protocol={protocol}, resp={result}");
            return null; // 모든 경로에서 반환
        }

    }

}
