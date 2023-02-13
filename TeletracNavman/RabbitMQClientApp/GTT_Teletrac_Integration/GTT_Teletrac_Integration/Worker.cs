using gtt_service_poc.Configuration;
using gtt_service_poc.Models;
using gtt_service_poc.Util;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json.Linq;
using PeterO.Cbor;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;
using System;
using System.Collections.Generic;
using System.Net;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using gtt_service_poc.SQS;
using GTT_Teletrac_Integration.Kinesis;

namespace gtt_service_poc
{
   public enum MessageMode
   {
      heli,
      GPIO,
      IOR,//ignition event
      TestGPS,
      TestGPIO
   }

   public class Worker : IHostedService
   {
      private readonly ILogger<Worker> Log;
      private readonly AppConfig Settings;
      MessageMode mode = MessageMode.heli;

      private bool _resub = true;


      public Worker(ILoggerFactory loggerFactory, AppConfig settings)
      {
         Log = loggerFactory.CreateLogger<Worker>();
         Settings = settings;
      }

      public Worker(ILoggerFactory loggerFactory, AppConfig settings, MessageMode mm)
      {

         Log = loggerFactory.CreateLogger<Worker>();
         Settings = settings;
         mode = mm;
      }

      public Task StartAsync(CancellationToken cancellationToken)
      {
         // this will only ever be fired once in application lifecycle.
         Log.LogInformation("Worker starting: " + mode.ToString());
         InitializeAmqpConnections(Settings.Amqp);

         // A single queue contains multiple routing keys
         //  # = wildcard
         //  #.heli = Helicopter/Drone (Second by second GPS)
         //  #.pr2 = Position Change (not second by second)
         //  #.gpio = General Purpose IO
         //  #.ior = Ignition Events
         if (mode == MessageMode.heli)
         {
            Task rebind = Task.Run(() =>
            {
               while (_resub)
               {
                  int rate = Environment.GetEnvironmentVariable("ResubRate") != null ? int.Parse(Environment.GetEnvironmentVariable("ResubRate")) : 7000;
                  BindQueue<AmqpCborMessage>(Settings.Amqp, "heli", new[] { "#.heli" }, Heli_Received);
                  Thread.Sleep(rate);
               }
            }, cancellationToken);
         }
         else if (mode == MessageMode.GPIO)
         {

            Task rebind = Task.Run(() =>
            {
               while (_resub)
               {
                  int rate = Environment.GetEnvironmentVariable("ResubRate") != null ? int.Parse(Environment.GetEnvironmentVariable("ResubRate")) : 7000;
                  BindQueue<AmqpCborMessage>(Settings.Amqp, "gpio", new[] { "#.gpio" }, Gpio_Received);
                  Thread.Sleep(rate);
               }
            }, cancellationToken);
         }
         else if (mode == MessageMode.IOR)
         {
            BindQueue<AmqpCborMessage>(Settings.Amqp, "ior", new[] { "#.ior" }, Ior_Received);
            Task rebind = Task.Run(() =>
            {
               while (_resub)
               {
                  int rate = Environment.GetEnvironmentVariable("ResubRate") != null ? int.Parse(Environment.GetEnvironmentVariable("ResubRate")) : 7000;
                  BindQueue<AmqpCborMessage>(Settings.Amqp, "ior", new[] { "#.ior" }, Ior_Received);
                  Thread.Sleep(rate);
               }
            }, cancellationToken);
         }
         else if (mode == MessageMode.TestGPIO)
         {
            Task rebind = Task.Run(() =>
            {
               while (_resub)
               {
                  int rate = Environment.GetEnvironmentVariable("ResubRate") != null ? int.Parse(Environment.GetEnvironmentVariable("ResubRate")) : 7000;
                  BindQueue<AmqpJsonMessage>(Settings.Amqp, "TestQueue", new[] { "#.GPIO" }, testGPIO_recieved);
                  Thread.Sleep(rate);
               }
            }, cancellationToken);
         }
         else if (mode == MessageMode.TestGPS)
         {
            Task rebind = Task.Run(() =>
            {
               while (_resub)
               {
                  int rate = Environment.GetEnvironmentVariable("ResubRate") != null ? int.Parse(Environment.GetEnvironmentVariable("ResubRate")) : 7000;
                  BindQueue<AmqpJsonMessage>(Settings.Amqp, "TestQueue", new[] { "#.heli" }, testGPS_recieved);
                  Thread.Sleep(rate);
               }
            }, cancellationToken);
         }
         return Task.CompletedTask;
      }

