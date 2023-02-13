import re
from string import Formatter
from typing import Dict, Optional, Union

from pydantic.types import constr

ChannelFormat = constr(regex=r"^((\{[^:]+\})|([^:]+))?((:\{[^:]+\})|(:[^:]+))*$")


class RedisChannel:
    """Consistent handling for Redis channel formats and keyword argument parsing"""

    channel_namespace: Optional[str]
    channel_format: Optional[ChannelFormat] = ""
    _default_channel_kwargs: Dict[str, str] = None

    @classmethod
    def default_channel_kwargs(cls):
        if cls._default_channel_kwargs is not None:
            return cls._default_channel_kwargs

        cls._default_channel_kwargs = {
            fname: "*"
            for _, fname, _, _ in Formatter().parse(cls.channel_format)
            if fname
        }

        return cls._default_channel_kwargs

    @classmethod
    def channel(
        cls,
        channel_prefix: Optional[bool] = None,
        channel_kwargs: Optional[Dict[str, str]] = None,
    ) -> str:
        if channel_kwargs is None:
            channel_kwargs = {}

        namespace_prefix = (
            "" if not hasattr(cls, "channel_namespace") else f"{cls.channel_namespace}:"
        )
        channel_prefix = f"{channel_prefix}_" if channel_prefix else ""

        # Substitute missing channel kwargs for wildard '*'
        channel = cls.channel_format.format(
            **{**cls.default_channel_kwargs(), **channel_kwargs}
        )

        # Simplify repeated ':*' sequences
        return re.sub(r"(:\*)+", ":*", f"{namespace_prefix}{channel_prefix}{channel}")

    @classmethod
    def all(cls) -> str:
        """Channel format with wildcards for all fillable params

        Returns:
            str: Wildcard expression for channel
        """
        return cls.channel()

    @classmethod
    def cache(cls, **kwargs) -> str:
        """Channel namespace and channel name formatted with substituted kwargs or '*'"""
        return cls.channel(channel_kwargs=kwargs)

    @classmethod
    def new(cls, **kwargs) -> str:
        """Channel namespace and channel name with 'new_' formatted with substituted kwargs or '*'"""
        return cls.channel(channel_prefix="new", channel_kwargs=kwargs)

    @classmethod
    def parse(cls, channel: Union[str, bytes]) -> Dict[str, str]:
        """Extract keywork arguments from Redis channel

        Supports only the '*' glob pattern. Will parse any prefix

        Args:
            channel (Union[str, bytes]): Channel string

        Raises:
            ValueError: Message channel string does not match channel format

        Returns:
            Dict[str, str]: Channel keywork arguments
        """
        try:
            channel = channel.decode()
        except (UnicodeDecodeError, AttributeError):
            pass

        keywords = cls.default_channel_kwargs().keys()

        # Create capture groups from kwargs
        capture_groups = {k: "(?P<{}>[^:]*)".format(k) for k in keywords}
        channel_prefix = "[^:]*"
        pattern = (
            cls.channel(channel_prefix=channel_prefix, channel_kwargs=capture_groups)
            .replace(f"{channel_prefix}_", channel_prefix)
            .replace(":", ":?")
        )

        # Run match for kwargs
        matches = re.match(pattern, channel)

        if not matches:
            raise ValueError("Format string did not match")

        # Extract kwargs
        return {x: matches.group(x) or "*" for x in keywords}
