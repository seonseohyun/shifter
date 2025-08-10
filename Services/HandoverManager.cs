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
    public class HandoverManager
    {
        private readonly SocketManager _socket;
        private readonly UserSession _session;

        public HandoverManager(SocketManager socket, UserSession session)
        {
            _socket = socket;
            _session = session;
        }

        public List<HandoverModel> LoadHandoverList()
        {
            JObject request = new()
            {
                ["protocol"] = "ask_handover_list",
                ["data"] = new JObject
                {
                    ["team_uid"] = _session.GetTeamCode()
                }
            };

            WorkItem sendItem = new()
            {
                json = request.ToString(),
                payload = [],
                path = ""
            };

            Console.WriteLine($"[송신] {sendItem.json}");
            _socket.Send(sendItem);

            Console.WriteLine("[디버그] 응답 대기 중...");
            WorkItem response = _socket.Receive();
            Console.WriteLine("[디버그] 응답 수신: " + response.json);

            List<HandoverModel> list = new();

            try
            {
                JObject jsonData = JObject.Parse(response.json);
                string protocol = jsonData["protocol"]?.ToString() ?? "";
                string result = jsonData["resp"]?.ToString() ?? "";

                if (protocol == "ask_handover_list" && result == "success")
                {
                    JArray? arr = (JArray?)jsonData["data"]?["list"];
                    if (arr != null)
                    {
                        foreach (JObject item in arr)
                        {
                            list.Add(new HandoverModel
                            {
                                HandoverUid = (int)item["handover_uid"],
                                Name = item["staff_name"]?.ToString() ?? "",
                                ShiftDate = item["handover_time"]?.ToString()?.Split(' ')[0] ?? "",
                                ShiftTime = ParseShiftTime(item["shift_type"]?.ToString()),
                                ShiftTypeTag = ParseHandoverType(item["note_type"]?.ToString()),
                                Title = item["title"]?.ToString() ?? ""
                            });
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[오류] JSON 파싱 오류: {ex.Message}");
            }

            return list;
        }

        public HandoverDetailModel? LoadHandoverDetail(int handoverUid)
        {

            JObject request = new()
            {
                ["protocol"] = "ask_handover_detail",
                ["data"] = new JObject
                {
                    ["handover_uid"] = handoverUid
                }
            };

            WorkItem sendItem = new()
            {
                json = request.ToString(),
                payload = [],
                path = ""
            };

            Console.WriteLine($"[송신] {sendItem.json}");
            _socket.Send(sendItem);

            Console.WriteLine("[디버그] 응답 대기 중...");
            WorkItem resp = _socket.Receive();
            Console.WriteLine("[디버그] 응답 수신: " + resp.json);

            try
            {
                JObject root = JObject.Parse(resp.json);
                if ((string?)root["protocol"] != "ask_handover_detail") return null;
                if ((string?)root["resp"] != "success") return null;

                JObject? data = (JObject?)root["data"];
                if (data == null) return null;

                var model = new HandoverDetailModel
                {
                    HandoverUid = handoverUid,
                    HandoverTime = data["handover_time"]?.ToString()?.Split(' ')[0] ?? "",
                    Author = data["staff_name"]?.ToString() ?? "",
                    ShiftType = ParseShiftTime(data["shift_type"]?.ToString()),
                    NoteType = ParseHandoverType(data["note_type"]?.ToString()),
                    Title = data["title"]?.ToString() ?? "",
                    Text = data["text"]?.ToString() ?? "",
                    TextParticular = data["text_particular"]?.ToString() ?? "",
                    AdditionalInfo = data["additional_info"]?.ToString() ?? "",
                    IsAttached = (int?)data["is_attached"] ?? 0,
                    FileName = data["file_name"]?.ToString() ?? ""
                };

                return model;
            }
            catch (Exception ex)
            {
                Console.WriteLine("[오류] 상세 파싱 실패: " + ex.Message);
                return null;
            }
        }


        // AI 문장 정리
        public async Task<string?> SummarizeJournalAsync(string rawText)
        {
            var req = new JObject
            {
                ["protocol"] = "summary_journal",
                ["data"] = new JObject { ["text"] = rawText ?? "" }
            };

            var send = new WorkItem { json = req.ToString(), payload = [], path = "" };
            _socket.Send(send);

            WorkItem resp = await Task.Run(() => _socket.Receive());

            var root = JObject.Parse(resp.json);
            if ((string?)root["protocol"] != "summary_journal") return null;
            if (((string?)root["resp"])?.ToLower() != "success") return null;

            return (string?)root["data"]?["text"];
        }

        // 인수인계 등록 
        public async Task<(bool ok, int? handoverUid, string? error)> RegisterHandoverAsync(HandoverDetailModel m)
        {
            
            var req = new JObject
            {
                ["protocol"] = "reg_handover",
                ["data"] = new JObject
                {
                    ["staff_uid"] = _session.GetUid(),
                    ["team_uid"] = _session.GetTeamCode(),
                    ["title"] = m.Title ?? "",
                    ["text"] = m.Text ?? "",
                    ["text_particular"] = m.TextParticular ?? "",
                    ["additional_info"] = m.AdditionalInfo ?? "",
                    ["shift_type"] = ShiftCode.ToCode(m.ShiftType),
                    ["note_type"] = m.NoteTypeDisplay,
                    ["is_attached"] = m.IsAttached,
                    ["file_name"] = m.FileName ?? ""
                }
            };

            var send = new WorkItem { json = req.ToString(), payload = [], path = "" };
            _socket.Send(send);

            WorkItem resp = _socket.Receive();

            var root = JObject.Parse(resp.json);

            var ok = ((string?)root["resp"])?.ToLower() == "success";
            var uid = (int?)root["data"]?["handover_uid"];
            var err = (string?)root["message"] ?? (string?)root["messege"];

            return (ok, uid, ok ? null : err);
        }

        private ShiftType ParseShiftTime(string? str) => str?.ToLower() switch
        {
            "day" => ShiftType.Day,
            "evening" => ShiftType.Evening,
            "night" => ShiftType.Night,
            "off" => ShiftType.Off,
            _ => ShiftType.Off
        };

        private HandoverType ParseHandoverType(string? str) => str switch
        {
            "교대" => HandoverType.교대,
            "출장" => HandoverType.출장,
            "휴가/부재" => HandoverType.휴가및부재,
            "퇴사" => HandoverType.퇴사,
            "장비/물품" => HandoverType.장비및물품,
            "기타" => HandoverType.기타,
            _ => HandoverType.기타
        };

    }

}