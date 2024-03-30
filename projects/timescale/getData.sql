
/*
These 2 functions return the types, assets, data which are defined in the json input parameter for the function


We are using function overloading:
Version 1: for RAW data
    getData(config jsonb) --> Usage: SELECT * FROM getData('{"bucket":"default","assets":"(''746252f0-b478-4b62-9a9b-ac2adb4e4140'',''289e5edd-0fb2-4dd8-b853-b4fb1d09c04b'')","types":"(''powertrain__engine_fuelrate'',''powertrain__engine_speed_rpm'')","timeTo":"2021-11-16T10:40:31.461Z","timeFrom":"2020-11-13T10:41:31.461Z"}');

Version 2: for time_buckets
    Predefined values for bucket: 'default', '5 minutes', '1 hour'
    If 'default' is set the function decides which bucket type is used based on time frame range of timeTo - timeFrom
    getData(bucket VARCHAR, config jsonb) --> Usage: SELECT * FROM getData('5 minutes', '{"assets":"(''746252f0-b478-4b62-9a9b-ac2adb4e4140'',''289e5edd-0fb2-4dd8-b853-b4fb1d09c04b'')","types":"(''powertrain__engine_fuelrate'',''powertrain__engine_speed_rpm'')","timeTo":"2021-11-16T10:40:31.461Z","timeFrom":"2020-11-13T10:41:31.461Z"}')



How it is currently implemented
Usage: SELECT * FROM getData('{"bucket":"default","assets":"(''746252f0-b478-4b62-9a9b-ac2adb4e4140'',''289e5edd-0fb2-4dd8-b853-b4fb1d09c04b'')","types":"(''powertrain__engine_fuelrate'',''powertrain__engine_speed_rpm'')","timeTo":"2021-11-16T10:40:31.461Z","timeFrom":"2020-11-13T10:41:31.461Z"}');
Sample jsonb: '{"bucket":"default","assets":"(''746252f0-b478-4b62-9a9b-ac2adb4e4140'',''289e5edd-0fb2-4dd8-b853-b4fb1d09c04b'')","types":"(''powertrain__engine_fuelrate'',''powertrain__engine_speed_rpm'')","timeTo":"2021-11-16T10:40:31.461Z","timeFrom":"2020-11-13T10:41:31.461Z","time_bucket_gapfill":"TRUE","gapfill":"$gapfill"}'

Grafana Query:
SELECT bucket AS time,type as METRIC,avg FROM getData('{"bucket":"$bucket","assets":"(${assets_uuid_json:raw})","types":"(${signal:raw})","timeTo":"${__to:date}","timeFrom":"${__from:date}","time_bucket_gapfill":"$time_bucket_gapfill","gapfill":"$gapfill"}')
WHERE $__timeFilter(bucket)
ORDER BY bucket
*/



-- instead of RETURNS table we could use returns setof RECORDS
CREATE OR REPLACE FUNCTION getData(config jsonb) 
RETURNS TABLE 
(
    asset uuid,
    type VARCHAR(100),
    bucket TIMESTAMP WITHOUT TIME ZONE,
    avg float8
)
LANGUAGE PLPGSQL 
AS $$
DECLARE
    _bucket TEXT;
    _assets TEXT;
    _types TEXT;
    _timeFrom timestamp;
    _timeTo timestamp;
    _time_bucket_gapfill BOOLEAN;
    _gapfill_function TEXT;

    _tablename VARCHAR;
    _bucketname VARCHAR;
