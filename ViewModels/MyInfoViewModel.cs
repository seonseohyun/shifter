using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;


namespace ShifterUser.ViewModels
{
    public partial class MyInfoViewModel : ObservableObject
    {



        [RelayCommand]
        public static void GoBack()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Goback));
        }

    }
}
