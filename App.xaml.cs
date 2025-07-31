using ShifterUser.Models;
using System;
using System.Configuration;
using System.Data;
using System.Windows;
using ShifterUser.Views;
using ShifterUser.ViewModels;
using ShifterUser.Helpers;
using Microsoft.Extensions.DependencyInjection;

namespace ShifterUser
{
    /// <summary>
    /// App.xaml에 대한 상호 작용 논리
    /// </summary>
    public partial class App : Application
    {
        public static IServiceProvider Helpers { get; private set; }

        public App()
        {
            var serviceCollection = new ServiceCollection();
            ConfigureServices(serviceCollection);
            Helpers = serviceCollection.BuildServiceProvider();

            var socket = Helpers.GetService<Helpers.SocketManager>();
            Console.WriteLine("[App] EnsureConnectedAsync() Executed");
            _ = socket?.EnsureConnectedAsync();
        }

        private static void ConfigureServices(IServiceCollection services)
        {
            // Models
            services.AddSingleton<Models.UserSession>();
            services.AddSingleton<Models.GroupNoticeModel>();
            services.AddSingleton<Models.UserInfoModel>();
            services.AddSingleton<Models.WorkScheReqModel>();

            // Helpers
            services.AddSingleton<Helpers.SocketManager>();

            // ViewModels
            services.AddSingleton<MainVM>();
            services.AddTransient<StartVM>();
            services.AddTransient<LoginVM>();
            services.AddTransient<QRCheckVM>();
            services.AddTransient<HomeVM>();
        }
    }
}
