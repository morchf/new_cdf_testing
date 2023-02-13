using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using PeterO.Cbor;

namespace gtt_service_poc.Models
{
   public abstract class AmqpMessage
   {
      public string DeviceId { get; set; }
      public AmqpRoutingKeyParts RoutingKey { get; set; }
      public byte[] Body { get; set; }
      public AmqpMessageFormat MessageFormat { get; set; }
      public bool Validated { get; set; }
   }

   public class AmqpCborMessage : AmqpMessage
   {
      public AmqpCborMessage()
      {
         base.MessageFormat = AmqpMessageFormat.Cbor;
      }

      public CBORObject Cbor { get; set; }
   }

   public class AmqpJsonMessage : AmqpMessage
   {
      public AmqpJsonMessage()
      {
         base.MessageFormat = AmqpMessageFormat.Json;
      }

      public JObject Json { get; set; }

      public override string ToString()
      {
         return Json.ToString();
      }
   }

   public class InvalidMessage : AmqpMessage
   {
      public InvalidMessage()
      {
         base.MessageFormat = AmqpMessageFormat.Json;
         Validated = false;
      }

   }
   public enum AmqpMessageFormat
   {
      Cbor,
      Json
   }

}
