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