BEGIN
    --RAISE NOTICE 'Executing getData() with config %', config;
    SELECT jsonb_object_field_text (config, 'bucket')::TEXT INTO STRICT _bucket;
    SELECT jsonb_object_field_text (config, 'assets')::TEXT INTO STRICT _assets;
    SELECT jsonb_object_field_text (config, 'types')::TEXT INTO STRICT _types;
    SELECT jsonb_object_field_text (config, 'timeFrom')::TIMESTAMP INTO STRICT _timeFrom;
    SELECT jsonb_object_field_text (config, 'timeTo')::TIMESTAMP INTO STRICT _timeTo;
    SELECT jsonb_object_field_text (config, 'time_bucket_gapfill')::BOOLEAN INTO STRICT _time_bucket_gapfill;
    SELECT jsonb_object_field_text (config, 'gapfill')::TEXT INTO STRICT _gapfill_function;


    -- set table to select from
    IF (_bucket = '5 minutes' ) THEN _tablename := 'ts.data_float8_5minutes';
                                    _bucketname :='_5minutes';
    ELSEIF (_bucket = '1 hour') THEN _tablename := 'ts.data_float8_hourly';
                                     _bucketname :='_hourly';
    ELSEIF (_bucket = 'default') THEN
        IF (_timeTo - _timeFrom > '14 days'::INTERVAL) THEN _tablename := 'ts.data_float8_hourly'; _bucketname :='_hourly'; _bucket := '1 hour';
        ELSEIF (_timeTo - _timeFrom BETWEEN '3 days'::INTERVAL AND '14 days'::INTERVAL) THEN _tablename := 'ts.data_float8_5minutes'; _bucketname :='_5minutes';_bucket := '5 minutes';
        ELSEIF (_timeTo - _timeFrom < '3 days'::INTERVAL) THEN _tablename := 'ts.data_float8_5minutes'; _bucketname :='_5minutes';_bucket := '5 minutes';
        END IF;
    END IF;

    /*
    RAISE NOTICE '_assets: %', _assets;
    RAISE NOTICE '_types: %', _types;
    RAISE NOTICE '_timeFrom: %', _timeFrom;
    RAISE NOTICE '_timeTo: %', _timeTo;
    RAISE NOTICE 'interval _timeTo - _timeFrom: %', (_timeTo - _timeFrom)::INTERVAL;
    RAISE NOTICE '_tablename: %', _tablename;
    RAISE NOTICE '_bucketname: %', _bucketname;
    */
    IF (_time_bucket_gapfill = FALSE) THEN
        RETURN QUERY EXECUTE FORMAT (
        'SELECT asset, CONCAT(type,%L)::VARCHAR, bucket, data
         FROM %s
         WHERE asset IN %s AND type IN %s AND bucket BETWEEN %L AND %L' 
        , _bucketname, _tablename,_assets,_types,_timeFrom,_timeTo);
    ELSEIF (_time_bucket_gapfill = TRUE) THEN
        RETURN QUERY EXECUTE FORMAT (
            'SELECT asset, CONCAT(type,%L)::VARCHAR, time_bucket_gapfill(%L,bucket)AS time_bucket, %s(avg(data))
             FROM %s
             WHERE asset IN %s AND type IN %s AND bucket BETWEEN %L AND %L 
             GROUP BY time_bucket,asset,type 
             ORDER BY time_bucket'
            , _bucketname,_bucket, _gapfill_function, _tablename, _assets,_types, _timeFrom, _timeTo);
    END IF;         
END
$$;
/*
 * getdata() for one table per signal type
*/
SELECT * FROM getData('{"bucket":"default","assets": ["746252f0-b478-4b62-9a9b-ac2adb4e4140","289e5edd-0fb2-4dd8-b853-b4fb1d09c04b"],"types": ["oilandgas__fracpump__oph__escmode_active"],"timeTo":"2021-11-16T10:40:31.461Z","timeFrom":"2020-11-13T10:41:31.461Z","time_bucket_gapfill":"TRUE","gapfill":"interpolate"}');
CREATE OR REPLACE FUNCTION getData(config jsonb) 
RETURNS TABLE 
(
    asset uuid,
    type text,
    bucket TIMESTAMP WITHOUT TIME ZONE,
    avg float8,
    max float8,
    min float8,
    count bigint,
    first_value float8,
    last_value float8,
    stddev float8,
    first_time_utc TIMESTAMP WITHOUT TIME ZONE,
    last_time_utc TIMESTAMP WITHOUT TIME ZONE
)
LANGUAGE PLPGSQL 
AS $$
DECLARE
    _bucket TEXT; --catch wrong buckets
    _assets uuid[]; --use array of uuids -> better for sql injection
    _types text[]; 
    _timeFrom timestamp;
    _timeTo timestamp;
    _time_bucket_gapfill BOOLEAN;
    _gapfill_function TEXT;

    _schemaname VARCHAR;
    _rec RECORD;
    _cnt INT;
    _strSQL TEXT; -- sql query that will be executed
