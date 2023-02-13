-- agg_travel_time_per_route_stop_day
with --
     travel_time_source_data as (
         select *,
                $$LABEL                            as label,
                stopstart                          as stopstartname,
                stopend                            as stopendname,
                stopstartid                        as stopstart_id,
                stopendid                          as stopend_id,
                "date" AS eventdate
         from travel_time_source_data
         where agency = $AGENCY
           and "date" between $START_DATE and $END_DATE
           and route = $ROUTE
           and direction in $$SELECTED_DIRECTION
           and $$LABEL in $$SELECTED_TIMEPERIOD
     )
    select 
        stopstartname,
        stopendname,
        stopstart_id,
        stopend_id,        
        round(avg(stopstartlatitude), 5)   as stopstartlatitude,
        round(avg(stopstartlongitude), 5)  as stopstartlongitude,
        round(avg(stopendlatitude), 5)     as stopendlatitude,
        round(avg(stopendlongitude), 5)    as stopendlongitude,
        round(avg(dwelltime), 3)           as dwelltime,
        round(avg(traveltime), 3)          as traveltime,
        round(avg(drivetime), 3)           as drivetime,
        round(avg(signaldelay), 3)         as signaldelay,
        round(avg(tspsavings), 3)          as tspsavings,
        eventdate AS eventdate
    from travel_time_source_data
    group by eventdate, stopstartname, stopendname, stopstart_id, stopend_id,
    order by eventdate;