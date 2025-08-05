using Microsoft.Extensions.DependencyInjection;
using System.Configuration;
using System.Data;
using System.Windows;


namespace Shifter
{
    public partial class App : Application {
        
        /** Constructor **/
        public App() {
            InitializeComponent();

            Console.WriteLine("[App] Allocated in Memory");
            var serviceCollection = new ServiceCollection();
            ConfigureServices(serviceCollection);
            Services = serviceCollection.BuildServiceProvider();

            var socket = Services.GetService<Services.SocketManager>();
            Console.WriteLine("[App] EnsureConnectedAsync() Executed");
            _ = socket?.EnsureConnectedAsync();
        }



        /** Member Variables **/
        public static IServiceProvider? Services { get; private set; }



        /** Member Methods **/
        private static void ConfigureServices(IServiceCollection services) {
            // Models
            services.AddSingleton<Models.EmpModel>                  ();
            services.AddSingleton<Models.ScdModel>                  ();
            services.AddSingleton<Models.Session>                   ();
            services.AddSingleton<Models.UserModel>                 ();

            // Services
            services.AddSingleton<Services.SocketManager>           ();

            // ViewModels
            services.AddSingleton<ViewModels.MainViewModel>         ();
            services.AddTransient<ViewModels.LogInViewModel>        ();
            services.AddTransient<ViewModels.HomeViewModel>         ();
            services.AddTransient<ViewModels.MngEmpStartViewModel>  ();
            services.AddTransient<ViewModels.RgsEmpWorkViewModel>   ();
            services.AddTransient<ViewModels.RgsEmpGradeViewModel>  ();
            services.AddTransient<ViewModels.RgsEmpInfoViewModel>   ();
            services.AddTransient<ViewModels.ChkTmpEmpViewModel>    ();
            services.AddTransient<ViewModels.MngEmpViewModel>       ();
            services.AddTransient<ViewModels.GenScdViewModel>       ();
            services.AddTransient<ViewModels.MdfScdViewModel>       ();
            services.AddTransient<ViewModels.MngScdViewModel>       ();
            services.AddTransient<ViewModels.ChkChgReqViewModel>    ();
            services.AddTransient<ViewModels.StatusViewModel>       ();
       }
    }
}
