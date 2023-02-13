namespace gtt_service_poc.Configuration
{
    public class AppConfig
    {
        public string Name { get; set; }

        public AmqpClientConfiguration Amqp { get; set; }
    }
}
