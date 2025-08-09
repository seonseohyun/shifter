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
        public string FileName { get; set; } = "";   // UI 표시용
        public string LocalPath { get; set; } = "";  // 로컬 전체 경로 (열기/보기용)
    }
}

