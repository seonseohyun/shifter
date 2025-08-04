using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.Models {
    public partial class Session {
        /** Consturctor **/
        public Session() { }


        /** Member Variables **/
        private int CurrentAdminId;
        private int CurrentTeamId;
        private string CurrentTeamName;


        /** Member Mathods **/

        /* Set Variables */
        public void SetCurrentAdminId (int adminId)     { CurrentAdminId  = adminId; }
        public void SetCurrentTeamId  (int teamId)      { CurrentTeamId   = teamId; }
        public void SetCurrentTeamName(string teamName) { CurrentTeamName = teamName; }
    
        /* Get Variables */
        public int GetCurrentAdminId()     { return CurrentAdminId; }
        public int GetCurrentTeamId()      { return CurrentTeamId; }
        public string GetCurrentTeamName() { return CurrentTeamName; }
    }
}
