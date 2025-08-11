using CommunityToolkit.Mvvm.ComponentModel;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Shifter.Models;

using System.Collections.ObjectModel;

//////////////////////////////////



// 달력 셀 모델(달력 생성에 필요한 최소 필드만)

////////////////////////////////
public class DayModel
{
    public string? DayText { get; set; }
    public DateTime? Date { get; set; }
    public bool IsToday { get; set; }
}


namespace Shifter.ViewModels {
    public partial class StatusViewModel : ObservableObject {


        public ObservableCollection<DayModel> Days { get; } = new();



        /** Constructor **/
        public StatusViewModel(Session? session) {
            _session = session;
            // 생성자에서 달력 생성 메서드를 호출하여 데이터를 초기화합니다.
            GenerateCalendar(DateTime.Now);
        }

        // 달력 생성
        private void GenerateCalendar(DateTime targetDate)
        {
            Days.Clear();

            var firstDayOfMonth = new DateTime(targetDate.Year, targetDate.Month, 1);
            int daysInMonth = DateTime.DaysInMonth(targetDate.Year, targetDate.Month);
            int skipDays = (int)firstDayOfMonth.DayOfWeek; // 월의 1일이 무슨 요일인지(앞 공백 수)

            // 앞 공백 채우기
            for (int i = 0; i < skipDays; i++)
                Days.Add(new DayModel { DayText = "" });

            // 실제 날짜 채우기
            for (int day = 1; day <= daysInMonth; day++)
            {
                var date = new DateTime(targetDate.Year, targetDate.Month, day);
                Days.Add(new DayModel
                {
                    DayText = day.ToString(),
                    Date = date,
                    IsToday = DateTime.Today.Date == date
                });
            }
        }



        /** Member Variables **/
        private readonly Session? _session;



        /** Member Methods **/
    }
}
