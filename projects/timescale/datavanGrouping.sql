
/**
* Calculate the "online" time slots for each asset at fatnode @fatnode_id between a time range.
*
* NOTE:This query considers buckets of 15 minutes
*
* Usage: SELECT * FROM getAssetsFromFatnode('4','1 hour','2020-01-01T19:02:13.597Z','2021-03-10T15:34:41.135Z');
*
* @param fatnode_id 	the source uuid from fatnode
* @time_bucket      
* @param ts_min		the timestamp of the start of the time range
* @param ts_max		the timestamp of the end of the time range
*/
CREATE OR REPLACE FUNCTION getAssetsFromFatnode(fatnode_id bigint, time_bucket INTERVAL, ts_min TIMESTAMP WITHOUT TIME ZONE, ts_max TIMESTAMP WITHOUT TIME ZONE)
RETURNS TABLE
(
    asset_id uuid,
    source_id bigint,
    ts_from TIMESTAMP WITHOUT TIME ZONE,
    ts_to TIMESTAMP WITHOUT TIME ZONE
)
LANGUAGE PLPGSQL
AS $$
 
BEGIN
    
    RETURN QUERY
    SELECT asset,meta_source, _from,_to
    FROM(
        SELECT asset,meta_source,
            CASE WHEN new_start IS NULL THEN lag(new_start) OVER (PARTITION BY asset ORDER BY bucket) ELSE new_start END AS _from,
            CASE WHEN new_end IS NULL THEN lead(new_end) OVER (PARTITION BY asset ORDER BY bucket) ELSE new_end END AS _to
        FROM(
            SELECT asset,meta_source,bucket,
                    CASE WHEN before_data IS NULL OR(before_source != meta_source AND min_ts IS NOT NULL) THEN min_ts ELSE NULL END AS new_start,
                    CASE WHEN after_data IS NULL OR(after_source != meta_source AND min_ts IS NOT NULL) THEN max_ts ELSE NULL END AS new_end
            FROM(
                SELECT asset,meta_source,bucket,before_data,after_data,before_source,after_source,min_ts,max_ts
                FROM
                    (SELECT asset,meta_source,gap_bucket AS bucket, min_ts, max_ts,
                            lag(min_ts) OVER (PARTITION BY asset,meta_source ORDER BY gap_bucket) AS before_data,
                            lead(min_ts) OVER (PARTITION BY asset,meta_source ORDER BY gap_bucket) AS after_data,
                            lag(meta_source) OVER (PARTITION BY asset,meta_source ORDER BY gap_bucket) AS before_source,
                            lead(meta_source) OVER (PARTITION BY asset,meta_source ORDER BY gap_bucket) AS after_source     
                        FROM(
                            SELECT  asset,meta_source,time_bucket_gapfill(time_bucket, time_utc)AS gap_bucket, min(time_utc) AS min_ts, max(time_utc) AS max_ts
                            FROM data_raw.oilandgas__frac_pump_oph_esc_mode_active
                            WHERE meta_source = fatnode_id AND time_utc BETWEEN ts_min AND ts_max
                            GROUP BY asset,meta_source,gap_bucket
                            ORDER BY gap_bucket ASC
                        )sub0
                    )sub1
                WHERE min_ts IS NOT NULL AND (before_data IS NULL OR after_data IS NULL OR before_source != meta_source OR after_source != meta_source) 
                )sub2
            )sub3
        )sub4
    GROUP BY asset,meta_source,_from, _to
    ORDER BY asset,_from;  
END
$$;

/*
*   Calculate the oph deltas for the time slots from the function from above
*/
SELECT dv.asset_id, dv.source_id, dv.ts_from, dv.ts_to,
        esc_active_max.max - esc_active_min.min AS delta_esc_active, esc_cond_max.max - esc_cond_min.min AS delta_esc_cond,esc_engine_max.max - esc_engine_min.min AS delta_esc_engine,esc_nonpumping_max.max - esc_nonpumping_min.min AS delta_esc_nonpumping,esc_pumping_max.max - esc_pumping_min.min AS delta_esc_pumping,esc_ready_max.max - esc_ready_min.min AS delta_esc_ready
        man_active_max.max - man_active_min.min AS delta_man_active, man_cond_max.max - man_cond_min.min AS delta_man_cond,man_engine_max.max - man_engine_min.min AS delta_man_engine,man_nonpumping_max.max - man_nonpumping_min.min AS delta_man_nonpumping,man_pumping_max.max - man_pumping_min.min AS delta_man_pumping,man_ready_max.max - man_ready_min.min AS delta_man_ready

