/* Useful to test syncing:
    echo "CREATE TEMP TABLE temp(uuid uuid NOT NULL);
    \COPY temp FROM '/home/AD.EKUPD.COM/matthias.epple/Desktop/source-UUID_run3_TN0001001CE9D6_69003045-8779-4b49-82c5-086153b5ada3_2020-12-08_17-07';
    UPDATE data SET source = '69003045-8779-4b49-82c5-086153b5ada3' WHERE uuid IN (SELECT * FROM temp)" | psql -h localhost -U ekupd__matthias_epple profrac_data_27_10_20
*/


/*
##################################################      This function is for 1 table per base datatype (float, varchar) ################################################
*/
CREATE OR REPLACE PROCEDURE ts_sync_action()
LANGUAGE plpgsql
AS
$$
DECLARE 
    temprow RECORD;
    cnt int:=1;
    arr_value VARCHAR;
    start_time timestamptz := clock_timestamp();

BEGIN
    CREATE TEMP TABLE temp( --copy of data table
      uuid uuid,
      time_utc timestamp without time zone,
      time_mono bigint,
      rcvtime_utc timestamp without time zone,
      rcvtime_mono bigint NOT NULL,
      source uuid NOT NULL,
      asset uuid,
      rcvnode uuid,
      type VARCHAR(100),
      data jsonb,
      validated boolean NOT NULL);
    -- sync all inserts
    RAISE INFO '############################################################# sync INSERTS ######################################';

    FOR temprow IN SELECT typename, keys, newtypenames,datatypes FROM timescale_types ORDER BY typename LOOP --iterate over each old signaltype 
        RAISE INFO 'sync INSERTS for %', temprow.typename;
        EXECUTE format('INSERT INTO temp SELECT * FROM foreign_data  WHERE uuid IN (SELECT row FROM foreign_timescale_sync ts WHERE ts.synced=FALSE AND operation=''INSERT'' AND ts.type=%L )',temprow.typename);
        
        FOREACH arr_value IN ARRAY temprow.Keys LOOP--iterate over each key
            EXECUTE format(
                'INSERT INTO ts.data_%s(time_utc, time_mono,rcvtime_utc, rcvtime_mono,source,asset,rcvnode, data, validated,type, uuid_original)
                 SELECT time_utc, time_mono,rcvtime_utc, rcvtime_mono,source,asset,rcvnode, (data->''%I''->>''value'')::%s AS value, validated, %L, uuid FROM temp'
                ,temprow.datatypes[cnt], arr_value, temprow.datatypes[cnt],temprow.newtypenames[cnt]
            );
            Raise INFO 'synced % : total time spent=%', temprow.newtypenames[cnt], clock_timestamp() - start_time;        
            cnt:=cnt +1;
        END LOOP;
        cnt:=1;
        EXECUTE format('UPDATE foreign_timescale_sync SET synced = TRUE, host = ''ts.data'' WHERE synced=FALSE AND operation=''INSERT'' AND type=%L',temprow.typename); -- mark as synced
        --TRUNCATE TABLE temp;
        DELETE FROM temp;
        RAISE INFO 'All signals from datatype % are synced now',temprow.typename;
        --COMMIT;--Commit changes to database
    END LOOP;

    ----sync all updates
    DROP TABLE temp;
     CREATE TEMP TABLE temp( --copy of data table
      uuid uuid,
      time_utc timestamp without time zone,
      time_mono bigint,
      rcvtime_utc timestamp without time zone,
      rcvtime_mono bigint NOT NULL,
      source uuid NOT NULL,
      asset uuid,
      rcvnode uuid,
      type VARCHAR(100),
      data jsonb,
      validated boolean NOT NULL);
    --RAISE INFO '############################################################# sync UPDATES ######################################';
