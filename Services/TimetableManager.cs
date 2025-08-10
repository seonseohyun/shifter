// Services/TimetableManager.cs
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using ShifterUser.Helpers;
using ShifterUser.Models;
using ShifterUser.Services;

public class TimetableManager
{
    private readonly SocketManager _socket;
    private readonly UserSession _session;

    public TimetableManager(SocketManager socket, UserSession session)
    {
        _socket = socket;
        _session = session;
    }

    // ⬇ 내부 전용 모델(별도 파일 불필요)
    public class TimeTableEntry
    {
        public DateTime Date { get; set; }
        public string Shift { get; set; } = "";    
        public int Hours { get; set; }
        public int ScheduleUid { get; set; }
    }

    public async Task<List<TimeTableEntry>> GetUserTimetableAsync(int year, int month)
    {
        var req = new
        {
            protocol = "ask_timetable_user",
            data = new
            {
                req_year = year.ToString("0000"),
                req_month = month.ToString("00"),
                staff_uid = _session.GetUid()
            }
        };

        _socket.Send(new WorkItem { json = JsonConvert.SerializeObject(req) });

        WorkItem resp = _socket.Receive();

        var root = JObject.Parse(resp.json);

        if ((string?)root["protocol"] != "ask_timetable_user") return new();
        if (!string.Equals((string?)root["resp"], "success", StringComparison.OrdinalIgnoreCase)) return new();

        var arr = (JArray?)root["data"]?["time_table"] ?? new JArray();
        var list = new List<TimeTableEntry>();

        foreach (var it in arr)
        {
            list.Add(new TimeTableEntry
            {
                Date = DateTime.Parse(it["date"]!.ToString()),  // "yyyy-MM-dd"
                Shift = it["shift"]!.ToString(),                  // Day|Eve|Night|Off
                Hours = it["hours"]?.Value<int>() ?? 0,
                ScheduleUid = it["schedule_uid"]?.Value<int>() ?? 0
            });
        }
        return list;
    }

    // 오늘 팀 근무 현황
    // 오늘 팀 근무 현황
    public async Task<List<TodayDutyGroup>> GetTodayDutyAsync(DateTime date, int teamuid)
    {
        var req = new
        {
            protocol = "check_today_duty",
            data = new
            {
                date = date.ToString("yyyy-MM-dd"),
                team_uid = teamuid   // ← 전달받은 매개변수 사용(세션값 쓰려면 이 줄만 교체)
            }
        };

        var sendItem = new WorkItem
        {
            json = JsonConvert.SerializeObject(req),
            payload = Array.Empty<byte>(),
            path = string.Empty
        };

        _socket.Send(sendItem);

        // 수신/기본 가드
        WorkItem recv = _socket.Receive();

        var root = JObject.Parse(recv.json);
        string protocol = root["protocol"]?.ToString() ?? "";
        string resp = root["resp"]?.ToString() ?? "";

        // 프로토콜 체크
        if (!string.Equals(protocol, "check_today_duty", StringComparison.OrdinalIgnoreCase))
            return new List<TodayDutyGroup>();

        // 서버가 ""(빈문자열) 또는 "success" 두 케이스 모두 올 수 있음
        if (!(string.IsNullOrEmpty(resp) || string.Equals(resp, "success", StringComparison.OrdinalIgnoreCase)))
            return new List<TodayDutyGroup>();

        var arr = root["data"] as JArray;
        if (arr == null)
            return new List<TodayDutyGroup>();

        var result = new List<TodayDutyGroup>();

        foreach (var g in arr)
        {
            var shift = g?["shift"]?.ToString() ?? "";
            var staffArr = g?["staff"] as JArray;

            var names = new List<string>();
            if (staffArr != null)
            {
                foreach (var s in staffArr)
                {
                    var name = s?.ToString();
                    if (!string.IsNullOrWhiteSpace(name))
                        names.Add(name);
                }
            }

            // 비어있는 섹션은 추가 안 함(원하면 제거)
            if (names.Count > 0)
            {
                result.Add(new TodayDutyGroup
                {
                    Shift = shift,
                    Staff = names
                });
            }
        }

        // 정렬: D → E → N → O
        static int Key(string s) => (s ?? "").Trim().ToLower() switch
        {
            "d" or "day" => 0,
            "e" or "eve" or "evening" => 1,
            "n" or "night" => 2,
            "o" or "off" => 3,
            _ => 4
        };

        return result.OrderBy(x => Key(x.Shift)).ToList();
    }


    public class TodayDutyGroup
    {
        public string Shift { get; set; } = "";                 // "D"/"E"/"N"/"O" 혹은 영문
        public List<string> Staff { get; set; } = new();        // 이름 리스트
    }
}
