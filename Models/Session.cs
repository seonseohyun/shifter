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
        private string? CurrentTeamName;
        [ObservableProperty] bool visToolbar = true;


        /** Member Mathods **/

        /* Set Variables */
        public void SetCurrentAdminId (int adminId)     { CurrentAdminId  = adminId; }
        public void SetCurrentTeamId  (int teamId)      { CurrentTeamId   = teamId; }
        public void SetCurrentTeamName(string teamName) { CurrentTeamName = teamName; }
    
        /* Get Variables */
        public int GetCurrentAdminId()     { return CurrentAdminId; }
        public int GetCurrentTeamId()      { return CurrentTeamId; }
        public string GetCurrentTeamName() { return CurrentTeamName!; }
    }
}
