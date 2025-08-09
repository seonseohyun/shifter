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
using System.Windows;

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
        [RelayCommand] private async Task RgsEmpInfo() {
            Console.WriteLine("[RgsEmpInfoViewModel] Executed RgsEmpInfo()");

            /* Register Employee Info on Server */
            bool result = await _empmodel!.RgsEmpInfoAsync(Employees);
           
            if( result == true ) {
                /* Change Page */
                WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.ChkTmpEmpInfo));
            }
            else if ( result == false ) {
                /* Show Error Message */
                MessageBox.Show("직원정보 등록에 실패했습니다. 다시 시도해주세요.", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            else {
                /* Show Error Message */
                MessageBox.Show("직원정보 등록에 실패했습니다. 다시 시도해주세요.", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }


        }
    }
}