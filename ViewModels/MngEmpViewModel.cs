using CommunityToolkit.Mvvm.ComponentModel;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.ViewModels {
    public partial class MngEmpViewModel : ObservableObject {

        /** Constructor **/
        public MngEmpViewModel(Session? session) {
            _session = session;
            Grades = new ObservableCollection<GradeItem>(_session!.Grades);

            UpdateEmpInfoList();
        }



        /** Member Variables **/
        private readonly Session? _session;
        [ObservableProperty] private ObservableCollection<GradeItem> grades = new();
        [ObservableProperty] private ObservableCollection<EmpInfo> emps = new();



        /** Member Methods **/
        private async Task UpdateEmpInfoList() {
            for (int i = 0; i < 25; i++) {
                Emps.Add(new EmpInfo
                {
                    TeamName = $"팀{i}",
                    EmpId = i + 1,
                    EmpName = $"직원{i}",
                    TotalHours = 10 + i,
                    GradeItem = new GradeItem
                    {
                        GradeName = "TestGrade",
                        GradeNum = i + 1,
                    }
                });
            }
        }
    }


    public partial class EmpInfo : ObservableObject {
        [ObservableProperty] private string    ? teamName   = "";
        [ObservableProperty] private int       ? empId      = 0;
        [ObservableProperty] private string    ? empName    = "";
        [ObservableProperty] private GradeItem ? gradeItem  = null;
        [ObservableProperty] private int       ? totalHours = 0;
    }
}
