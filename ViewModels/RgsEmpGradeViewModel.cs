using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;

namespace Shifter.ViewModels {
    public partial class RgsEmpGradeViewModel : ObservableObject{

        /** Constructor **/
        public RgsEmpGradeViewModel(Session? session) {
            _session = session;
        }



        /** Member Variables **/
        private readonly Session? _session;
        [ObservableProperty] private ObservableCollection<GradeItem> grades = new();



        /** Member Methods **/
        [RelayCommand] void AddGrade() {
            if( Grades.Count < 5) {
                Grades.Add(new GradeItem
                {
                    GradeNum = Grades.Count+1,
                    GradeName = ""
                });
            }
            else if( Grades.Count == 5 ) {
                MessageBox.Show("직급정보는 최대 다섯개까지 추가가능합니다.", "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }
    }
}


public partial class GradeItem : ObservableObject {
    [ObservableProperty] private int?    gradeNum;
    [ObservableProperty] private string? gradeName;
}