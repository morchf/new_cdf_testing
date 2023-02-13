class Metric:
    FIELD_NAMES_MAP = {
        "ontime": "onTime",
        "ontimepercentage": "onTimePercentage",
        "earlypercentage": "earlyPercentage",
        "latepercentage": "latePercentage",
        "avgdeviation": "avgDeviation",
        "scheduledeviation": "scheduleDeviation",
        "avgscheduledeviation": "avgScheduleDeviation",
    }

    def __map_item_fields(item):
        if not item:
            return None

        mapped_item = {}

        for key, value in item.items():
            if key in Metric.FIELD_NAMES_MAP:
                mapped_item[Metric.FIELD_NAMES_MAP[key]] = value
            else:
                mapped_item[key] = value

        return mapped_item

    def map_fields(items):
        if not items or len(items) == 0:
            return []

        return list(map(Metric.__map_item_fields, items))
