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
    public partial class GroupHandoverViewModel : ObservableObject
    {

        public GroupHandoverViewModel() { }

        [RelayCommand]
        private static void GoBack()
        {
            WeakReferenceMessenger.Default.Send((new PageChangeMessage(PageType.Goback)));
        }
    }
}