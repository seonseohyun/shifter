using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using Microsoft.Win32;
using ShifterUser.Enums;
using ShifterUser.Helpers;
using ShifterUser.Messages;
using ShifterUser.Models;
using ShifterUser.Services;
using System;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Threading.Tasks;

namespace ShifterUser.ViewModels
{
    public partial class WriteHandoverViewModel : ObservableObject
    {
        private readonly UserSession _session;
        private readonly HandoverManager _manager;
        private readonly IUserScheduleProvider _schedule;

        public ObservableCollection<string> HandoverTypes { get; } = new()
        { "교대", "출장", "휴가/부재", "퇴사", "장비/물품", "기타" };

        // UI가 바인딩해서 쓰는 편집 대상
        [ObservableProperty] private HandoverDetailModel selectedHandoverDetail = new();
        [ObservableProperty] private bool isAI;
        [ObservableProperty] private string aIMessage = "";


        public WriteHandoverViewModel(UserSession session, HandoverManager manager, IUserScheduleProvider schedule)
        {
            _session = session;
            _manager = manager;
            _schedule = schedule;

            // 기본값 세팅 
            SelectedHandoverDetail.Author = _session.GetName();
            SelectedHandoverDetail.HandoverTime = DateTime.Now.ToString("yyyy-MM-dd");
        }

        // 등록 커맨드
        [RelayCommand]
        private async Task RegisterAsync()
        {
            _schedule.TryGetShiftType(DateTime.Today, out var todayShift);
            SelectedHandoverDetail.ShiftType = todayShift;    // ✅ 모델에 넣기


            var (ok, uid, err) = await _manager.RegisterHandoverAsync(SelectedHandoverDetail); // ✅ 인자 한 개
            if (!ok || uid is null)
            {
                System.Windows.MessageBox.Show(err ?? "등록에 실패했어요.");
                return;
            }

            WeakReferenceMessenger.Default.Send(new HandoverRegisteredMessage(uid.Value));
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.HandoverPopup));
        }

        [RelayCommand]
        private async Task SummarizeAsync()
        {
            if (string.IsNullOrWhiteSpace(SelectedHandoverDetail.Text))
            {
                System.Windows.MessageBox.Show("업무 내용을 먼저 입력하세요.");
                return;
            }

            try
            {
                
                IsAI = true;
                AIMessage = "AI가 문장을 정리하는 중...";

                var result = await _manager.SummarizeJournalAsync(SelectedHandoverDetail.Text);
                if (string.IsNullOrWhiteSpace(result))
                {
                    System.Windows.MessageBox.Show("문장 정리에 실패했습니다.");
                    return;
                }

                SelectedHandoverDetail.Text = result;
                System.Windows.MessageBox.Show("문장 정리가 완료되었습니다.");
            }
            finally
            {
                // 프로퍼티로 끄기
                IsAI = false;
            }
        }


        // 자료 첨부
        [RelayCommand]
        private void AttachFiles()
        {
            var dialog = new OpenFileDialog
            {
                Title = "첨부할 파일 선택",
                Filter = "모든 파일 (*.*)|*.*",
                Multiselect = true
            };

            if (dialog.ShowDialog() == true)
            {
                foreach (var filePath in dialog.FileNames)
                {
                    SelectedHandoverDetail.Attachments.Add(new AttachmentModel
                    {
                        FileName = Path.GetFileName(filePath),
                        LocalPath = filePath
                    });
                }

                // 서버 전송용 필드 업데이트
                SelectedHandoverDetail.IsAttached = SelectedHandoverDetail.Attachments.Count > 0 ? 1 : 0;
                SelectedHandoverDetail.FileName = SelectedHandoverDetail.Attachments.Count > 0
                    ? SelectedHandoverDetail.Attachments[0].FileName
                    : null;
            }
        }

        // 리스트에서 파일 열기
        [RelayCommand]
        private void OpenAttachment(AttachmentModel? att)
        {
            if (att == null || string.IsNullOrWhiteSpace(att.LocalPath)) return;
            if (!File.Exists(att.LocalPath))
            {
                System.Windows.MessageBox.Show("파일을 찾을 수 없습니다.");
                return;
            }

            Process.Start(new ProcessStartInfo
            {
                FileName = att.LocalPath,
                UseShellExecute = true
            });
        }

        // 리스트에서 제거
        [RelayCommand]
        private void RemoveAttachment(AttachmentModel? att)
        {
            if (att == null) return;
            SelectedHandoverDetail.Attachments.Remove(att);

            SelectedHandoverDetail.IsAttached = SelectedHandoverDetail.Attachments.Count > 0 ? 1 : 0;
            SelectedHandoverDetail.FileName = SelectedHandoverDetail.Attachments.Count > 0
                ? SelectedHandoverDetail.Attachments[0].FileName
                : null;
        }

        [RelayCommand]
        private void GoBack()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(ShifterUser.Enums.PageType.Goback));
        }
    }
}