      private List<IModel> AmqpChannels = new List<IModel>();

      #region Amqp Initialization

      private void InitializeAmqpConnections(AmqpClientConfiguration settings)
      {
         Log.LogInformation("Initializing Amqp Connection Factory");

         ConnectionFactory connectionFactory = new ConnectionFactory();

         #region build ConnectionFactory
         //|||
         connectionFactory.HostName = Environment.GetEnvironmentVariable("HostName") != null ? Environment.GetEnvironmentVariable("HostName") : settings.Host;
         connectionFactory.VirtualHost = Environment.GetEnvironmentVariable("VirtualHost") != null ? Environment.GetEnvironmentVariable("VirtualHost") : settings.VirtualHost;
         connectionFactory.Port = Environment.GetEnvironmentVariable("Port") != null ? int.Parse(Environment.GetEnvironmentVariable("Port")) : settings.Port;
         connectionFactory.UserName = settings.UserName; //Environment.GetEnvironmentVariable("UserName") != null ? Environment.GetEnvironmentVariable("UserName") : settings.UserName;
         connectionFactory.Password = settings.Password; //Environment.GetEnvironmentVariable("Password") != null ? Environment.GetEnvironmentVariable("HostName") : settings.Host;

         connectionFactory.RequestedHeartbeat = TimeSpan.FromMilliseconds(settings.HeartbeatInMs);
         connectionFactory.NetworkRecoveryInterval = TimeSpan.FromMilliseconds(settings.ConnectionRetryWaitTimeInMs);
         connectionFactory.AutomaticRecoveryEnabled = true;

         Console.WriteLine("HostName - " + connectionFactory.HostName);
         Console.WriteLine("VirtualHost - " + connectionFactory.VirtualHost);
         Console.WriteLine("Port - " + connectionFactory.Port);
         Console.WriteLine("UserName - " + connectionFactory.UserName);
         Console.WriteLine("Password - " + connectionFactory.Password);


         if (settings.EnableSsl)
         {
            connectionFactory.Ssl.Enabled = true;
            if (settings.DisableSslCertificateValidation)
               connectionFactory.Ssl.CertificateValidationCallback = (sender, certificate, chain, sslPolicyErrors) => true;
         }

         #endregion

         int retryLimit = 10;
         while (retryLimit > 0)
         {
            try
            {
               for (int i = 0; i < settings.ConsumerCount; i++)
               {
                  // one connection per consumer
                  IConnection connection = connectionFactory.CreateConnection();

                  // in the C# lib, the channels are called Models, typical TN best practice is to create one channel per thread.
                  // this allows the channels and connections to be load balanced across our 3 MQ nodes
                  IModel channel = connection.CreateModel();
                  AmqpChannels.Add(channel); // need to keep the channels in memory

                  // QOS = the number of messages to hold unacked before stopping delivery
                  // this setting can help prevent a single app node from being overwhelmed
                  channel.BasicQos(prefetchSize: settings.PrefetchSize, prefetchCount: settings.PrefetchCount, global: false);
               }
               retryLimit = -1;
            }
            catch
            {
               retryLimit--;
               Thread.Sleep(1000);
               if (retryLimit < 1)
               {
                  throw;
               }
            }
         }
      }

