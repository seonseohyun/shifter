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
using Shifter.Enums;

namespace Shifter.ViewModels {
    public partial class RgsEmpInfoViewModel : ObservableObject{

        /** Constructor **/
        public RgsEmpInfoViewModel(Session? session) {
            _session = session;

            Grades = new ObservableCollection<GradeItem>(_session!.Grades);
            for( int i = 0; i < Grades.Count; i++ ) {
                Console.WriteLine($"[RgsEmpInfoViewModel] Grade[{i}] GradeNum: {Grades[i].GradeNum}, GradeName: {Grades[i].GradeName}");
            }
        }



        /** Member Variables **/
        private readonly Session? _session;
        [ObservableProperty] private ObservableCollection<Employee> employees = new();
        [ObservableProperty] private IList<GradeItem> grades;



        /** Member Methods **/
        [RelayCommand] private void AddEmp() {
            Employees.Add(new Employee
            {
                GradeItem = Grades.First(),
                EmpName = "직원명",
                PhoneNum = "010-0000-0000",
                TotalHours = 0
            });
        }


        /* Register Employee Information */
        [RelayCommand] private void RgsEmpInfo() {
            Console.WriteLine("[RgsEmpInfoViewModel] Executed RgsEmpInfo()");

            /* Register Employee Info on Server */

            /* Change Page */
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.ChkTmpEmpInfo));
        }
    }
}



public partial class Employee : ObservableObject {
    [ObservableProperty] private GradeItem? gradeItem;
    [ObservableProperty] private string?    empName;
    [ObservableProperty] private string?    phoneNum;
    [ObservableProperty] private int?       totalHours;
}