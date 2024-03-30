/*
    Returns the integrated fuel consumption. Checks when assets were offline. Creates 0.0 data values for offline time slots
    @assets[uuid]: array of assets
    @param ts_min:
    @param ts_max:
    @time_bucket: bucket size that is used
    @offline_after: asset is offline if no signals reveived for this time duration

    Usage: SELECT * FROM fuel_consumption('{a718da95-5b41-450c-beda-88a0f4d8491a,746252f0-b478-4b62-9a9b-ac2adb4e4140}','5 minutes','15 minutes','2020-10-09T10:23:34.197Z','2021-02-09T10:23:34.197Z')

    Improvements: - This function currently creates buckets on the fly. Doesn't use pre calculated buckets
*/ 

CREATE OR REPLACE FUNCTION fuel_consumption(_assets uuid[], _time_bucket INTERVAL, _offline_after INTERVAL, _ts_min TIMESTAMP WITHOUT TIME ZONE, _ts_max TIMESTAMP WITHOUT TIME ZONE)
RETURNS TABLE
(
    asset_id uuid,
    bucket TIMESTAMP WITHOUT TIME ZONE,
    data float8
)
LANGUAGE SQL STABLE
AS $$ 
   SELECT asset_id, bucket_filled, sum(data * EXTRACT(EPOCH FROM _time_bucket)/3600) OVER (PARTITION BY asset_id ORDER BY bucket_filled) FROM( --cast INTERVAL to seconds, then to hours
        WITH my_series AS
                     ( -- create a series of 0.0 values for all buckets where asset is offline
                             SELECT asset_id, 0.0 AS data, series AS bucket   
                                     FROM(
                                             SELECT asset_id, offline_from, offline_to 
                                             FROM asset_offline(_assets,_offline_after,_ts_min,_ts_max)
                                         )sub0, LATERAL generate_series(offline_from,offline_to, _time_bucket)series
                             GROUP BY asset_id,bucket
                             ORDER BY bucket
                     ),

             fuelrate AS( --get fuelrate in buckets
                             SELECT asset AS asset_id, avg(data) as data, time_bucket_gapfill(_time_bucket, time_utc) AS bucket
                             FROM data_raw.powertrain__engine_fuelrate 
                             WHERE asset = ANY(_assets) AND time_utc BETWEEN _ts_min AND _ts_max
                             GROUP BY bucket, asset
                         )
        --And now we combine the two queries from above and make gapfilling for missing buckets, this should only be gaps < _offline_after
        SELECT asset_id, time_bucket_gapfill(_time_bucket,bucket) AS "bucket_filled",locf(avg(data)) AS data FROM(
             SELECT asset_id, bucket, data FROM my_series WHERE data IS NOT NULL
             UNION ALL
             SELECT asset_id, bucket, data FROM fuelrate 
             ORDER BY bucket 
         )sub1
         WHERE sub1.bucket BETWEEN _ts_min AND _ts_max
         GROUP BY asset_id, bucket_filled 
   )sub2
$$;

/*
    Simple Integration without gapfilling
*/
SELECT sum(value * 1/60) OVER (PARTITION BY asset ORDER BY time), time, '1 min' as meta FROM (
SELECT time_bucket_gapfill('1 minutes', time_utc) AS time,
        asset::varchar,
        avg(data) AS value
FROM data_raw.powertrain__engine_fuelrate
WHERE asset IN ($pump_uuid) AND
$__timeFilter(time_utc)
GROUP BY time, asset
ORDER BY time
)sub0

/*
    Simple Integration with gapfilling
*/
SELECT time, asset, sum(value * 2/60) OVER (PARTITION BY asset ORDER BY time), time FROM (
    SELECT time_bucket_gapfill('2 minutes', time_utc) AS time,
            asset,
            locf(avg(data)) AS value
    FROM data_raw.powertrain__engine_fuelrate
    WHERE asset IN ('5ec826dd-f449-4def-834d-7239cde0439b') AND
    time_utc BETWEEN '2021-02-25T01:25:18.39Z' AND '2021-03-04T03:37:10.013Z'
    GROUP BY time, asset
    ORDER BY time
    )sub0
