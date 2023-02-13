import { useMemo } from 'react';
import moment from 'moment';
import { useStatusQuery } from '../../redux/api';
import { Metric } from '../enums';

const useAgency = () => {
  const { data } = useStatusQuery();

  const availability = useMemo(
    () =>
      data?.availability
        ? {
            [Metric.ScheduleDeviation]: {
              min: moment(data.availability.schedule_deviation.min),
              max: moment(data.availability.schedule_deviation.max),
              isAvailable:
                data.availability.schedule_deviation.min ||
                data.availability.schedule_deviation.max,
            },
            [Metric.TravelTime]: {
              min: moment(data.availability.travel_time.min),
              max: moment(data.availability.travel_time.max),
              isAvailable:
                data.availability.travel_time.min ||
                data.availability.travel_time.max,
            },
          }
        : {
            [Metric.ScheduleDeviation]: {
              min: null,
              max: null,
            },
            [Metric.TravelTime]: {
              min: null,
              max: null,
            },
          },
    [data]
  );

  return { status: { availability }, isLoading: !data };
};

export default useAgency;
