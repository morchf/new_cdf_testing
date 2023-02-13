class Datum:
    def from_numeric(value, is_higher_better=False, precision=3):
        prev, curr = value
        is_not_none = curr is not None and prev is not None
        return {
            "change": round(curr - prev, precision) if is_not_none else None,
            "isBetter": (
                (curr > prev if is_higher_better else abs(curr) < abs(prev))
                if is_not_none
                else None
            ),
            "secs": curr if curr is not None else None,
            "percentage": round((curr - prev) / prev, precision)
            if is_not_none and prev
            else None,
        }

    def from_percent(value, is_higher_better=False, precision=3):
        prev, curr = value
        is_not_none = curr is not None and prev is not None
        return {
            "change": round(curr - prev, precision) if is_not_none else None,
            "isBetter": (
                (curr > prev if is_higher_better else abs(curr) < abs(prev))
                if is_not_none
                else None
            ),
            "percent": curr if curr is not None else None,
        }

    def from_summary(value, num, precision=3):
        return {
            "num": round(value, precision),
            "totalNum": int(num),
            "percentage": round(value / num, precision),
        }
