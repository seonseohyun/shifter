using CommunityToolkit.Mvvm.Messaging;
using Microsoft.Extensions.DependencyInjection;
using Shifter.Enums;
using Shifter.Messages;
using Shifter.Views;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Controls;
namespace Shifter.ViewModels;

public class MainViewModel {
    
    /** Constructor **/
    public MainViewModel() {
        WeakReferenceMessenger.Default.Register<PageChangeMessage>(this, (r, m) => {
            Navigate(m.Value);
        });
    }

    
    /** Member Variables **/
    private Frame? _mainFrame;


    /** Member Methods **/
    public void SetFrame(Frame frame) {  // 메인 프레임 설정(예: MainWindow.xaml.cs에서 호출)
        Console.WriteLine("[MainViewModel] Executed SetFrame");
        _mainFrame = frame;              // 프레임을 설정
        Navigate(PageType.LogIn);        // 첫 페이지 로딩 ( Enum PageType.LogIn )
    }


    private void Navigate(PageType page) {
        if (_mainFrame == null) return;
        Console.WriteLine($"[MainViewModel] 페이지 전환 요청: {page}");

        switch (page) {
            case PageType.LogIn:
                _mainFrame.Navigate(new LogInView { DataContext = App.Services!.GetService(typeof(LogInViewModel)) });
                break;
            case PageType.Home:
                _mainFrame.Navigate(new HomeView { DataContext = App.Services!.GetService(typeof(HomeViewModel)) });
                break;
            case PageType.MngEmpStart:
                _mainFrame.Navigate(new MngEmpStartView { DataContext = App.Services!.GetService(typeof(MngEmpStartViewModel)) });
                break;
            case PageType.MngEmp:
                _mainFrame.Navigate(new MngEmpView { DataContext = App.Services!.GetService(typeof(MngEmpViewModel)) });
                break;
            case PageType.RgsEmpWork:
                _mainFrame.Navigate(new RgsEmpWorkView { DataContext = App.Services!.GetService(typeof(RgsEmpWorkViewModel)) });
                break;
            case PageType.RgsEmpGrade:
                _mainFrame.Navigate(new RgsEmpGradeView { DataContext = App.Services!.GetService(typeof(RgsEmpGradeViewModel)) });
                break;
            case PageType.RgsEmpInfo:
                _mainFrame.Navigate(new RgsEmpInfoView { DataContext = App.Services!.GetService(typeof(RgsEmpInfoViewModel)) });
                break;
            case PageType.GenScd:
                _mainFrame.Navigate(new GenScdView { DataContext = App.Services!.GetService(typeof(GenScdViewModel)) });
                break;
            case PageType.MdfScd:
                _mainFrame.Navigate(new MdfScdView { DataContext = App.Services!.GetService(typeof(MdfScdViewModel)) });
                break;
            case PageType.MngScd:
                _mainFrame.Navigate(new MngScdView { DataContext = App.Services!.GetService(typeof(MngScdViewModel)) });
                break;
            case PageType.ChkChgReq:
                _mainFrame.Navigate(new ChkChgReqView { DataContext = App.Services!.GetService(typeof(ChkChgReqViewModel)) });
                break;
            case PageType.Status:
                _mainFrame.Navigate(new StatusView { DataContext = App.Services!.GetService(typeof(StatusViewModel)) });
                break;
            case PageType.GoBack:
                _mainFrame.GoBack();
                break;
        }
    }
}

