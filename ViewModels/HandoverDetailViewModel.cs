// ViewModels/HandoverDetailViewModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Messages;
using ShifterUser.Models;
using ShifterUser.Services;
using System;
using System.Globalization;

namespace ShifterUser.ViewModels
{
    public partial class HandoverDetailViewModel : ObservableObject
    {
        private readonly HandoverManager _manager;
        private readonly UserSession _session;

        [ObservableProperty] private HandoverDetailModel? selectedHandoverDetail;
        [ObservableProperty] private bool isOwner;   // 수정하기 버튼 Visible 바인딩

        public HandoverDetailViewModel(HandoverManager manager, UserSession session)
        {
            _manager = manager;
            _session = session;

            // 리스트에서 들어오는 handover_uid 수신
            WeakReferenceMessenger.Default.Register<HandoverDetailRequestMessage>(
                this, (r, m) => LoadDetail(m.HandoverUid)
            );
        }

        private void LoadDetail(int uid)
        {
            try
            {
                var detail = _manager.LoadHandoverDetail(uid);
                if (detail == null)
                {
                    Console.WriteLine("[경고] 상세 데이터 로드 실패");
                    return;
                }

                // 작성자는 서버에서 내려준 staff_name 사용
                if (string.IsNullOrWhiteSpace(detail.Author))
                {
                    // 혹시 서버값이 비어오면 마지막 fallback으로 세션 이름
                    detail.Author = _session.GetName();
                }

                // 첨부 단건 응답을 리스트로 변환
                detail.Attachments.Clear();
                if (detail.IsAttached == 1 && !string.IsNullOrWhiteSpace(detail.FileName))
                    detail.Attachments.Add(new AttachmentModel { FileName = detail.FileName });

                SelectedHandoverDetail = detail;

                // 소유자 여부 판단 
                IsOwner = string.Equals(_session.GetName(), detail.Author, StringComparison.Ordinal);

                Console.WriteLine("[디버그] 상세 데이터 로드 완료");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[오류] 상세 로드 중 예외: {ex.Message}");
            }
        }


        [RelayCommand]
        private void GoBack()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(Enums.PageType.Goback));
        }

        [RelayCommand]
        private void Download(object? param)
        {
            if (param is not AttachmentModel att || SelectedHandoverDetail == null) return;
            try
            {
                Console.WriteLine($"[다운로드] {att.FileName}");
                // _manager.DownloadAttachment(SelectedHandoverDetail.HandoverUid, att.FileName);
            }
            catch (Exception ex)
            {
                Console.WriteLine("[오류] 다운로드 실패: " + ex.Message);
            }
        }
    }
}
