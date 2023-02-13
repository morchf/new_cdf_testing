using Amazon.KinesisFirehose;
using Amazon.KinesisFirehose.Model;
using Newtonsoft.Json;
using System;
using System.IO;
using System.Text;

namespace GTT_Teletrac_Integration.Kinesis
{

   class GenLog
   {
      public string MessageId { get { return Guid.NewGuid().ToString(); } }
      public string Source { get { return "Teletrack Integration"; } }
      public string Timestamp { get { return DateTime.Now.ToString(); } }
      public string RegionId { get {return "-"; } }
      public string AgencyId { get {return "-"; } }
      public string VehicleId { get {return "-"; } }
      public string DeviceId { get; set; }
      public string MessageType { get; set; }
      public string MessageSubtype { get; set; }
      public string Message { get; set; }

      public string Aux { get; set; }

      public GenLog(string mtype, string msubtype, string msg, string auxInfo, string devId = "-")
      {
         this.MessageType = mtype;
         this.MessageSubtype = msubtype;
         this.Message = msg;
         this.Aux = auxInfo;
         this.DeviceId = devId;
      }

      public override string ToString()
         => JsonConvert.SerializeObject(this);
   }


   class KinesisProcessing
   {
      /// <summary>
      /// 
      /// </summary>
      /// <param name="mtype"></param>
      /// <param name="msubtype"></param>
      /// <param name="msg"></param>
      /// <param name="aux"></param>
      /// <param name="devId"></param>
      public static async void PostMessage(string mtype, string msubtype, string msg, string aux = "", string devId = "-")
      {
         byte[] oByte = Encoding.UTF8.GetBytes(new GenLog(mtype, msubtype, msg, aux, devId).ToString());
         string RegionString = Environment.GetEnvironmentVariable("Region");

         try
         {
            using (MemoryStream ms = new MemoryStream(oByte))
            {
               Amazon.Kinesis.Model.PutRecordRequest requestRecord = new Amazon.Kinesis.Model.PutRecordRequest();

               PutRecordRequest putRecordRequest = new PutRecordRequest();
               
               putRecordRequest.DeliveryStreamName = "TeleTracIntegtrationLogs";
               putRecordRequest.Record = new Record();
               
               putRecordRequest.Record.Data = ms;

               AmazonKinesisFirehoseConfig conf = new AmazonKinesisFirehoseConfig();
               conf.RegionEndpoint = Amazon.RegionEndpoint.USEast1;
               switch (RegionString)
               {
                  case "us-west-1":
                     conf.RegionEndpoint = Amazon.RegionEndpoint.USWest1;
                     break;
                  case "us-west-2":
                     conf.RegionEndpoint = Amazon.RegionEndpoint.USWest2;
                     break;
                  case "us-east-2":
                     conf.RegionEndpoint = Amazon.RegionEndpoint.USEast2;
                     break;
                  case "us-east-1":
                  default:
                     conf.RegionEndpoint = Amazon.RegionEndpoint.USEast1;
                     break;
               }
               
               AmazonKinesisFirehoseClient firehoseClient = new AmazonKinesisFirehoseClient(conf);
               await firehoseClient.PutRecordAsync(putRecordRequest);
            }
         }
         catch (Exception e)
         {
            Console.WriteLine("EXCEPTION IN LOGGING PROCEDURE: " + e);
         }
      }
   }
}
