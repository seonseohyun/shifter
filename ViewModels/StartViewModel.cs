using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ShifterUser.ViewModels
{
    public partial class StartViewModel : ObservableObject
    {
        [RelayCommand]
        private void GoToLogin()
        {
            Console.WriteLine("GoToLogin Command 호출됨");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Login));
        }
    }
}

//namespace shifter_user.ViewModels
//{
//    public partial class StartVM : ObservableObject
//    {
//        public IRelayCommand GoToLoginCommand { get; }

//        public StartVM()
//        {
//            GoToLoginCommand = new RelayCommand(GoToLogin);
//        }

//        private void GoToLogin()
//        {
//            Console.WriteLine("GoToLogin 수동 호출됨");
//            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Login));
//        }
//    }

//}
