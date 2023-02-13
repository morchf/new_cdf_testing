import base64
import struct
from typing import ClassVar, Dict, Literal, Union

from pydantic import BaseModel, Field


def pad(size: int) -> Field:
    return Field(default=0, exclude=True, struct_fmt=f"{size}x")


def _uint(size: int, struct_fmt: str, **kwargs) -> Field:
    return Field(default=0, ge=0, lt=pow(2, size), struct_fmt=struct_fmt, **kwargs)


def _sint(size: int, struct_fmt: str, **kwargs) -> Field:
    return Field(
        default=0,
        ge=-(2 ** (size - 1)),
        lt=2 ** (size - 1),
        struct_fmt=struct_fmt,
        **kwargs,
    )


def uint8(**kwargs) -> Field:
    return _uint(8, "B", **kwargs)


def uint16(**kwargs) -> Field:
    return _uint(16, "H", **kwargs)


def uint32(**kwargs) -> Field:
    return _uint(32, "I", **kwargs)


def sint8(**kwargs) -> Field:
    return _sint(8, "b", **kwargs)


def sint16(**kwargs) -> Field:
    return _sint(16, "h", **kwargs)


def sint32(**kwargs) -> Field:
    return _sint(32, "i", **kwargs)


class StructModel(BaseModel):
    _fmt_str: ClassVar[str] = ""
    _byte_order_chars: ClassVar[Dict[str, str]] = {"big": ">", "little": "<"}

    def pack(self, byte_order: Literal["big", "little"]) -> bytes:
        fmt_str = self.__class__.get_fmt_str(byte_order)
        return struct.pack(fmt_str, *self.dict().values())

    @classmethod
    def unpack(cls, data: Union[bytes, str], byte_order: Literal["big", "little"]):
        if type(data) == str:
            try:
                data = bytes.fromhex(data)
            except ValueError:
                data = base64.b64decode(data)
        fmt_str = cls.get_fmt_str(byte_order)
        values = struct.unpack(fmt_str, data)
        keys = filter(  # filter out padding fields
            lambda key: not cls.__fields__[key].field_info.exclude,
            cls.__fields__.keys(),
        )
        return cls(**{key: values[i] for i, key in enumerate(keys)})

    @classmethod
    def get_fmt_str(cls, byte_order: Literal["big", "little"]) -> str:
        if not cls._fmt_str:
            for field in cls.__fields__.values():
                cls._fmt_str += field.field_info.extra.get("struct_fmt", "")
        return cls._byte_order_chars[byte_order] + cls._fmt_str
