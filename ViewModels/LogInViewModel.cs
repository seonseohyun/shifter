using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using Shifter.Messages;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Shifter.Enums;

namespace Shifter.ViewModels {
    public partial class LogInViewModel : ObservableObject{

        /** Constructor **/
        public LogInViewModel(Session? session, UserModel? userModel) {
            Console.WriteLine("[LogInViewModel] Allocated in Memory");
            _session   = session!;
            _userModel = userModel!;

            _session.VisToolbar = false;    // LogInViewModel 생성 시, MainWindow의 Toolbar Visibillity = Collapsed
        }



        /** Member Variables **/
        /* Models */
        private readonly Session?   _session;
        private readonly UserModel? _userModel;
        
        /* Observable Properties */
        [ObservableProperty] string? id;
        [ObservableProperty] string? pw;


        /** Member Methods **/
        [RelayCommand] async Task LogInAsync() {
            if( Id.Length>0 && Pw.Length>0) {
                bool result = await _userModel!.LogInAsync(Id, Pw);

                if( result ) {
                    WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Home));
                    
                }
            }
        }
    }
}
