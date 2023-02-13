using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Security;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Xml.Serialization;
using uPLibrary.Networking.M2Mqtt;

using Org.BouncyCastle.Crypto;
using Org.BouncyCastle.Crypto.Encodings;
using Org.BouncyCastle.Crypto.Engines;
using Org.BouncyCastle.OpenSsl;

namespace CradlepointSIM.MQTTClient
{
   public enum IoTEndpoint
   {
      dev,
      test,
      pilot,
      prod
   }
   class MainMQTTClient
   {
      public bool Connected = false;
      private string _devEndpoint = "a1gvce2632u6tc-ats.iot.us-east-1.amazonaws.com";
      private string _testEndpoint = "axxai1lkxmzlb-ats.iot.us-east-1.amazonaws.com";
      private string _pilotEndpoint = "a26bc95he55ite-ats.iot.us-east-1.amazonaws.com";
      private string _prodEndpoint = "a257fet5yu52sy-ats.iot.us-east-1.amazonaws.com";
      private int _mqttPort = 8883;
      private X509Certificate2 _certificateAuthority;
      private MqttClient _mqtt = null;
      private IoTEndpoint _targetEndpoint = IoTEndpoint.dev;
      #region Public Methods
      public string Connect(IoTEndpoint endpoint)
      {
         string target = _devEndpoint;
         if (endpoint == IoTEndpoint.test)
            target = _testEndpoint;
         else if (endpoint == IoTEndpoint.pilot)
            target = _pilotEndpoint;
         else if (endpoint == IoTEndpoint.prod)
            target = _prodEndpoint;
         try
         {
            if (_mqtt != null)
            {
               if (_mqtt.IsConnected)
               {
                  //_mqtt.Close();
                  _mqtt.Disconnect();
               }
               _mqtt = null;
            }



           string targetIP = GetIPFromDNS(target);



            _mqtt = new MqttClient(targetIP, _mqttPort, true, null,
                new RemoteCertificateValidationCallback(ValidateServerCertificate),
                new LocalCertificateSelectionCallback(SelectClientCertificate));

            _mqtt.Settings.TimeoutOnConnection = 120000;
            _mqtt.Settings.TimeoutOnReceiving = 120000;

            _mqtt.Connect("Cradlepoint MQTT Message SIM" + Guid.NewGuid().ToString(), "", "", true, 15000);
            if (_mqtt.IsConnected)
            {
               Connected = true;
               return "Connection to " + target +" successful";
            }
            else
               return "CONNECTION to " + target + " FAILED";
         }
         catch (Exception ex)
         {
            return ("CONNECTION to " + target + " FAILED! Exceotion -" + ex.ToString());
         }
      }

      public void Disconnect()
      {
         try
         {
            _mqtt.Disconnect();
         }
         catch { }
      }


      public string Send(CradlepointGPSMsg gpsm)
      {
         try
         {
            _mqtt.Publish(gpsm.topic, Encoding.UTF8.GetBytes(gpsm.ToString()));
            return "Send to " + gpsm.topic + " successful";
         }
         catch (Exception ex)
         {
            return "Send to " + gpsm.topic + "failed - " + ex;
         }
      }

      #region Cert Handling

