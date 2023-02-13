using gtt_service_poc.DataTypes;
using GTT_Teletrac_Integration.Kinesis;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using PeterO.Cbor;
using System;

namespace gtt_service_poc.Models
{
   public class GPIOAction
   {


      public string Input { get; set; }
      public bool Activation { get; set; }

      public override string ToString()
            => JsonConvert.SerializeObject(this);

      public static GPIOAction GPIO(CBORObject obj)
      {
         Console.WriteLine(obj);
         string[] divided = obj.ToString().Split(',');
         GPIOAction gpio = new GPIOAction();
         if (divided.Length < 18)
         {
            gpio.Activation = false;
            gpio.Input = "None";
            return gpio;
         }
         string action = divided[18].ToLower();
         string val = divided[19];
         string directon = divided[16].ToLower();
         Console.WriteLine("Original GPIO Message "+ obj);
         KinesisProcessing.PostMessage("Message Recieved", "Original GPIO Message", obj.ToString());
         if (action.Contains("siren"))
         { gpio.Input = "Enabled"; }
         else if (action.Contains("input2") || (action.Contains("turnindicator") && directon.Contains("left")))
         { gpio.Input = "LeftTurn"; }
         else if (action.Contains("input3") || (action.Contains("turnindicator") && directon.Contains("right")))
         { gpio.Input = "RightTurn"; }
         else if (action.Contains("input4") || (action.Contains("parkbrake")))
         { gpio.Input = "DisabledMode"; }
         else
         { gpio.Input = "Unknown"; }

         gpio.Activation = val.ToLower().Contains("on");
         Console.WriteLine(gpio);
         return gpio;
      }

      public static GPIOAction Ignition(CBORObject obj)
      {
         Console.WriteLine("Original IOR Message " + obj);
         KinesisProcessing.PostMessage("Message Recieved", "Original IOR Message", obj.ToString());
         string[] divided = obj.ToString().Split(',');
         GPIOAction gpio = new GPIOAction();
         string val = divided[9];

         gpio.Input = "Ignition";

         gpio.Activation = val.Contains("Y");

         return gpio;
      }

      public static GPIOAction GPIOTest(JObject obj)
      {

         KinesisProcessing.PostMessage("TEST Message Recieved", "Original TEST Message", obj.ToString());
         GPIOAction gpio = new GPIOAction();
         gpio.Input = (string)obj.GetValue("Input");
         gpio.Activation = (bool)obj.GetValue("Activation");
         return gpio;
      }
   }
   /// <summary>
   /// Message Class for the GTT required GPIO object
   /// </summary>
   public class GTTGpio
   {
      public string Input { get; set; }
      public bool activation { get; set; }
      public GTTGpio() { }
      public GTTGpio(string input, bool active)
      {
         this.Input = input;
         this.activation = active;
      }

      public override string ToString()
      => JsonConvert.SerializeObject(this);
   }
}
