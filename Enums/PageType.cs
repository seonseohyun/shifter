using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.Enums {
    public enum PageType {
        LogIn,          // 로그인페이지
        Home,           // 홈페이지
        MngEmpStart,    // 직원관리시작페이지
        MngEmp,         // 근무정보등록페이지
        RgsEmpWork,     // 직급등록페이지
        RgsEmpGrade,    // 직원등록페이지
        RgsEmpInfo,     // 직원관리페이지
        GenScd,         // 근무생성페이지
        MdfScd,         // 스케줄수정페이지
        MngScd,         // 스케줄확인페이지
        ChkChgReq,      // 스케줄 변경 요청사항 확인페이지
        Status,         // 근무기록페이지
        GoBack          // 돌아가기
    }
}
