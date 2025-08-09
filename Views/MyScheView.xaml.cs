using ShifterUser.ViewModels;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
namespace ShifterUser.Views
{
    /// <summary>
    /// MyScheView.xaml에 대한 상호 작용 논리
    /// </summary>
    public partial class MyScheView : Page
    {
        public MyScheView()
        {
            InitializeComponent();
        }

        private void DetailBackground_MouseDown(object sender, MouseButtonEventArgs e)
        {
            if (DataContext is MyScheViewModel vm)
            {
                if (vm.HideDetailCommand.CanExecute(null))
                    vm.HideDetailCommand.Execute(null);
            }
        }

        private void Page_Loaded(object sender, RoutedEventArgs e)
        {
            if (DataContext is MyScheViewModel vm && vm.LoadOnAppearAsyncCommand.CanExecute(null))
                vm.LoadOnAppearAsyncCommand.Execute(null);
        }

    }
}