--
    --FOR temprow IN SELECT typename, keys, newtypenames,datatypes FROM timescale_types ORDER BY typename LOOP 
    --    RAISE INFO 'sync UPDATES for %', temprow.newtypenames[cnt];
    --    EXECUTE format('INSERT INTO temp SELECT * FROM foreign_data  WHERE uuid IN (SELECT row FROM foreign_timescale_sync ts WHERE ts.synced=FALSE AND operation=''UPDATE'' AND ts.type=%L )',temprow.typename);
--
    --    FOREACH arr_value IN ARRAY temprow.Keys LOOP
    --        EXECUTE format(
    --            'UPDATE ts.data_%s 
    --             SET uuid =subquery.uuid, time_utc =subquery.time_utc, time_mono =subquery.time_mono, rcvtime_utc =subquery.rcvtime_utc, rcvtime_mono =subquery.rcvtime_mono,source =subquery.source,asset =subquery.asset ,rcvnode =subquery.rcvnode, data =subquery.value, validated =subquery.validated, uuid_original =subquery.uuid
    --             FROM (SELECT uuid,time_utc, time_mono,rcvtime_utc, rcvtime_mono,source,asset,rcvnode, (data->''%I''->>''value'')::%s AS value, validated FROM temp)AS subquery
    --             WHERE ts.data_%s.uuid_original = subquery.uuid AND ts.data_%s.type =%L'
    --            ,temprow.datatypes[cnt], arr_value, temprow.datatypes[cnt],temprow.datatypes[cnt],temprow.datatypes[cnt],temprow.newtypenames[cnt]
    --        );
    --        Raise INFO 'synced % : total time spent=%', temprow.newtypenames[cnt], clock_timestamp() - start_time;        
    --        cnt:=cnt +1;
--
    --    END LOOP;
    --    cnt:=1;
    --    EXECUTE format('UPDATE foreign_timescale_sync SET synced = TRUE, host = ''ts.data'' WHERE synced=FALSE AND operation=''UPDATE'' AND type=%L',temprow.typename); -- mark as synced
    --    RAISE INFO 'All signals from datatype % are synced now',temprow.typename;
    --    DELETE FROM temp;
    --    --COMMIT;--Commit changes to database
    --END LOOP;

    --DELETE FROM temp;
    ----sync all DELETES
    --RAISE INFO '############################################################# sync DELETES ######################################';
    --CREATE TEMP TABLE tempDeletes(uuid uuid);
    --FOR temprow IN SELECT typename, keys, newtypenames,datatypes FROM timescale_types ORDER BY typename LOOP
    --    RAISE INFO 'sync DELETES for %', temprow.newtypenames[cnt];
    --    EXECUTE format('INSERT INTO tempDeletes SELECT row FROM foreign_timescale_sync ts WHERE ts.synced=FALSE AND operation=''DELETE'' AND ts.type=%L',temprow.typename);
--
    --    FOREACH arr_value IN ARRAY temprow.Keys LOOP
    --        EXECUTE format(
    --            'DELETE FROM ts.data_%s WHERE uuid_original IN (SELECT * FROM tempDeletes)' --this is now deleting too often, but that should be OK for first
    --            ,temprow.datatypes[cnt],temprow.typename);
    --        Raise INFO 'deleted % : total time spent=%', temprow.newtypenames[cnt], clock_timestamp() - start_time;        
    --        cnt:=cnt +1;
    --    END LOOP;
    --    cnt:=1;
    --    EXECUTE format('UPDATE foreign_timescale_sync SET synced = TRUE, host = ''ts.data'' WHERE synced=FALSE AND operation=''DELETE'' AND type=%L',temprow.typename); -- mark as synced
    --    RAISE INFO 'All signals from datatype % are synced now',temprow.typename;
    --    DELETE FROM tempDeletes;
    --    --COMMIT;--Commit changes to database
    --END LOOP;
    --DROP TABLE tempDeletes;

    DROP TABLE temp;
END$$;

