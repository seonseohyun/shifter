using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Helpers;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ShifterUser.ViewModels
{
    public partial class LoginVM : ObservableObject
    {
        public LoginVM()
        {

        }


        [RelayCommand]
        private static void GoBack()
        {
            WeakReferenceMessenger.Default.Send((new PageChangeMessage(PageType.Goback)));
        }
    }

}
