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
    public partial class GroupHandoverView : Page
    {
        public GroupHandoverView()
        {
            InitializeComponent();
        }

        // GroupHandoverView.xaml.cs

        private void Page_Loaded(object sender, RoutedEventArgs e)
        {
            if (DataContext is GroupHandoverViewModel vm)
            {
                Console.WriteLine("✅ Page_Loaded - 커맨드 실행");
                if (vm.LoadOnAppearAsyncCommand.CanExecute(null))
                    vm.LoadOnAppearAsyncCommand.Execute(null);
            }
        }
    }
}