      /// <summary>
      /// Custom certificate validation method.
      /// </summary>
      /// <param name="sender"></param>
      /// <param name="certificate">Incoming Certificate</param>
      /// <param name="chain">Incoming Certificate chain</param>
      /// <param name="sslPolicyErrors">Validation errors in given chain/certificate</param>
      /// <returns></returns>
      private bool ValidateServerCertificate(object sender, X509Certificate certificate, X509Chain chain, SslPolicyErrors sslPolicyErrors)
      {
         bool keymatch = false;

         X509Certificate2 ca1 = new X509Certificate2(Encoding.UTF8.GetBytes(awsCA1));
         X509Certificate2 ca2 = new X509Certificate2(Encoding.UTF8.GetBytes(awsCA2));
         X509Certificate2 ca3 = new X509Certificate2(Encoding.UTF8.GetBytes(awsCA3));
         X509Certificate2 ca4 = new X509Certificate2(Encoding.UTF8.GetBytes(awsCA4));
         X509Certificate2 ca5 = new X509Certificate2(Encoding.UTF8.GetBytes(awsCA5));
         X509Certificate2 ca6 = new X509Certificate2(Encoding.UTF8.GetBytes(awsCA6));

         List<X509Certificate2> allThumbs = new List<X509Certificate2>();

         try
         {
            foreach (X509ChainElement x in chain.ChainElements)
            {
               allThumbs.Add(x.Certificate);
               if (x.Certificate.Thumbprint == _certificateAuthority.Thumbprint
                  || x.Certificate.Thumbprint == ca1.Thumbprint
                  || x.Certificate.Thumbprint == ca2.Thumbprint
                  || x.Certificate.Thumbprint == ca3.Thumbprint
                  || x.Certificate.Thumbprint == ca4.Thumbprint
                  || x.Certificate.Thumbprint == ca5.Thumbprint
                  || x.Certificate.Thumbprint == ca6.Thumbprint)
               {
                  keymatch = true;
                  break;
               }
            }
         }
         catch (Exception ex)
         {
            //DiagnosticLog.Instance.WriteDiagnosticLog(string.Format("ValidateServerCertificate failure: " + ex.Message));
         }
         return keymatch;
      }