BEGIN
    
    SELECT jsonb_object_field_text (config, 'bucket')::TEXT INTO STRICT _bucket;
    SELECT ARRAY(SELECT jsonb_array_elements_text(config->'assets')::uuid) INTO STRICT _assets;
    SELECT ARRAY(SELECT jsonb_array_elements_text(config->'types')) INTO STRICT _types;
    SELECT jsonb_object_field_text (config, 'timeFrom')::TIMESTAMP INTO STRICT _timeFrom;
    SELECT jsonb_object_field_text (config, 'timeTo')::TIMESTAMP INTO STRICT _timeTo;
    SELECT jsonb_object_field_text (config, 'time_bucket_gapfill')::BOOLEAN INTO STRICT _time_bucket_gapfill;
    SELECT jsonb_object_field_text (config, 'gapfill')::TEXT INTO STRICT _gapfill_function;
    _strSQL = '';
    _cnt := 1;
    RAISE NOTICE 'array types %', _types;

--
    -- set schema to select from
    IF (_bucket = '5 minutes' ) THEN _schemaname := 'data_5min';
    ELSEIF (_bucket = '15 minutes') THEN _schemaname := 'data_15min';
    ELSEIF (_bucket = '1 hour') THEN _schemaname := 'data_1hour';
    ELSEIF (_bucket = '1 day') THEN _schemaname := 'data_1day';
    ELSEIF (_bucket = 'default') THEN
        IF (_timeTo - _timeFrom > '14 days'::INTERVAL) THEN _schemaname := 'data_1hour'; _bucket = ' 1 hour'; 
            ELSEIF (_timeTo - _timeFrom BETWEEN '3 days'::INTERVAL AND '14 days'::INTERVAL) THEN _schemaname := 'data_5min';
            ELSEIF (_timeTo - _timeFrom < '3 days'::INTERVAL) THEN _schemaname := 'data_5min';
        END IF;
    END IF;

    -- make query:

    IF (_time_bucket_gapfill = 'FALSE') THEN
        FOR _rec IN SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = _schemaname AND table_name = ANY(_types) LOOP -- select from information_schema to avoid SQL-Injection
            _strSQL :=_strSQL || 'SELECT asset, ''' || _rec.table_name || ''' AS type, bucket, avg, max, min, count, first_value, last_value, stddev, first_time_utc, last_time_utc FROM '|| CONCAT(_rec.table_schema,'.', _rec.table_name) || ' WHERE asset IN(''' ||array_to_string(_assets, ''',''')||''') AND ' || 'bucket BETWEEN ''' || _timeFrom || ''' AND ''' || _timeTo ||'''';
            IF(_cnt < array_upper(_types,1)) THEN -- add UNION ALL
                _strSQL := _strSQL || ' UNION ALL ';
            END IF;
            _cnt = _cnt + 1;
        END LOOP;

    ELSEIF (_time_bucket_gapfill = 'TRUE') THEN
        FOR _rec IN SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = _schemaname AND table_name = ANY(_types) LOOP -- select from information_schema to avoid SQL-Injection
            _strSQL :=_strSQL || 'SELECT asset, ''' || _rec.table_name || ''' AS type, time_bucket_gapfill('''|| _bucket ||''',bucket) AS time_bucket,';
            IF(_gapfill_function = 'locf') THEN
                _strSQL := _strSQL || 'locf(avg), locf(max), locf(min), locf(count), locf(first_value), locf(last_value), locf(stddev),locf(first_time_utc), locf(last_time_utc) FROM ';
            ELSEIF (_gapfill_function = 'interpolate') THEN
                _strSQL := _strSQL || 'interpolate(avg), interpolate(max), interpolate(min), interpolate(count), interpolate(first_value), interpolate(last_value), interpolate(stddev),first_time_utc,last_time_utc FROM ';
            END IF;
            _strSQL := _strSQL || CONCAT(_rec.table_schema,'.', _rec.table_name) || ' WHERE asset IN(''' ||array_to_string(_assets, ''',''')||''') AND ' || 'bucket BETWEEN ''' || _timeFrom || ''' AND ''' || _timeTo ||'''';
            IF(_cnt < array_upper(_types,1)) THEN -- add UNION ALL
                _strSQL := _strSQL || ' UNION ALL ';
            END IF;
            _cnt = _cnt + 1;
        END LOOP;
        --_strSQL := _strSQL || ' GROUP BY time_bucket,asset'; -> is Group by needed for gapfill ?? 
    END IF;
    --add ORDER BY
    _strSQL := _strSQL || ' ORDER BY 1';
    
    RAISE DEBUG 'query %',_strSQL;
    RETURN QUERY EXECUTE _strSQL;
END
$$;