FROM (SELECT * FROM getAssetsFromFatnode('11','1 hour','2020-09-01T19:02:13.597Z','2021-03-10T15:34:41.135Z'))dv
INNER JOIN data_1hour.oilandgas__frac_pump_oph_esc_mode_active esc_active_min ON dv.asset_id = esc_active_min.asset AND dv.ts_from = esc_active_min.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_esc_mode_active esc_active_max ON dv.asset_id = esc_active_max.asset AND dv.ts_to = esc_active_max.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_esc_mode_conditioning esc_cond_min ON dv.asset_id = esc_cond_min.asset AND dv.ts_from = esc_cond_min.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_esc_mode_conditioning esc_cond_max ON dv.asset_id = esc_cond_max.asset AND dv.ts_to = esc_cond_max.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_esc_mode_engine esc_engine_min ON dv.asset_id = esc_engine_min.asset AND dv.ts_from = esc_engine_min.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_esc_mode_engine esc_engine_max ON dv.asset_id = esc_engine_max.asset AND dv.ts_to = esc_engine_max.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_esc_mode_nonpumping esc_nonpumping_min ON dv.asset_id = esc_nonpumping_min.asset AND dv.ts_from = esc_nonpumping_min.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_esc_mode_nonpumping esc_nonpumping_max ON dv.asset_id = esc_nonpumping_max.asset AND dv.ts_to = esc_nonpumping_max.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_esc_mode_pumping esc_pumping_min ON dv.asset_id = esc_pumping_min.asset AND dv.ts_from = esc_pumping_min.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_esc_mode_pumping esc_pumping_max ON dv.asset_id = esc_pumping_max.asset AND dv.ts_to = esc_pumping_max.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_esc_mode_ready esc_ready_min ON dv.asset_id = esc_ready_min.asset AND dv.ts_from = esc_ready_min.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_esc_mode_ready esc_ready_max ON dv.asset_id = esc_ready_max.asset AND dv.ts_to = esc_ready_max.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_manual_mode_active man_active_min ON dv.asset_id = man_active_min.asset AND dv.ts_from = man_active_min.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_manual_mode_active man_active_max ON dv.asset_id = man_active_max.asset AND dv.ts_to = man_active_max.bucket
--INNER JOIN data_1hour.oilandgas__frac_pump_oph_manual_mode_conditioning man_cond_min ON dv.asset_id = man_cond_min.asset AND dv.ts_from = man_cond_min.bucket
--INNER JOIN data_1hour.oilandgas__frac_pump_oph_manual_mode_conditioning man_cond_max ON dv.asset_id = man_cond_max.asset AND dv.ts_to = man_cond_max.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_manual_mode_engine man_engine_min ON dv.asset_id = man_engine_min.asset AND dv.ts_from = man_engine_min.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_manual_mode_engine man_engine_max ON dv.asset_id = man_engine_max.asset AND dv.ts_to = man_engine_max.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_manual_mode_nonpumping man_nonpumping_min ON dv.asset_id = man_nonpumping_min.asset AND dv.ts_from = man_nonpumping_min.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_manual_mode_nonpumping man_nonpumping_max ON dv.asset_id = man_nonpumping_max.asset AND dv.ts_to = man_nonpumping_max.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_manual_mode_pumping man_pumping_min ON dv.asset_id = man_pumping_min.asset AND dv.ts_from = man_pumping_min.bucket
INNER JOIN data_1hour.oilandgas__frac_pump_oph_manual_mode_pumping man_pumping_max ON dv.asset_id = man_pumping_max.asset AND dv.ts_to = man_pumping_max.bucket

