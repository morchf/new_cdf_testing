using System.IO;
using System.IO.Compression;

namespace gtt_service_poc.Util
{
    public static class GZip
    {
        public static byte[] UnZip(byte[] compressedBytes) {
            byte[] uncompressedBytes;
            using (MemoryStream compressedStream = new MemoryStream(compressedBytes))
            using (MemoryStream uncompressedStream = new MemoryStream())
            {
                using (GZipStream gzipStream = new GZipStream(compressedStream, CompressionMode.Decompress))
                {
                    gzipStream.CopyTo(uncompressedStream);
                }

                uncompressedBytes = uncompressedStream.ToArray();
            }

            return uncompressedBytes;
        }
    }
}
