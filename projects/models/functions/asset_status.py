from alembic_utils.pg_function import PGFunction

# asset_online
# Returns the online time slots of the input assets
# - currently the "data_raw.oilandgas__frac_pump_oph_esc_mode_active" signal is used to check if an asset is online
# @assets[uuid]: array of assets
# @param ts_min:
# @param ts_max:
# @time_bucket: bucket size that is used
# 
# Usage: SELECT * FROM asset_online('{a9d22a28-699c-4644-a3f7-167c38f3c8b6,289e5edd-0fb2-4dd8-b853-b4fb1d09c04b}','5 minutes','2020-10-09T10:23:34.197Z','2021-02-09T10:23:34.197Z')


# INFO:

# if we move to plpgsql function use this format: https://stackoverflow.com/questions/10705616/table-name-as-a-postgresql-function-parameter

asset_online = PGFunction(
    schema='public',
    signature='asset_online(_assets uuid[], _time_bucket INTERVAL, _ts_min TIMESTAMP WITHOUT TIME ZONE, _ts_max TIMESTAMP WITHOUT TIME ZONE)',
    definition="""
    RETURNS TABLE
    (
        asset_id uuid,
        online_from TIMESTAMP WITHOUT TIME ZONE,
        online_to TIMESTAMP WITHOUT TIME ZONE
    )
    LANGUAGE SQL STABLE
    AS $$ 
        SELECT asset,_from,_to
            FROM(
                SELECT asset,new_start,new_end,
                    CASE WHEN new_start IS NULL THEN lag(new_start) OVER (PARTITION BY asset ORDER BY bucket) ELSE new_start END AS _from,
                    CASE WHEN new_end IS NULL THEN lead(new_end) OVER (PARTITION BY asset ORDER BY bucket) ELSE new_end END AS _to
                FROM(
                    SELECT asset,bucket,data,before_data,after_data,
                            CASE WHEN before_data IS NULL THEN bucket ELSE NULL END AS new_start,
                            CASE WHEN after_data IS NULL THEN bucket ELSE NULL END AS new_end
                    FROM(
                        SELECT asset,gap_bucket AS bucket,data,
                                lag(data) OVER (PARTITION BY asset ORDER BY gap_bucket) AS before_data,
                                lead(data) OVER (PARTITION BY asset ORDER BY gap_bucket) AS after_data
                        FROM(
                            SELECT asset,time_bucket_gapfill(_time_bucket, time_utc)AS gap_bucket, count(data)AS data
                            FROM data_raw.oilandgas__frac_pump_oph_esc_mode_active
                            WHERE   
                                asset = ANY(_assets) AND time_utc BETWEEN _ts_min AND _ts_max
                            GROUP BY asset,gap_bucket
                            ORDER BY gap_bucket ASC
                            )sub0
                        )sub1
                    WHERE data IS NOT NULL AND (before_data IS NULL OR after_data IS NULL) 
                )sub3
            )sub4
        GROUP BY asset,_from, _to
        ORDER BY asset,_from
    $$;
    """
)

#    Returns the offline time slots of the input assets. This function is based on the asset_online() function
#    @assets[uuid]: array of assets
#    @param ts_min:
#    @param ts_max:
#    @time_bucket: bucket size that is used
#
#    Usage: SELECT * FROM asset_offline('{a9d22a28-699c-4644-a3f7-167c38f3c8b6,289e5edd-0fb2-4dd8-b853-b4fb1d09c04b}','5 minutes','2020-10-09T10:23:34.197Z','2021-02-09T10:23:34.197Z')
asset_offline = PGFunction(
    schema='public',
    signature='asset_offline(_assets uuid[], _time_bucket INTERVAL, _ts_min TIMESTAMP WITHOUT TIME ZONE, _ts_max TIMESTAMP WITHOUT TIME ZONE)',
    definition="""
    RETURNS TABLE
    (
        asset_id uuid,  
        offline_from TIMESTAMP WITHOUT TIME ZONE,
        offline_to TIMESTAMP WITHOUT TIME ZONE
    )
    LANGUAGE SQL STABLE
    AS $$ 
        SELECT asset_id, online_to AS off_From,
        COALESCE(lead(online_from) OVER (PARTITION BY asset_id ORDER BY online_from),_ts_max) AS off_To -- if online_to is NULL then replace it with _ts_max
        FROM (
                SELECT * FROM asset_online(_assets,_time_bucket,_ts_min,_ts_max)
        )sub0
    $$;
    """
)