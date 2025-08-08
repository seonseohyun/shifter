using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

// Models/AttachmentModel.cs
namespace ShifterUser.Models
{
    public class AttachmentModel
    {
        public string FileName { get; set; } = "";
        // 필요하면 서버 경로/UID 등 추가
        public string? FilePath { get; set; }
    }
}

