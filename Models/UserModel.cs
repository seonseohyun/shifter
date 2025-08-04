using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ShifterUser.Services;
using ShifterUser.Helpers;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace ShifterUser.Models
{
    public class UserModel
    {
        // Meber Variables
        private readonly SocketManager _socket;
        private readonly UserSession _session;


        // 생성자
        public UserModel(SocketManager socket, UserSession session)
        {
            Console.WriteLine("[UserModel] UserModel 인스턴스가 생성되었습니다.");
            _socket = socket;
            _session = session;
        }
        // 사용자 정보
        // 근무표 정보

        /* Method for Protocol-LogIn */
        public bool LogIn(string id, string password)
        {

            /* [1] new json */
            JObject jsonData = new() {
                { "protocol", "login" },
                { "authority","user"},
                { "id", id },
                { "pw", password }
            };

            var sendItem = new WorkItem
            {
                json = JsonConvert.SerializeObject(jsonData),
                payload = [],
                path = ""
            };

            _socket.Send(sendItem);

            WorkItem response = _socket.Receive();

            jsonData = JObject.Parse(response.json);
            string protocol = jsonData["protocol"]?.ToString() ?? "";
            string result = jsonData["resp"]?.ToString() ?? "";

            if (protocol == "login" && result == "success")
            {
                Console.WriteLine("Success Communication with Server");
                //ParentInfo parentInfo = new()
                //{
                //    Name = jsonData["NICKNAME"]?.ToString() ?? "",
                //    Uid = jsonData["PARENTS_UID"]?.ToObject<int>() ?? -1
                //};

                //JArray childrenArray = (JArray)jsonData["CHILDREN"]!;
                //foreach (JObject child in childrenArray.Cast<JObject>())
                //{
                //    string birth = (string)child["BIRTH"]!;
                //    if (string.IsNullOrWhiteSpace(birth)) birth = "00000000";

                //    ChildInfo childInfo = new()
                //    {
                //        Uid = (int)child["CHILDUID"]!,
                //        Name = (string)child["NAME"]!,
                //        BirthDate = birth,
                //        Age = DateTime.Now.Year - int.Parse(birth[..4]),
                //        Gender = (string)child["GENDER"]!,
                //        IconColor = (string)child["ICON_COLOR"]!
                //    };

                //    AddChildInfo(childInfo);
                //}

                //_session.SetCurrentParentUid(parentInfo.Uid);
                //if(ChildrenInfo.Count > 0 ) {
                //    _session.SetCurrentChildUid(ChildrenInfo[0].Uid);
                //}

                //Console.WriteLine($"[UserModel] LogIn Completed");
                return true;
            }
            else if (protocol == "login" && result == "fail")
            {
                return false;
            }
            else
            {
                Console.WriteLine($"[UserModel] 로그인 응답 오류: {result}");
                return false;
            }
        }
    }
}
