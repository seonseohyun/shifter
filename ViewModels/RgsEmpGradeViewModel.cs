using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using Shifter.Messages;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using Shifter.Enums;

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
        /* Add Grades */
        [RelayCommand] private void AddGrade() {
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


        /* Go To Register Employee Information */
        [RelayCommand] private void GoToRgsEmpInfo() {
            Console.WriteLine("[RgsEmpGradeViewModel] Executed GoToRgsEmpInfo()");

            /* Check Input */
            if (Grades.Count == 0) {
                MessageBox.Show("직급정보를 입력해주세요.", "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            foreach (var grade in Grades) {
                if (grade.GradeNum == null || string.IsNullOrEmpty(grade.GradeName)) {
                    MessageBox.Show("직급정보를 모두 입력해주세요.", "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
            }

            /* Add Input Grades to Session */
            _session!.Grades.Clear();
            for (int i = 0; i < Grades.Count; i++) {
                Console.WriteLine($"[RgsEmpGradeViewModel] Grade[{i}] GradeNum: {Grades[i].GradeNum}, GradeName: {Grades[i].GradeName}");
                _session.Grades.Add(Grades[i]);
            }

            /* NavigatePage */
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.RgsEmpInfo));
        }
    }
}


public partial class GradeItem : ObservableObject {
    [ObservableProperty] private int?    gradeNum;
    [ObservableProperty] private string? gradeName;
}