      /// <summary>
      /// Internal Client Certificate Selection Method
      /// </summary>
      /// <param name="sender"></param>
      /// <param name="targetHost"></param>
      /// <param name="localCertificates"></param>
      /// <param name="remoteCertificate"></param>
      /// <param name="acceptableIssuers"></param>
      /// <returns>Client Certificate for SSL Communication</returns>
      private X509Certificate SelectClientCertificate(object sender, string targetHost, X509CertificateCollection localCertificates, X509Certificate remoteCertificate, string[] acceptableIssuers)
      {

         string targetFolder = @"Certs-Dev\";
         switch (_targetEndpoint)
         {
            case (IoTEndpoint.pilot):
               targetFolder = @"Certs-Pilot\";
               break;
            case (IoTEndpoint.test):
               targetFolder = @"Certs-Test\";
               break;
            case (IoTEndpoint.prod):
               targetFolder = @"Certs-Prod\";
               break;
            default:
               targetFolder = @"Certs-Dev\";
               break;
         }

         string targetCertPath = Path.Combine(Environment.CurrentDirectory, @"MQTTClient\" + targetFolder);

        
         return GetCertificate(targetCertPath);
      }

      /// <summary>
      /// Decrypt the active.licx file into necessary security credentials
      /// </summary>
      /// <param name="path"></param>
      /// <returns></returns>
      private X509Certificate GetCertificate(string path)
      {
         try
         {
            string certPath = Path.Combine(path, "cert.crt");
            string keyPath = Path.Combine(path, "cert.key");


            List<string> certLines = new List<string>();
            List<string> keyLines = new List<string>();
            using (StreamReader sr = new StreamReader(certPath))
            {
               while (sr.Peek() >= 0)
               {
                  string line = sr.ReadLine();
                  if (line != string.Empty)
                  {
                     certLines.Add(line);
                  }
               }
            }

            using (StreamReader sr = new StreamReader(keyPath))
            {
               while (sr.Peek() >= 0)
               {
                  string line = sr.ReadLine();
                  if (line != string.Empty)
                  {
                     keyLines.Add(line);
                  }
               }
            }

            string decodedCert = "";
            foreach (string s in certLines)
            {
               if (s != string.Empty)
               {
                  string cleanStr = s.Replace("\n", "").Replace("-----BEGIN CERTIFICATE-----", "").Replace("-----END CERTIFICATE-----", "");  //.Replace("-----BEGIN RSA PRIVATE KEY-----", "").Replace("-----END RSA PRIVATE KEY-----", "");
                  if (cleanStr != string.Empty)
                  {
                     decodedCert += cleanStr + "\n";
                  }
               }
            }

            string decodedKey = "";
            foreach (string s in keyLines)
            {
               if (s != string.Empty)
               {
                  string cleanStr = s.Replace("\n", "").Replace("-----BEGIN CERTIFICATE-----", "").Replace("-----END CERTIFICATE-----", "");  //.Replace("-----BEGIN RSA PRIVATE KEY-----", "").Replace("-----END RSA PRIVATE KEY-----", "");
                  if (cleanStr != string.Empty)
                  {
                     decodedKey += cleanStr + "\n";
                  }
               }
            }



            string keyFile = decodedKey;

            X509Certificate2 clientCertificate = new X509Certificate2(Convert.FromBase64String(decodedCert));
            string AWSCA = awsCA1.Replace("\n", "").Replace("-----BEGIN CERTIFICATE-----", "").Replace("-----END CERTIFICATE-----", "");  //.Replace("-----BEGIN RSA PRIVATE KEY-----", "").Replace("-----END RSA PRIVATE KEY-----", "");

            _certificateAuthority = new X509Certificate2(Convert.FromBase64String(AWSCA));

            //
            // Convert the base 64 encoded string to a key pair
            //
            PemReader pr = new PemReader(new StringReader(keyFile));
            Org.BouncyCastle.Crypto.AsymmetricCipherKeyPair KeyPair = (Org.BouncyCastle.Crypto.AsymmetricCipherKeyPair)pr.ReadObject();
            RSAParameters rsa = Org.BouncyCastle.Security.DotNetUtilities.ToRSAParameters((Org.BouncyCastle.Crypto.Parameters.RsaPrivateCrtKeyParameters)KeyPair.Private);

            RSACryptoServiceProvider p = new RSACryptoServiceProvider();
            p.ImportParameters(rsa);

            // Apparently, using DotNetUtilities to convert the private key is a little iffy. Have to do some init up front.
            RSACryptoServiceProvider rcsp = new RSACryptoServiceProvider(new CspParameters(1, "Microsoft Strong Cryptographic Provider",
                        new Guid().ToString(),
                        new System.Security.AccessControl.CryptoKeySecurity(), null));

            rcsp.ImportCspBlob(p.ExportCspBlob(true));
            clientCertificate.PrivateKey = rcsp;

            return new X509Certificate2(clientCertificate);
         }
         catch (Exception ex)
         {
            string wtf = "";
            throw;
         }
      }


      #region AwS CAs
      public const string awsCA1 = @"-----BEGIN CERTIFICATE-----
MIIDQTCCAimgAwIBAgITBmyfz5m/jAo54vB4ikPmljZbyjANBgkqhkiG9w0BAQsF
ADA5MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRkwFwYDVQQDExBBbWF6
b24gUm9vdCBDQSAxMB4XDTE1MDUyNjAwMDAwMFoXDTM4MDExNzAwMDAwMFowOTEL
MAkGA1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJv
b3QgQ0EgMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALJ4gHHKeNXj
ca9HgFB0fW7Y14h29Jlo91ghYPl0hAEvrAIthtOgQ3pOsqTQNroBvo3bSMgHFzZM
9O6II8c+6zf1tRn4SWiw3te5djgdYZ6k/oI2peVKVuRF4fn9tBb6dNqcmzU5L/qw
IFAGbHrQgLKm+a/sRxmPUDgH3KKHOVj4utWp+UhnMJbulHheb4mjUcAwhmahRWa6
VOujw5H5SNz/0egwLX0tdHA114gk957EWW67c4cX8jJGKLhD+rcdqsq08p8kDi1L
93FcXmn/6pUCyziKrlA4b9v7LWIbxcceVOF34GfID5yHI9Y/QCB/IIDEgEw+OyQm
jgSubJrIqg0CAwEAAaNCMEAwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0OBBYEFIQYzIU07LwMlJQuCFmcx7IQTgoIMA0GCSqGSIb3DQEBCwUA
A4IBAQCY8jdaQZChGsV2USggNiMOruYou6r4lK5IpDB/G/wkjUu0yKGX9rbxenDI
U5PMCCjjmCXPI6T53iHTfIUJrU6adTrCC2qJeHZERxhlbI1Bjjt/msv0tadQ1wUs
N+gDS63pYaACbvXy8MWy7Vu33PqUXHeeE6V/Uq2V8viTO96LXFvKWlJbYK8U90vv
o/ufQJVtMVT8QtPHRh8jrdkPSHCa2XV4cdFyQzR1bldZwgJcJmApzyMZFo6IQ6XU
5MsI+yMRQ+hDKXJioaldXgjUkK642M4UwtBV8ob2xJNDd2ZhwLnoQdeXeGADbkpy
rqXRfboQnoZsG4q5WTP468SQvvG5
-----END CERTIFICATE-----";
      public const string awsCA2 = @"-----BEGIN CERTIFICATE-----
MIIFQTCCAymgAwIBAgITBmyf0pY1hp8KD+WGePhbJruKNzANBgkqhkiG9w0BAQwF
ADA5MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRkwFwYDVQQDExBBbWF6
b24gUm9vdCBDQSAyMB4XDTE1MDUyNjAwMDAwMFoXDTQwMDUyNjAwMDAwMFowOTEL
MAkGA1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJv
b3QgQ0EgMjCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK2Wny2cSkxK
gXlRmeyKy2tgURO8TW0G/LAIjd0ZEGrHJgw12MBvIITplLGbhQPDW9tK6Mj4kHbZ
W0/jTOgGNk3Mmqw9DJArktQGGWCsN0R5hYGCrVo34A3MnaZMUnbqQ523BNFQ9lXg
1dKmSYXpN+nKfq5clU1Imj+uIFptiJXZNLhSGkOQsL9sBbm2eLfq0OQ6PBJTYv9K
8nu+NQWpEjTj82R0Yiw9AElaKP4yRLuH3WUnAnE72kr3H9rN9yFVkE8P7K6C4Z9r
2UXTu/Bfh+08LDmG2j/e7HJV63mjrdvdfLC6HM783k81ds8P+HgfajZRRidhW+me
z/CiVX18JYpvL7TFz4QuK/0NURBs+18bvBt+xa47mAExkv8LV/SasrlX6avvDXbR
8O70zoan4G7ptGmh32n2M8ZpLpcTnqWHsFcQgTfJU7O7f/aS0ZzQGPSSbtqDT6Zj
mUyl+17vIWR6IF9sZIUVyzfpYgwLKhbcAS4y2j5L9Z469hdAlO+ekQiG+r5jqFoz
7Mt0Q5X5bGlSNscpb/xVA1wf+5+9R+vnSUeVC06JIglJ4PVhHvG/LopyboBZ/1c6
+XUyo05f7O0oYtlNc/LMgRdg7c3r3NunysV+Ar3yVAhU/bQtCSwXVEqY0VThUWcI
0u1ufm8/0i2BWSlmy5A5lREedCf+3euvAgMBAAGjQjBAMA8GA1UdEwEB/wQFMAMB
Af8wDgYDVR0PAQH/BAQDAgGGMB0GA1UdDgQWBBSwDPBMMPQFWAJI/TPlUq9LhONm
UjANBgkqhkiG9w0BAQwFAAOCAgEAqqiAjw54o+Ci1M3m9Zh6O+oAA7CXDpO8Wqj2
LIxyh6mx/H9z/WNxeKWHWc8w4Q0QshNabYL1auaAn6AFC2jkR2vHat+2/XcycuUY
+gn0oJMsXdKMdYV2ZZAMA3m3MSNjrXiDCYZohMr/+c8mmpJ5581LxedhpxfL86kS
k5Nrp+gvU5LEYFiwzAJRGFuFjWJZY7attN6a+yb3ACfAXVU3dJnJUH/jWS5E4ywl
7uxMMne0nxrpS10gxdr9HIcWxkPo1LsmmkVwXqkLN1PiRnsn/eBG8om3zEK2yygm
btmlyTrIQRNg91CMFa6ybRoVGld45pIq2WWQgj9sAq+uEjonljYE1x2igGOpm/Hl
urR8FLBOybEfdF849lHqm/osohHUqS0nGkWxr7JOcQ3AWEbWaQbLU8uz/mtBzUF+
fUwPfHJ5elnNXkoOrJupmHN5fLT0zLm4BwyydFy4x2+IoZCn9Kr5v2c69BoVYh63
n749sSmvZ6ES8lgQGVMDMBu4Gon2nL2XA46jCfMdiyHxtN/kHNGfZQIG6lzWE7OE
76KlXIx3KadowGuuQNKotOrN8I1LOJwZmhsoVLiJkO/KdYE+HvJkJMcYr07/R54H
9jVlpNMKVv/1F2Rs76giJUmTtt8AF9pYfl3uxRuw0dFfIRDH+fO6AgonB8Xx1sfT
4PsJYGw=
-----END CERTIFICATE-----";
      public const string awsCA3 = @"-----BEGIN CERTIFICATE-----
MIIBtjCCAVugAwIBAgITBmyf1XSXNmY/Owua2eiedgPySjAKBggqhkjOPQQDAjA5
MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRkwFwYDVQQDExBBbWF6b24g
Um9vdCBDQSAzMB4XDTE1MDUyNjAwMDAwMFoXDTQwMDUyNjAwMDAwMFowOTELMAkG
A1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJvb3Qg
Q0EgMzBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABCmXp8ZBf8ANm+gBG1bG8lKl
ui2yEujSLtf6ycXYqm0fc4E7O5hrOXwzpcVOho6AF2hiRVd9RFgdszflZwjrZt6j
QjBAMA8GA1UdEwEB/wQFMAMBAf8wDgYDVR0PAQH/BAQDAgGGMB0GA1UdDgQWBBSr
ttvXBp43rDCGB5Fwx5zEGbF4wDAKBggqhkjOPQQDAgNJADBGAiEA4IWSoxe3jfkr
BqWTrBqYaGFy+uGh0PsceGCmQ5nFuMQCIQCcAu/xlJyzlvnrxir4tiz+OpAUFteM
YyRIHN8wfdVoOw==
-----END CERTIFICATE-----";
      public const string awsCA4 = @"-----BEGIN CERTIFICATE-----
MIIB8jCCAXigAwIBAgITBmyf18G7EEwpQ+Vxe3ssyBrBDjAKBggqhkjOPQQDAzA5
MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRkwFwYDVQQDExBBbWF6b24g
Um9vdCBDQSA0MB4XDTE1MDUyNjAwMDAwMFoXDTQwMDUyNjAwMDAwMFowOTELMAkG
A1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJvb3Qg
Q0EgNDB2MBAGByqGSM49AgEGBSuBBAAiA2IABNKrijdPo1MN/sGKe0uoe0ZLY7Bi
9i0b2whxIdIA6GO9mif78DluXeo9pcmBqqNbIJhFXRbb/egQbeOc4OO9X4Ri83Bk
M6DLJC9wuoihKqB1+IGuYgbEgds5bimwHvouXKNCMEAwDwYDVR0TAQH/BAUwAwEB
/zAOBgNVHQ8BAf8EBAMCAYYwHQYDVR0OBBYEFNPsxzplbszh2naaVvuc84ZtV+WB
MAoGCCqGSM49BAMDA2gAMGUCMDqLIfG9fhGt0O9Yli/W651+kI0rz2ZVwyzjKKlw
CkcO8DdZEv8tmZQoTipPNU0zWgIxAOp1AE47xDqUEpHJWEadIRNyp4iciuRMStuW
1KyLa2tJElMzrdfkviT8tQp21KW8EA==
-----END CERTIFICATE-----";
      public const string awsCA5 = @"-----BEGIN CERTIFICATE-----
MIIE0zCCA7ugAwIBAgIQGNrRniZ96LtKIVjNzGs7SjANBgkqhkiG9w0BAQUFADCB
yjELMAkGA1UEBhMCVVMxFzAVBgNVBAoTDlZlcmlTaWduLCBJbmMuMR8wHQYDVQQL
ExZWZXJpU2lnbiBUcnVzdCBOZXR3b3JrMTowOAYDVQQLEzEoYykgMjAwNiBWZXJp
U2lnbiwgSW5jLiAtIEZvciBhdXRob3JpemVkIHVzZSBvbmx5MUUwQwYDVQQDEzxW
ZXJpU2lnbiBDbGFzcyAzIFB1YmxpYyBQcmltYXJ5IENlcnRpZmljYXRpb24gQXV0
aG9yaXR5IC0gRzUwHhcNMDYxMTA4MDAwMDAwWhcNMzYwNzE2MjM1OTU5WjCByjEL
MAkGA1UEBhMCVVMxFzAVBgNVBAoTDlZlcmlTaWduLCBJbmMuMR8wHQYDVQQLExZW
ZXJpU2lnbiBUcnVzdCBOZXR3b3JrMTowOAYDVQQLEzEoYykgMjAwNiBWZXJpU2ln
biwgSW5jLiAtIEZvciBhdXRob3JpemVkIHVzZSBvbmx5MUUwQwYDVQQDEzxWZXJp
U2lnbiBDbGFzcyAzIFB1YmxpYyBQcmltYXJ5IENlcnRpZmljYXRpb24gQXV0aG9y
aXR5IC0gRzUwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCvJAgIKXo1
nmAMqudLO07cfLw8RRy7K+D+KQL5VwijZIUVJ/XxrcgxiV0i6CqqpkKzj/i5Vbex
t0uz/o9+B1fs70PbZmIVYc9gDaTY3vjgw2IIPVQT60nKWVSFJuUrjxuf6/WhkcIz
SdhDY2pSS9KP6HBRTdGJaXvHcPaz3BJ023tdS1bTlr8Vd6Gw9KIl8q8ckmcY5fQG
BO+QueQA5N06tRn/Arr0PO7gi+s3i+z016zy9vA9r911kTMZHRxAy3QkGSGT2RT+
rCpSx4/VBEnkjWNHiDxpg8v+R70rfk/Fla4OndTRQ8Bnc+MUCH7lP59zuDMKz10/
NIeWiu5T6CUVAgMBAAGjgbIwga8wDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8E
BAMCAQYwbQYIKwYBBQUHAQwEYTBfoV2gWzBZMFcwVRYJaW1hZ2UvZ2lmMCEwHzAH
BgUrDgMCGgQUj+XTGoasjY5rw8+AatRIGCx7GS4wJRYjaHR0cDovL2xvZ28udmVy
aXNpZ24uY29tL3ZzbG9nby5naWYwHQYDVR0OBBYEFH/TZafC3ey78DAJ80M5+gKv
MzEzMA0GCSqGSIb3DQEBBQUAA4IBAQCTJEowX2LP2BqYLz3q3JktvXf2pXkiOOzE
p6B4Eq1iDkVwZMXnl2YtmAl+X6/WzChl8gGqCBpH3vn5fJJaCGkgDdk+bW48DW7Y
5gaRQBi5+MHt39tBquCWIMnNZBU4gcmU7qKEKQsTb47bDN0lAtukixlE0kF6BWlK
WE9gyn6CagsCqiUXObXbf+eEZSqVir2G3l6BFoMtEMze/aiCKm0oHw0LxOXnGiYZ
4fQRbxC1lfznQgUy286dUV4otp6F01vvpX1FQHKOtw5rDgb7MzVIcbidJ4vEZV8N
hnacRHr2lVz2XTIIM6RUthg/aFzyQkqFOFSDX9HoLPKsEdao7WNq
-----END CERTIFICATE-----";

      public const string awsCA6 = @"-----BEGIN CERTIFICATE-----
MIIEkjCCA3qgAwIBAgITBn+USionzfP6wq4rAfkI7rnExjANBgkqhkiG9w0BAQsF
ADCBmDELMAkGA1UEBhMCVVMxEDAOBgNVBAgTB0FyaXpvbmExEzARBgNVBAcTClNj
b3R0c2RhbGUxJTAjBgNVBAoTHFN0YXJmaWVsZCBUZWNobm9sb2dpZXMsIEluYy4x
OzA5BgNVBAMTMlN0YXJmaWVsZCBTZXJ2aWNlcyBSb290IENlcnRpZmljYXRlIEF1
dGhvcml0eSAtIEcyMB4XDTE1MDUyNTEyMDAwMFoXDTM3MTIzMTAxMDAwMFowOTEL
MAkGA1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJv
b3QgQ0EgMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALJ4gHHKeNXj
ca9HgFB0fW7Y14h29Jlo91ghYPl0hAEvrAIthtOgQ3pOsqTQNroBvo3bSMgHFzZM
9O6II8c+6zf1tRn4SWiw3te5djgdYZ6k/oI2peVKVuRF4fn9tBb6dNqcmzU5L/qw
IFAGbHrQgLKm+a/sRxmPUDgH3KKHOVj4utWp+UhnMJbulHheb4mjUcAwhmahRWa6
VOujw5H5SNz/0egwLX0tdHA114gk957EWW67c4cX8jJGKLhD+rcdqsq08p8kDi1L
93FcXmn/6pUCyziKrlA4b9v7LWIbxcceVOF34GfID5yHI9Y/QCB/IIDEgEw+OyQm
jgSubJrIqg0CAwEAAaOCATEwggEtMA8GA1UdEwEB/wQFMAMBAf8wDgYDVR0PAQH/
BAQDAgGGMB0GA1UdDgQWBBSEGMyFNOy8DJSULghZnMeyEE4KCDAfBgNVHSMEGDAW
gBScXwDfqgHXMCs4iKK4bUqc8hGRgzB4BggrBgEFBQcBAQRsMGowLgYIKwYBBQUH
MAGGImh0dHA6Ly9vY3NwLnJvb3RnMi5hbWF6b250cnVzdC5jb20wOAYIKwYBBQUH
MAKGLGh0dHA6Ly9jcnQucm9vdGcyLmFtYXpvbnRydXN0LmNvbS9yb290ZzIuY2Vy
MD0GA1UdHwQ2MDQwMqAwoC6GLGh0dHA6Ly9jcmwucm9vdGcyLmFtYXpvbnRydXN0
LmNvbS9yb290ZzIuY3JsMBEGA1UdIAQKMAgwBgYEVR0gADANBgkqhkiG9w0BAQsF
AAOCAQEAYjdCXLwQtT6LLOkMm2xF4gcAevnFWAu5CIw+7bMlPLVvUOTNNWqnkzSW
MiGpSESrnO09tKpzbeR/FoCJbM8oAxiDR3mjEH4wW6w7sGDgd9QIpuEdfF7Au/ma
eyKdpwAJfqxGF4PcnCZXmTA5YpaP7dreqsXMGz7KQ2hsVxa81Q4gLv7/wmpdLqBK
bRRYh5TmOTFffHPLkIhqhBGWJ6bt2YFGpn6jcgAKUj6DiAdjd4lpFw85hdKrCEVN
0FE6/V1dN2RMfjCyVSRCnTawXZwXgWHxyvkQAiSr6w10kY17RSlQOYiypok1JR4U
akcjMS9cmvqtmg5iUaQqqcT5NJ0hGA==
-----END CERTIFICATE-----";
      #endregion AwS CAs




      #endregion





      #endregion

      private string GetIPFromDNS(string DNS)
      {
         string result = string.Empty;
         try
         {
            List<IPAddress> addrs = new List<IPAddress>();
            addrs.AddRange(Dns.GetHostAddresses(DNS));
            IPAddress res = addrs.Find(x => x.AddressFamily == AddressFamily.InterNetwork);
            result = res.ToString();
         }
         catch
         {
            throw new Exception("Could not find IP for DNS -" + DNS);
         }
         if (result == string.Empty)
         {
            throw new Exception("Could not find IP for DNS -" + DNS);
         }
         return result;
      }
   }
}
