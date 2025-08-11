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
using Shifter.ViewModels;


namespace Shifter.Views {
    /// <summary>
    /// ChkChgReqView.xaml에 대한 상호 작용 논리
    /// </summary>
    public partial class ChkChgReqView : Page {
        public ChkChgReqView() {
            InitializeComponent();
        }

        
        private void Page_Loaded(object sender, RoutedEventArgs e)
        {
            if (DataContext is ChkChgReqViewModel vm)
            {
                Console.WriteLine("Page_Loaded - 커맨드 실행");
                if (vm.LoadOnAppearAsyncCommand.CanExecute(null))
                    vm.LoadOnAppearAsyncCommand.Execute(null);
            }
        }

        
    }
}