/*
##################################################      This function is for 1 table per sophia type ################################################
*/
CREATE OR REPLACE PROCEDURE eku_action_timescale_sync(job_id int ,config jsonb)
LANGUAGE plpgsql
AS
$$
DECLARE 
    temprow RECORD;
    _old_typenames RECORD;
    _sources RECORD;
    start_time timestamptz := clock_timestamp();

BEGIN
    /* columns:
        uuid = uuid from foreing data table = sync row from foreign timescale_sync
        sync_uuid = uuid of foreign_timescale_sync
    */
    CREATE TEMP TABLE temp( --copy of data table
      uuid uuid,
      time_utc timestamp without time zone,
      time_mono bigint,
      rcvtime_mono bigint NOT NULL,
      source uuid NOT NULL,
      asset uuid,
      type VARCHAR(100),
      data jsonb,
      sync_uuid uuid,
      sync_time_utc timestamp without time zone);
    
    --CREATE TEMP TABLE temp_duplicates AS TABLE temp;

    -- sync all inserts
    RAISE INFO '############################################################# sync INSERTS ######################################';

    FOR _old_typenames IN SELECT DISTINCT(old_typename) FROM datatypes LOOP
        RAISE INFO 'sync INSERTS for %', _old_typenames;
        
        --Insert old datatype to temp table
        Raise INFO 'copy signal of type % from foreign_timescale_sync to TEMP TABLE ',  _old_typenames.old_typename;
        INSERT INTO temp
        SELECT * FROM (
        SELECT d.uuid,d.time_utc, d.time_mono,d.rcvtime_mono,d.source,d.asset,d.type,d.data,
               ts.uuid AS sync_uuid,ts.time_utc
        FROM foreign_data d
        INNER JOIN foreign_timescale_sync ts ON d.uuid = ts.row
        WHERE ts.synced = FALSE AND ts.operation = 'INSERT' AND ts.type = _old_typenames.old_typename )sub;
        
        Raise INFO 'Finished copy to TEMP TABLE. Time spend: % ', clock_timestamp() - start_time;

        --check if all sources (fatnodes) already exist in meta_source table, if not add them! (should do this without a loop!)
        FOR _sources IN SELECT DISTINCT source FROM temp LOOP
            EXECUTE format(
            '
                INSERT INTO meta_source(source)
                SELECT ''{"fatnode": "%s"}''
                WHERE NOT EXISTS(SELECT 1 FROM meta_source WHERE (source->>''fatnode'')::uuid = %L)'
            ,_sources.source,_sources.source);
        END LOOP;
        
        --Insert data into tables
        FOR temprow IN SELECT typename, json_getter FROM datatypes WHERE old_typename = _old_typenames.old_typename LOOP
        EXECUTE format('
            INSERT INTO data_raw.%I
            SELECT uuid, time_utc, time_mono, rcvtime_mono, asset, meta_source.id,NULL,NULL,%s
            FROM temp
            LEFT JOIN meta_source ON temp.source = (meta_source.source->>''fatnode'')::uuid'
        ,temprow.typename,temprow.json_getter);
        -- ON CONFLICT(time_utc, meta_source) DO NOTHING

        Raise INFO 'insert % : total time spent=%', temprow.typename, clock_timestamp() - start_time;
        END LOOP;

        -- update foreign timescale_sync table
        UPDATE foreign_timescale_sync SET synced = TRUE WHERE uuid IN (SELECT sync_uuid FROM temp);
        DELETE FROM temp;
    END LOOP;

    RAISE INFO '############################################################# sync UPDATES ######################################';
    FOR _old_typenames IN SELECT DISTINCT(old_typename) FROM datatypes LOOP
        Raise INFO 'copy signal of type % from foreign_timescale_sync to TEMP TABLE ',  _old_typenames.old_typename;

        INSERT INTO temp
        SELECT * FROM (
        SELECT d.uuid,d.time_utc, d.time_mono,d.rcvtime_mono,d.source,d.asset,d.type,d.data,
               ts.uuid AS sync_uuid, ts.time_utc AS sync_time_utc
        FROM foreign_data d
        INNER JOIN foreign_timescale_sync ts ON d.uuid = ts.row
        WHERE ts.synced = FALSE AND ts.operation = 'UPDATE' AND ts.type = _old_typenames.old_typename )sub;
        
        Raise INFO 'Finished copy to TEMP TABLE. Time spend: % ', clock_timestamp() - start_time;

        --check if all sources (fatnodes) already exist in meta_source table, if not add them! (should do this without a loop!)
        FOR _sources IN SELECT DISTINCT source FROM temp LOOP
            EXECUTE format(
            '
                INSERT INTO meta_source(source)
                SELECT ''{"fatnode": "%s"}''
                WHERE NOT EXISTS(SELECT 1 FROM meta_source WHERE (source->>''fatnode'')::uuid = %L)'
            ,_sources.source,_sources.source);
        END LOOP;
        /*
        --check for multiple UPDATES on same row and add the
        INSERT INTO temp_duplicates SELECT * FROM temp WHERE sync_uuid IN(
          SELECT sync_uuid FROM(
          SELECT DISTINCT ON (uuid) uuid,sync_time_utc,sync_uuid FROM
            (
            SELECT * FROM temp
            WHERE uuid IN(SELECT uuid FROM temp GROUP BY uuid HAVING COUNT(*) >1)
            )sub1
            ORDER BY uuid, sync_time_utc DESC NULLS LAST)sub2
        )
        */
        FOR temprow IN SELECT typename, json_getter FROM datatypes WHERE old_typename = _old_typenames.old_typename LOOP
        EXECUTE format('
            UPDATE data_raw.%I
            SET uuid =subquery.uuid, time_utc =subquery.time_utc, time_mono =subquery.time_mono, rcvtime_mono =subquery.rcvtime_mono,meta_source =subquery.source_id,asset =subquery.asset, data =subquery.data
            FROM (SELECT uuid, time_utc, time_mono, rcvtime_mono, asset, meta_source.id AS source_id,NULL,NULL,%s AS data
                  FROM temp
                  LEFT JOIN meta_source ON temp.source = (meta_source.source->>''fatnode'')::uuid) AS subquery
            WHERE data_raw.%I.uuid = subquery.uuid'
            ,temprow.typename,temprow.json_getter,temprow.typename);
            Raise INFO 'update % : total time spent=%', temprow.typename, clock_timestamp() - start_time;
        END LOOP;

        -- update foreign timescale_sync table
        UPDATE foreign_timescale_sync SET synced = TRUE WHERE uuid IN (SELECT sync_uuid FROM temp);
        DELETE FROM temp;
    END LOOP;

    DROP TABLE temp;

    RAISE INFO '############################################################# sync DELETES ######################################';
    CREATE TEMP TABLE temp(
        sync_uuid uuid,
        row_uuid uuid,
        type varchar
        );
    --sync all deletes into temp table
    INSERT INTO temp SELECT uuid,row,type FROM foreign_timescale_sync WHERE operation = 'DELETE' AND synced = 'FALSE';

    FOR _old_typenames IN SELECT DISTINCT(old_typename) FROM datatypes LOOP
        FOR temprow IN SELECT typename FROM datatypes WHERE old_typename = _old_typenames.old_typename LOOP
            EXECUTE format('DELETE FROM data_raw.%I WHERE uuid IN (SELECT row_uuid FROM temp WHERE type = %L)',temprow.typename,_old_typenames.old_typename);
        END LOOP;
    END LOOP;
    
    UPDATE foreign_timescale_sync SET synced = TRUE WHERE uuid IN (SELECT sync_uuid FROM temp);

    DROP TABLE temp;
    --DROP TABLE temp_duplicates;
END$$;

SET ROLE ekupd__timescale_syncer;
SELECT add_job('eku_action_timescale_sync','1 hour',config => NULL);


