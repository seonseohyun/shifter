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
}
