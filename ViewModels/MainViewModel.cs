using Microsoft.Extensions.DependencyInjection;
using CommunityToolkit.Mvvm.Messaging;
using System.Windows.Controls;
using ShifterUser.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ShifterUser.Enums;
using ShifterUser.Views;
using ShifterUser.ViewModels;
using System.Windows.Navigation;
using ShifterUser.Messages;


namespace ShifterUser.ViewModels
{
    public class MainViewModel
    {
        private Frame _mainFrame;

        public MainViewModel() 
        {
            WeakReferenceMessenger.Default.Register<PageChangeMessage>(this, (r, m) =>
            {
                Navigate(m.Value);
            });
        }

        public void SetFrame(Frame frame)
        {  // 메인 프레임 설정(예: MainWindow.xaml.cs에서 호출)
            _mainFrame = frame;              // 프레임을 설정
            Navigate(PageType.Login);        // 첫 페이지 로딩 ( Enum PageType.Start )
        }

        private void Navigate(PageType page)
        {
            if (_mainFrame == null) return;
            Console.WriteLine($"[MainViewModel] 페이지 전환 요청: {page}");

            switch (page)
            {
                
                case PageType.Login:
                    _mainFrame.Navigate(new LoginView { DataContext = App.Services.GetService(typeof(LoginViewModel)) });
                    break;
                case PageType.Home:
                    _mainFrame.Navigate(new HomeView { DataContext = App.Services.GetService(typeof(HomeViewModel)) });
                    break;
                case PageType.Info:
                    _mainFrame.Navigate(new InfoView { DataContext = App.Services.GetService(typeof(InfoViewModel)) });
                    break;
                case PageType.QR:
                    _mainFrame.Navigate(new QRCheckView { DataContext = App.Services.GetService(typeof(QRCheckViewModel)) });
                    break;
                case PageType.MySche:
                    _mainFrame.Navigate(new MyScheView { DataContext = App.Services.GetService(typeof(MyScheViewModel)) });
                    break;
                case PageType.ReqStatus:
                    _mainFrame.Navigate(new MyReqStatusView { DataContext = App.Services.GetService(typeof(MyReqStatusViewModel)) });
                    break;
                case PageType.ReqSche:
                    _mainFrame.Navigate(new ReqScheView { DataContext = App.Services.GetService(typeof(ReqScheViewModel)) });
                    break;
                case PageType.GroupDashboard:
                    _mainFrame.Navigate(new GroupDashboardView { DataContext = App.Services.GetService(typeof(GroupDashboardViewModel)) });
                    break;
                case PageType.GroupHandover:
                    _mainFrame.Navigate(new GroupHandoverView {  DataContext = App.Services.GetService(typeof(GroupHandoverViewModel)) });
                    break;
                case PageType.Goback:
                        _mainFrame.GoBack();
                        break;
                    }
        }
    }
}
