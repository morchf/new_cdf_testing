using Amazon.SQS;
using Amazon.SQS.Model;
using GTT_Teletrac_Integration.Kinesis;
using Newtonsoft.Json;
using System;
using System.Threading.Tasks;

namespace gtt_service_poc.SQS
{
   public class SQSMessage
   {
      public string DeviceId;
      public string msgData;

      public SQSMessage(string devID, string gpsData)
      {
         this.DeviceId = devID;
         this.msgData = gpsData;
      }

      private SQSMessage() { }

      public override string ToString()
          => JsonConvert.SerializeObject(this);

   }

   class SQSProcessing
   {
      public AmazonSQSConfig SqsConfig { get; set; }
      public AmazonSQSClient SqsClient { get; set; }
      public string QueueUrl { get; set; }
      public string MessageBody { get; set; }

      private static SQSProcessing _instance = new SQSProcessing();
      private static readonly object threadLock = new object();

      private SQSProcessing()
      {

         string ServiceURLVal = Environment.GetEnvironmentVariable("ServiceURL");
         string QueueUrlVal = Environment.GetEnvironmentVariable("QueueURL");

         if (ServiceURLVal == null)
         {
            throw new ArgumentNullException("ServiceURLVal not found");
         }

         if (QueueUrlVal == null)
         {
            throw new ArgumentNullException("QueueUrlVal not found");
         }

         SqsConfig = new AmazonSQSConfig
         {
            ServiceURL = ServiceURLVal
         };
         SqsClient = new AmazonSQSClient(SqsConfig);
         QueueUrl = QueueUrlVal;
      }

      public static async Task SendMsg(string msg, string dupId)
      {
         if (_instance == null)
         {
            lock (threadLock)
            {
               if (_instance == null)
               {
                  _instance = new SQSProcessing();
               }
            }
         }

         try
         {
            string msgGrpID = Guid.NewGuid().ToString();
            string msgDupId = dupId;
            SendMessageRequest sendMessageRequest = new SendMessageRequest
            {
               QueueUrl = _instance.QueueUrl,
               MessageBody = "" + msg,
               MessageGroupId = msgGrpID,
               MessageDeduplicationId = msgDupId
            };

            var sendMessageResponse = await _instance.SqsClient.SendMessageAsync(sendMessageRequest);
            Console.WriteLine("Sent " + msg + "\t\t Response " + sendMessageResponse.HttpStatusCode);
            KinesisProcessing.PostMessage("SQS Message Processing", "Sent...", msg + " (Resp: "+ sendMessageResponse.HttpStatusCode + ")");
         }
         catch(Exception ex)
         {
            throw;
         }
      }
   }
}
