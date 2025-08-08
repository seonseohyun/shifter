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
    public partial class GroupNoticeView : Page
    {
        public GroupNoticeView()
        {
            InitializeComponent();
            Console.WriteLine("[GroupNoticeView] ctor");
        }

        private void Page_Loaded(object sender, RoutedEventArgs e)
        {
            Console.WriteLine("[GroupNoticeView] Loaded 이벤트 발생");
            if (DataContext is GroupNoticeViewModel vm)
            {
                Console.WriteLine("[GroupNoticeView] LoadOnAppearAsyncCommand 실행");
                vm.LoadOnAppearAsyncCommand.Execute(null);
            }
            else
            {
                Console.WriteLine("[GroupNoticeView] DataContext가 VM이 아님");
            }
        }
    }
}
