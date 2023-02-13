from typing import Optional

FROM_ENVIRONMENT_SHORT_NAME_MAP = {
    "dev": "develop",
    "prod": "production",
    "qa": "test",  # 'test' -> 'test' overrides 'test' -> 'qa'
    "test": "test",
    "pilot": "pilot",
}

TO_ENVIRONMENT_SHORT_NAME_MAP = dict(
    map(reversed, FROM_ENVIRONMENT_SHORT_NAME_MAP.items())
)


class Environment:
    def __init__(
        self, short_name: Optional[str] = None, long_name: Optional[str] = None
    ):
        assert short_name or long_name

        self._short_name = (
            short_name if short_name else TO_ENVIRONMENT_SHORT_NAME_MAP.get(long_name)
        )
        self._long_name = (
            long_name if long_name else FROM_ENVIRONMENT_SHORT_NAME_MAP.get(short_name)
        )

    @property
    def short_name(self) -> str:
        return self._short_name

    @property
    def long_name(self) -> str:
        return self._long_name
