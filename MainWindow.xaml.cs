using System.Text;
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

namespace Shifter
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            Console.WriteLine("[MainWindow] Allocated in Memory");
            InitializeComponent();

            if (App.Services!.GetService(typeof(MainViewModel)) is MainViewModel mainVM) {
                Console.WriteLine("App.Services!.GetService(typeof(MainViewModel)):" + App.Services!.GetService(typeof(MainViewModel)));
                DataContext = mainVM;
                mainVM.SetFrame(MainFrame);
            }
        }
    }
}