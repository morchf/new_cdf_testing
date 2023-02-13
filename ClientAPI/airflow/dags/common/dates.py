from typing import Optional
import json
import datetime


def parse_dates(date_range: Optional[str], date_pattern: Optional[str]) -> str:
    """
    Convert a date range or CSV of dates to an array of dates
    """
    dates = date_pattern[1:-1].split(",")

    try:
        [start_date, end_date] = [
            datetime.datetime.strptime(x, "%Y-%m-%d")
            for x in (
                json.loads(date_range) if isinstance(date_range, str) else date_range
            )
        ]

        assert start_date
        assert end_date
        assert start_date < end_date

        dates = [
            datetime.datetime.strftime(start_date + datetime.timedelta(n), "%Y-%m-%d")
            for n in range(int((end_date - start_date).days) + 1)
        ]

    except Exception:
        pass

    assert dates
    assert len(dates)

    return json.dumps(dates)
