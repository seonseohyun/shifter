using ShifterUser.Models;
using System;
using System.Configuration;
using System.Data;
using System.Windows;
using ShifterUser.Views;
using ShifterUser.ViewModels;
using Microsoft.Extensions.DependencyInjection;
using ShifterUser.Services;
using System.Runtime.InteropServices;

namespace ShifterUser
{
    /// <summary>
    /// App.xaml에 대한 상호 작용 논리
    /// </summary>
    public partial class App : Application
    {
        public static IServiceProvider Services { get; private set; }
        //[DllImport("user32.dll")]
        //private static extern bool SetProcessDPIAware();

        public App()
        {
            //SetProcessDPIAware();

            var serviceCollection = new ServiceCollection();
            ConfigureServices(serviceCollection);
            Services = serviceCollection.BuildServiceProvider();

            var socket = Services.GetService<SocketManager>();
            Console.WriteLine("[App] EnsureConnectedAsync() Executed");
            _ = socket?.EnsureConnectedAsync();
        }

        private static void ConfigureServices(IServiceCollection services)
        {
            // Models
            services.AddSingleton<Models.UserSession>();
            services.AddSingleton<Models.UserManager>();
            services.AddSingleton<Models.WorkRequestManager>();

            // Helpers
            services.AddSingleton<SocketManager>();

            // ViewModels
            services.AddSingleton<MainViewModel>();
            services.AddTransient<LoginViewModel>();
            services.AddTransient<QRCheckViewModel>();
            services.AddSingleton<HomeViewModel>();
            services.AddTransient<InfoViewModel>();
            services.AddTransient<MyScheViewModel>();
            services.AddTransient<QRCheckViewModel>();
            services.AddTransient<MyReqStatusViewModel>();
            services.AddTransient<ReqScheViewModel>();
        }
    }
}
