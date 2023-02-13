namespace gtt_service_poc.Models
{
    public class AmqpRoutingKeyParts
    {
        public string Application { get; set; }
        public string DeviceId { get; set; }
        public string Format { get; set; }
        public string DeviceType { get; set; }
        public string MessageType { get; set; }

        public override string ToString()
            => $"{DeviceType}.{MessageType}";

        public static AmqpRoutingKeyParts FromString(string routingKey) {
            // for messages coming from hermes devices directly, the deviceId is encoded in the routing key
            // a:hermes.i:015677001001211.f:cbor.hermes.heli

            AmqpRoutingKeyParts keyParts = new AmqpRoutingKeyParts();

            string[] parts = routingKey.Split('.');
            // 0 = a:hermes // application:{name}
            // 1 = i:{imei} // deviceId:{imei}
            // 2 = f:cbor // format:cbor
            // 3 = hermes // device type
            // 4 = heli // message type

            int deviceTypeIndex = parts.Length - 2;
            int messageTypeIndex = parts.Length - 1;

            // we loop in case more topics are added to the routing key.
            for (int i = 0; i < parts.Length; i++) {
                string part = parts[i];
                if (i == deviceTypeIndex)
                {
                    keyParts.DeviceType = part;
                }
                else if (i == messageTypeIndex)
                {
                    keyParts.MessageType = part;
                }
                else {
                    string[] keyValue = part.Split(':');
                    if (keyValue.Length == 2) {
                        string key = keyValue[0];
                        string value = keyValue[1];

                        switch (key) {
                            case "a":
                                keyParts.Application = value;
                                break;
                            case "i":
                                keyParts.DeviceId = value;
                                break;
                            case "f":
                                keyParts.Format = value;
                                break;
                            default:
                                // unknown/unsupported.
                                break;
                        }
                    }
                }
            }

            return keyParts;
        }
    }
}