      private void BindQueue<TMessage>(AmqpClientConfiguration settings, string name, string[] routingKeys, Action<TMessage> doWork)
          where TMessage : AmqpMessage
      {
         string conTag = Environment.GetEnvironmentVariable("ConsumerTag") != null ? Environment.GetEnvironmentVariable("ConsumerTag") : "gtt";

         string queueName = $"{conTag}.out.{name}";

         //Log.LogInformation($"Binding {string.Join(",", routingKeys)} => {queueName}");

         const string exchangeName = "GTT";

         string dnsHostName = Dns.GetHostName();

         for (int i = 0; i < AmqpChannels.Count; i++)
         {
            IModel channel = AmqpChannels[i];

            // declare the queue
            if (name == "TestQueue")
               channel.QueueDeclare(queue: queueName, durable: false, exclusive: false, autoDelete: false);
            else
               channel.QueueDeclare(queue: queueName, durable: false, exclusive: false, autoDelete: true);

            // bind the queue to the routing keys
            foreach (string routingKey in routingKeys)
               channel.QueueBind(queue: queueName, exchange: exchangeName, routingKey: routingKey);

            EventingBasicConsumer consumer = new EventingBasicConsumer(channel);
            consumer.Received += (s, e) =>
            {
               using (Log.BeginScope($"MessageType: {name}"))
               {
                  Log.LogDebug("Received new message");

                  try
                  {
                     AmqpMessage message = BuildMessage(e);
                     string ogMsgID = "";
                     object msgId;
                     e.BasicProperties.Headers.TryGetValue("messageId", out msgId);
                     if (msgId != null)
                     {
                        foreach (byte b in (byte[])msgId)
                        {
                           ogMsgID += b.ToString();
                        }
                     }
                     else
                     {
                        ogMsgID = Guid.NewGuid().ToString();
                     }
                     if (message.Validated)
                     {
                        using (Log.BeginScope($"Device: {message.DeviceId}"))
                        {
                           if (message is TMessage)
                           {
                              Log.LogTrace("Processing message");

                              try
                              {
                                 doWork((TMessage)message);
                              }
                              catch (Exception ex)
                              {
                                 Log.LogError(ex, "Unable to process message");

                                 KinesisProcessing.PostMessage("Error", "Worker", "Unable to process message:" + ex, $"Device: {message.DeviceId}", "Name :" + name);
                              }
                           }
                           else
                           {
                              Log.LogWarning($"Unable to process message (format = {message.MessageFormat})");
                              KinesisProcessing.PostMessage("Warning", "Worker", $"Unable to process message (format = {message.MessageFormat})");
                           }

                           string sqsMessage = "";
                           // if successful:
                           if (mode == MessageMode.heli)
                           {
                              Gps gps = Gps.FromCbor((message as AmqpCborMessage).Cbor);
                              SQSMessage sqsMsg = new SQSMessage(message.DeviceId, gps.ToString());
                              sqsMessage = sqsMsg.ToString();
                           }
                           else if (mode == MessageMode.GPIO)
                           {
                              GPIOAction gpio = GPIOAction.GPIO((message as AmqpCborMessage).Cbor);
                              SQSMessage sqsMsg = new SQSMessage(message.DeviceId, gpio.ToString());
                              sqsMessage = sqsMsg.ToString();
                           }
                           else if (mode == MessageMode.IOR)
                           {
                              GPIOAction gpio = GPIOAction.Ignition((message as AmqpCborMessage).Cbor);
                              SQSMessage sqsMsg = new SQSMessage(message.DeviceId, gpio.ToString());
                              sqsMessage = sqsMsg.ToString();
                           }
                           else if (mode == MessageMode.TestGPS)
                           {
                              Gps gps = Gps.FromJsonTest((message as AmqpJsonMessage).Json);
                              SQSMessage sqsMsg = new SQSMessage(message.DeviceId, gps.ToString());
                              sqsMessage = sqsMsg.ToString();
                           }
                           else if (mode == MessageMode.TestGPIO)
                           {
                              GPIOAction gpio = GPIOAction.GPIOTest((message as AmqpJsonMessage).Json);
                              SQSMessage sqsMsg = new SQSMessage(message.DeviceId, gpio.ToString());
                              sqsMessage = sqsMsg.ToString();
                           }
                           Console.WriteLine($"Sending {sqsMessage}");
                           SQSProcessing.SendMsg(sqsMessage, ogMsgID);
                        }
                     }
                  }
                  catch (Exception ex)
                  {
                     Log.LogError(ex, "Error occurred while consuming message");
                     KinesisProcessing.PostMessage("Error", "Worker", "Error occurred while consuming message:" + ex);
                     // if unsuccessful:
                     try
                     {
                        channel.BasicNack(e.DeliveryTag, multiple: false, requeue: false);
                     }
                     catch
                     {
                     }
                  }
               }
            };
            string con = Environment.GetEnvironmentVariable("conTag");
            // finally, we bind the consumer
            // autoAck will automatically send success messages
            // the consumerTag must be globally unique across all apps and services in TN360
            // The naming convention is applicationName-hostName-queueName-GUID
            channel.BasicConsume(queue: queueName, autoAck: false, consumerTag: $"{con}-{dnsHostName}-{queueName}-{Guid.NewGuid().ToString("N")}", consumer);
            // Log.LogInformation($"Consuming {queueName} ({i})");
         }
      }

