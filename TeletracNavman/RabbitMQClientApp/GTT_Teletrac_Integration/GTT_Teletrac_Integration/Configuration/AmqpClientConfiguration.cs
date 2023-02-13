namespace gtt_service_poc.Configuration
{
    public class AmqpClientConfiguration
    {
        public AmqpClientConfiguration() { }
        public AmqpClientConfiguration(AmqpClientConfiguration other)
        {
            if (other == null) return;

            this.Host = other.Host;
            this.Port = other.Port;
            this.VirtualHost = other.VirtualHost;
            this.UserName = other.UserName;
            this.Password = other.Password;
            this.HeartbeatInMs = other.HeartbeatInMs;

            this.ConsumerTag = other.ConsumerTag;
            this.ConsumerCount = other.ConsumerCount;

            this.PrefetchSize = other.PrefetchSize;
            this.PrefetchCount = other.PrefetchCount;

            this.ConnectionRetryWaitTimeInMs = other.ConnectionRetryWaitTimeInMs;
            this.ConnectionRetryAttempts = other.ConnectionRetryAttempts;

            this.EnableSsl = other.EnableSsl;
            this.DisableSslCertificateValidation = other.DisableSslCertificateValidation;
        }
        public string Host { get; set; }
        public int Port { get; set; } = 5672;
        public string VirtualHost { get; set; } = "/";
        public string UserName { get; set; }
        public string Password { get; set; }
        public int HeartbeatInMs { get; set; }

        public string ConsumerTag { get; set; }
        public int ConsumerCount { get; set; } = 3;

        public uint PrefetchSize { get; set; }
        public ushort PrefetchCount { get; set; }

        public int ConnectionRetryWaitTimeInMs { get; set; } = 1;
        public int ConnectionRetryAttempts { get; set; } = 3;

        public bool EnableSsl { get; set; }
        public bool DisableSslCertificateValidation { get; set; }

        public AmqpClientConfiguration Copy() => new AmqpClientConfiguration(this);
    }
}
