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
        public RgsEmpInfoViewModel(Session? session, EmpModel? empModel) {
            _session = session;
            _empmodel = empModel;
            Grades = new ObservableCollection<GradeItem>(_session!.Grades);     // GradeItem 객체를 Session에서 가져옴
        }



        /** Member Variables **/
        private readonly Session? _session;
        private readonly EmpModel? _empmodel;
        [ObservableProperty] private ObservableCollection<Employee> employees = new();
        [ObservableProperty] private IList<GradeItem> grades;



        /** Member Methods **/
        [RelayCommand] private void AddEmp() {
            Employees.Add(new Employee
            {
                GradeItem = Grades.First(),
                EmpName = "",
                PhoneNum = "",

            });
        }


        /* Register Employee Information */
        [RelayCommand] private void RgsEmpInfo() {
            Console.WriteLine("[RgsEmpInfoViewModel] Executed RgsEmpInfo()");

            /* Register Employee Info on Server */
            _empmodel!.RgsEmpInfoAsync(Employees).ContinueWith(task => {
                if (task.IsFaulted) {
                    Console.WriteLine("[RgsEmpInfoViewModel] Error: " + task.Exception?.Message);
                } else {
                    Console.WriteLine("[RgsEmpInfoViewModel] Employee information registered successfully.");
                }
            });


            /* Change Page */
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.ChkTmpEmpInfo));
        }
    }
}



public partial class Employee : ObservableObject {
    [ObservableProperty] private GradeItem? gradeItem;     // grade_level, grade_name
    [ObservableProperty] private string?    empName;       // staff_name
    [ObservableProperty] private string?    phoneNum;      // phone_num
    [ObservableProperty] private int?       totalHours;    // total_hours
}