      private AmqpMessage BuildMessage(BasicDeliverEventArgs e)
      {
         Log.LogDebug("Decoding body");

         AmqpRoutingKeyParts routingKey = AmqpRoutingKeyParts.FromString(e.RoutingKey);

         // this value will be the Hermes device IMEI
         string deviceId = routingKey.DeviceId;
         string messageFormat = $"application/{routingKey.Format}";
         if (e.BasicProperties.Headers is not null)
         {
            if (mode.ToString().Contains("Test"))
            {
               messageFormat = "application/json";
            }
            else
            {
               messageFormat = "application/cbor";
            }
            Console.WriteLine("messageFormat decoded as " + messageFormat);
            if (e.BasicProperties.Headers.TryGetValue("deviceId", out object deviceIdObj))
            {
               deviceId = Convert.ToString(deviceIdObj);
               if (deviceId.Contains("Byte"))
               {
                  deviceId = Encoding.UTF8.GetString((byte[])deviceIdObj);
               }
            }
            if (string.IsNullOrWhiteSpace(deviceId))
               deviceId = "**unknown**";
         }
         else
         {
            messageFormat = "application/cbor";
         }
         byte[] body = e.Body.ToArray();

         if (messageFormat.EndsWith("+gzip"))
            body = GZip.UnZip(body);

         AmqpMessage message = new AmqpCborMessage();
         if (messageFormat.StartsWith("application/cbor"))
         {
            try
            {
               CBORObject cbor = CBORObject.DecodeFromBytes(body);
               message = new AmqpCborMessage
               {
                  Cbor = cbor
               };
            }
            catch 
            { }
         }
         else if (messageFormat.StartsWith("application/json"))
         {
            try
            {
               string jsonString = Encoding.UTF8.GetString(body);
               jsonString = jsonString.Replace('\"', '\'');
               jsonString = jsonString.Replace("}, {", ",");
               jsonString = jsonString.Replace(" ", string.Empty);
               jsonString = jsonString.Remove(0, 1);
               jsonString = jsonString.Remove(jsonString.Length - 1, 1);
               JObject json = JObject.Parse(jsonString);
               message = new AmqpJsonMessage
               {
                  Json = json
               };
            }
            catch (Exception ex)
            {
               throw ex;
            }
         }
         else
         {
            KinesisProcessing.PostMessage("Error", "Worker", $"The message format <{messageFormat}> has not been implemented", "", deviceId);
            //throw new NotImplementedException($"The message format <{messageFormat}> has not been implemented");
            return new InvalidMessage();
         }
         message.DeviceId = deviceId;
         message.RoutingKey = routingKey;
         message.Body = body;
         message.Validated = true;
         return message;
      }

      #endregion

      private void Heli_Received(AmqpCborMessage e)
      {
         Gps gps = Gps.FromCbor(e.Cbor);

         Console.WriteLine($"Decoded heli message : {gps}");
         //SQSProcessing.SendMsg(gps.ToString());
         // do whatever additional processing here...
      }

      private void Gpio_Received(AmqpCborMessage e)
      {
         GPIOAction Gpio = GPIOAction.GPIO(e.Cbor);

         Console.WriteLine($"Decoded GPIO message : {Gpio}");
      }

      private void Ior_Received(AmqpCborMessage e)
      {
         GPIOAction Gpio = GPIOAction.Ignition(e.Cbor);

         Console.WriteLine($"Decoded IOR message : {Gpio}");
      }

      private void testGPS_recieved(AmqpJsonMessage e)
      {
         Gps gps = Gps.FromJsonTest(e.Json);

         Console.WriteLine($"Decoded TEST GPS message : {gps}");
      }

      private void testGPIO_recieved(AmqpJsonMessage e)
      {
         GPIOAction Gpio = GPIOAction.GPIOTest(e.Json);

         Console.WriteLine($"{DateTime.Now.ToLongTimeString()} Decoded TEST GPIO message : {Gpio}");
      }

      public Task StopAsync(CancellationToken cancellationToken)
      {
         // this will only ever be fired once in application lifecycle.
         Log.LogInformation("Worker stopping.");
         Log.LogInformation("cancellationToken = " + cancellationToken);
         AmqpChannels.ForEach(channel =>
         {
            try
            {
               if (channel.IsOpen)
                  channel.Close();
            }
            catch { }
         });
         _resub = false;

         return Task.CompletedTask;
      }
   }
}
