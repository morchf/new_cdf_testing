using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace CradlepointSIM.MQTTClient
{
   public class CradlepointGPSMsg
   {
      public fix fix = new fix();
      public gpio gpio = new gpio();
      public string topic;
      public override string ToString()
      {
         return Newtonsoft.Json.JsonConvert.SerializeObject(this);
      }
   }
   public class fix
   {
      public coordinates latitude = new coordinates();
      public coordinates longitude = new coordinates();
      public string from_sentence = "GPGGA";
      public int satelites = 7;
      public int time = 999999;
      public double age = 0.0000000000000000001;
      public double altitude_meters = 275.0;
      public int ground_speed_knots;
      public int heading;
      public int accuracy;
   }

   public class coordinates
   {
      public int degree;
      public int minute;
      public double second;
   }

   public class gpio
   {
      public int pwrIn;
      public int io1;
      public int io2;
      public int io3;
      public int io4;
      public int io5;
   }
}
