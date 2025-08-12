using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using Microsoft.Extensions.DependencyInjection;
using Shifter.Enums;
using Shifter.Messages;
using Shifter.Models;
using Shifter.Views;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
namespace Shifter.ViewModels;

public partial class MainViewModel : ObservableObject {
    
    /** Constructor **/
    public MainViewModel(Session? session) {
        Console.WriteLine("[MainViewModel] Allocated in Memory");
        if (session is not null) {
            _session = session!;
        }
        else if (session is null) {
            Console.WriteLine("[MainViewModel] Session is null");
        }
        WeakReferenceMessenger.Default.Register<PageChangeMessage>(this, (r, m) => {
            Navigate(m.Value);
        });
    }

    

    /** Member Variables **/
    private Frame? _mainFrame;
    private Session? _session;
    public Session Session => _session!; // binding을 위해 public변수 생성



    /** Member Methods **/
    public void SetFrame(Frame frame) {  // 메인 프레임 설정(예: MainWindow.xaml.cs에서 호출)
        Console.WriteLine("[MainViewModel] Executed SetFrame");
        _mainFrame = frame;              // 프레임을 설정

        Navigate(PageType.LogIn);        // 첫 페이지 로딩 ( Enum PageType.LogIn )
    }


    private void Navigate(PageType page) {
        if (_mainFrame == null) return;

        switch (page) {
            case PageType.LogIn:
                _mainFrame.Navigate(new LogInView { DataContext = App.Services!.GetService(typeof(LogInViewModel)) });
                break;
            case PageType.Home:
                Session.VisToolbar = true;
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
            case PageType.ChkTmpEmpInfo:
                _mainFrame.Navigate(new ChkTmpEmpView { DataContext = App.Services!.GetService(typeof(ChkTmpEmpViewModel)) });
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


    /* Go to Home */
    [RelayCommand] void GoToHome() {
        Console.WriteLine("[MainViewModel] GoToHome() Executed");
        Session.VisGoBack = true;
        Navigate(PageType.Home);
    }


    /* Go Back */
    [RelayCommand] void GoBack() {
        Console.WriteLine("[MainViewModel] GoBack() Executed");
        Session.VisGoBack = true;
        Navigate(PageType.GoBack);
    }


    /* Go To MngEmpView */
    [RelayCommand] void GoToMngEmp() {
        Console.WriteLine("[MainViewModel] GoToMngEmp() Executed");
        Session.VisGoBack = true;
        Navigate(PageType.MngEmpStart);
    }


    /* Go To GenDiaryView */
    [RelayCommand] void GoToGenScd() {
        Console.WriteLine("[MainViewModel] GoToGenScd() Executed");
        Session.VisGoBack = true;
        Navigate(PageType.GenScd);
    }


    /* Go To MngScdView */
    [RelayCommand] void GoToMngScd() {
        Console.WriteLine("[MainViewModel] GoToMngScd() Executed");
        Session.VisGoBack = true;
        Navigate(PageType.MngScd);
    }


    /* Go To StatusView */
    [RelayCommand] void GoToStatus() {
        Console.WriteLine("[MainViewModel] GoToStatus() Executed");
        Session.VisGoBack = true;
        Navigate(PageType.Status);
    }


    /* Go To ChkChgReqView */
    [RelayCommand] void GoToChkChgReq() {
        Console.WriteLine("[MainViewModel] GoToChkChgReq() Executed");
        Session.VisGoBack = true;
        Navigate(PageType.ChkChgReq);
    }


    /* Log Out */
    [RelayCommand] void LogOut() {
        MessageBoxResult result = MessageBox.Show("정말로 로그아웃하시겠습니까?" , "로그아웃", MessageBoxButton.YesNo, MessageBoxImage.Question);

        if (result == MessageBoxResult.Yes) {
            Navigate(PageType.LogIn);
        }
        else if (result == MessageBoxResult.No) {
        }
    }
}