using PeterO.Cbor;
using System;

namespace gtt_service_poc.DataTypes
{
    public sealed class HalfCBORConverter : ICBORToFromConverter<Half>
    {
        public Half FromCBORObject(CBORObject obj)
        {
            double value = obj.AsDoubleValue();
            return new Half(value);
        }

        public CBORObject ToCBORObject(Half obj)
        {
            byte[] bytes = Half.GetBytes(obj);
            ushort bits = Half.GetBits(obj);
            return CBORObject.FromFloatingPointBits(bits, bytes.Length);
        }
    }
}
