using gtt_service_poc.DataTypes;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using PeterO.Cbor;
using System;

namespace gtt_service_poc.Models
{
   public class Gps
   {
      [JsonProperty(PropertyName = "delayMs")]
      public double DelayMs { get; set; }

      [JsonProperty(PropertyName = "timeAt")]
      public DateTimeOffset TimeAt { get; set; }
      [JsonProperty(PropertyName = "latitude")]
      public float Latitude { get; set; }
      [JsonProperty(PropertyName = "longitude")]
      public float Longitude { get; set; }
      [JsonProperty(PropertyName = "speed")]
      public float? Speed { get; set; }
      [JsonProperty(PropertyName = "altitude")]
      public float? Altitude { get; set; }
      [JsonProperty(PropertyName = "heading")]
      public uint? Heading { get; set; }
      [JsonProperty(PropertyName = "numSatellites")]
      public uint? NumSatellites { get; set; }
      [JsonProperty(PropertyName = "hdop")]
      public float? Hdop { get; set; }

      public override string ToString()
          => JsonConvert.SerializeObject(this);

      public static Gps FromCbor(CBORObject obj)
      {
         Gps gps = new Gps();

         gps.TimeAt = DateTimeOffset.FromUnixTimeSeconds(obj[0].AsInt64Value());
         gps.Latitude = obj[1].ToObject<float>(); // latitude
         gps.Longitude = obj[2].ToObject<float>(); // longitude
         gps.Speed = obj[3].ToObject<float?>(); // speed (km/h)
         gps.Altitude = obj[4].ToObject<float?>(); // altitude (m)
         gps.Heading = obj[5].ToObject<uint?>(); // heading from north (deg)
         gps.NumSatellites = obj[6].ToObject<uint?>(); // number of satellites
         gps.Hdop = obj[7].ToObject<Half?>(CBORTypeMappers.Default); // // horizontal diluation of precision (hdop)

         gps.DelayMs = (DateTime.UtcNow - gps.TimeAt.UtcDateTime).TotalMilliseconds;

         return gps;
      }

      public static Gps FromJsonTest(JObject obj)
      {
         Gps gps = new Gps();

         gps.TimeAt = (DateTimeOffset)obj.GetValue("TimeAt"); //DateTimeOffset
         gps.Latitude = (float)obj.GetValue("Latitude"); // latitude
         gps.Longitude = (float)obj.GetValue("Longitude"); // longitude
         gps.Speed = (float)obj.GetValue("Speed"); // speed (km/h)
         gps.Altitude = (float)obj.GetValue("Altitude"); // altitude (m)
         gps.Heading = (uint)obj.GetValue("Heading"); // heading from north (deg)
         gps.NumSatellites = (uint)obj.GetValue("NumSatellites"); // number of satellites
         gps.Hdop = (float)obj.GetValue("Hdop"); // // horizontal diluation of precision (hdop)

         gps.DelayMs = (DateTime.UtcNow - gps.TimeAt.UtcDateTime).TotalMilliseconds;

         return gps;
      }
   }
}
