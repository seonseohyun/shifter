using CommunityToolkit.Mvvm.ComponentModel;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.Models {
    public partial class Session : ObservableObject {
        /** Consturctor **/
        public Session() { }


        /** Member Variables **/
        private int CurrentAdminId;
        private int CurrentTeamId;
        private string? CurrentCompanyName;
        private string? CurrentTeamName;
        private string? CurrentAdminName;
        private int CurrentYear;
        private int CurrentMonth;
        [ObservableProperty] bool visToolbar = true;
        [ObservableProperty] bool visGoBack  = true;
        public List<GradeItem> Grades { get; set; } = new();


        /** Member Mathods **/

        /* Set Variables */
        public void SetCurrentAdminId (int adminId)     { CurrentAdminId  = adminId; }
        public void SetCurrentTeamId  (int teamId)      { CurrentTeamId   = teamId; }
        public void SetCurrentTeamName(string teamName) { CurrentTeamName = teamName; }
        public void SetCurrentYear    (int year)        { CurrentYear     = year; }
        public void SetCurrentMonth   (int month)       { CurrentMonth    = month; }
        public void SetCurrentCompanyName(string companyName) { CurrentCompanyName = companyName; }
        public void SetCurrentAdminName(string adminName) { CurrentAdminName = adminName; }

        /* Get Variables */
        public int GetCurrentAdminId()     { return CurrentAdminId; }
        public int GetCurrentTeamId()      { return CurrentTeamId; }
        public int GetCurrentYear()        { return CurrentYear; }
        public int GetCurrentMonth()       { return CurrentMonth; }
        public string GetCurrentTeamName() { return CurrentTeamName!; }
        public string GetCurrentCompanyName() { return CurrentCompanyName!; }
        public string GetCurrentAdminName() { return CurrentAdminName!; }
    }
}
