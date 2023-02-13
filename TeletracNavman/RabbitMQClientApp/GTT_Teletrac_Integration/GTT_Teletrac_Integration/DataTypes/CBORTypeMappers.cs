using PeterO.Cbor;
using System;

namespace gtt_service_poc.DataTypes
{
    public static class CBORTypeMappers
    {
        static CBORTypeMappers() {
            Default = new CBORTypeMapper()
                .AddConverter(typeof(Half), new HalfCBORConverter());
        }

        public static CBORTypeMapper Default { get; }
    }
}
