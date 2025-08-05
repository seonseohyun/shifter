using ShifterUser.ViewModels;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace ShifterUser.Views
{
    /// <summary>
    /// MyReqStatusView.xaml에 대한 상호 작용 논리
    /// </summary>
    public partial class MyReqStatusView : Page
    {
        public MyReqStatusView()
        {
            InitializeComponent();
        }

        private void Page_Loaded(object sender, RoutedEventArgs e)
        {
            if (DataContext is MyReqStatusViewModel vm)
            {
                // ViewModel의 LoadOnAppearCommand 실행
                if (vm.LoadOnAppearCommand.CanExecute(null))
                    vm.LoadOnAppearCommand.Execute(null);
            }
        }
    }
}
