/* This query assumes that the data is already filtered so that there is only one unique pass for every combination of Intersection (locationname) and
Vehicle (id).  It filters these unique passes to one single row and gives statistics on specific fields, such as:
- First time the vehicle was seen by the intersection
- Last time the vehicle was seen by the intersection
- Maximum of caused preempt (did it successfully request at any point during the pass)
*/
WITH t as (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY "locationname", "id" ORDER BY "startdatetime") as record_num
  FROM "retrieveopticomlogsdb"."opticomlogsdata"
),
firstrow as (
  SELECT locationname, id, startdatetime as firststartdatetime
  FROM t
  WHERE record_num = 1
),
lastrow as (
  SELECT t.locationname, t.id, startdatetime as laststartdatetime
  FROM t JOIN (
    SELECT locationname, id, MAX(record_num) as lastindex
    FROM t
    GROUP BY locationname, id
  ) AS a ON t.locationname = a.locationname and t.id = a.id
  WHERE record_num = lastindex
),
accrossallrows as (
  SELECT locationname, id, MAX(causedpreempt) as maxcausedpreempt
  FROM t
  GROUP BY locationname, id
)
SELECT firstrow.locationname, firstrow.id, firststartdatetime, laststartdatetime, maxcausedpreempt
FROM firstrow
  JOIN lastrow ON firstrow.locationname = lastrow.locationname AND firstrow.id = lastrow.id
  JOIN accrossallrows ON firstrow.locationname = accrossallrows.locationname AND firstrow.id = accrossallrows.id
