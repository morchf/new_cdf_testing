using gtt_service_poc.Configuration;
using gtt_service_poc.SQS;
using GTT_Teletrac_Integration.Kinesis;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using System;
using System.IO;
using System.Linq;

namespace gtt_service_poc
{
   public class Program
   {

      public static void Main(string[] args)
      {
         KinesisProcessing.PostMessage("Information", "Startup", "Starting up...");
         string configurationFile = args.FirstOrDefault(v => v.EndsWith(".json", StringComparison.OrdinalIgnoreCase));

         if (string.IsNullOrWhiteSpace(configurationFile) || !File.Exists(configurationFile))
         {
            Console.WriteLine("Invalid or no configuration file found.");
            KinesisProcessing.PostMessage("Error", "Startup", "Invalid or no configuration file found.");
            Environment.Exit(-1);
         }

         MessageMode mode = (MessageMode)Enum.Parse(typeof(MessageMode), Environment.GetEnvironmentVariable("ProcessingMode"));

         if (mode == MessageMode.heli)
         {
            CreateHostBuilder(args, MessageMode.heli).Build().Run();
         }
         else if (mode == MessageMode.TestGPS)
         {
            {
               CreateHostBuilder(args, MessageMode.TestGPS).Build().Run();
            }
         }
         else if (mode == MessageMode.TestGPIO)
         {
            {
               CreateHostBuilder(args, MessageMode.TestGPIO).Build().Run();
            }
         }
         else
         {
            CreateHostBuilder(args, MessageMode.GPIO).Build().RunAsync();
            CreateHostBuilder(args, MessageMode.IOR).Build().Run();
         }
      }

      public static IHostBuilder CreateHostBuilder(string[] args, MessageMode mm)
      {
         // [KN] normally here, we pass in the appsettings as the argument, but if you don't do that you don't need to.
         string configurationFile = args.FirstOrDefault(v => v.EndsWith(".json", StringComparison.OrdinalIgnoreCase));

         return Host.CreateDefaultBuilder(args)
             // add the custom configuration
             .ConfigureAppConfiguration(builder => builder.AddJsonFile(configurationFile, optional: false))
             .ConfigureServices((hostContext, services) =>
             {
                services.AddLogging(builder =>
                {
                   builder.AddConsole(options =>
                   {
                      options.IncludeScopes = true;
                   });
                });

                IConfiguration configuration = hostContext.Configuration;

                // .NET Core manages it's own IoC container natively, so takes away a lot of overhead for us.

                // we need to extract the config and add it into the IoC container
                AppConfig settings = configuration.Get<AppConfig>();
                services.AddSingleton(settings);

                // initialize the service
                services.AddHostedService(serviceProvider => new Worker(serviceProvider.GetService<ILoggerFactory>(), settings, mm));
             });
      }

   }
}
