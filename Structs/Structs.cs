using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.Structs {
    /// <summary>
    /// '서버와의 소켓 통신을 위한 작업 단위.'
    /// </summary>
    public struct WorkItem {
        public string json;    // 보낼 JSON 문자열
        public byte[] payload; // 보낼 파일 데이터 (없으면 null 또는 빈 배열)
        public string path;    // 파일 경로 (클라이언트 개인용)
    }



    public class TeamInfo {
        public int TeamId = 0;
        public string TeamName = "";
    }
}
