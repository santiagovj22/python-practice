--################################################################ schema and foreign server setup #########################################################
 Create new database
    CREATE DATABASE "cudd__data_timescale"
    WITH OWNER "cudd__owner"
    ENCODING 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8';

-- ########################################################Do this in timescale database
/*  Create extensions:
    For a cron-based job scheduler pg_cron is necessary:
    If not already installed follow the instructions here: https://github.com/citusdata/pg_cron
    In the postgresql.conf cron.database_name = 'correctDatabaseNameHere'
    SELECT cron.schedule('timescale-sync-trican','0 * * * *',$CRON$ CALL ts_sync_action(); $CRON$)
    Set the nodename to 127.0.0.1 not to localhost, otherwise authorization fails: UPDATE cron.job set nodename = '127.0.0.1'
    Get all cron-jobs: SELECT * FROM cron.job
    https://www.postgresql.org/docs/current/auth-pg-hba-conf.html
    Get all job details:
    select * from cron.job_run_details;
    ekupd__timescale_syncer profrac__data_timescale
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS timescaledb;
    CREATE EXTENSION IF NOT EXISTS postgres_fdw; // necessary for remote database access 
*/

/*
3) Set up postgres_fdw (used to make connection between 2 databases):
Passworless usage of fdw (requires postgres 13):  https://www.percona.com/blog/2020/09/30/postgresql_fdw-authentication-changes-in-postgresql-13/
https://gist.github.com/sathed/8f27d00f092f0066e1e8e366ba3b0104
Useful: https://thoughtbot.com/blog/postgres-foreign-data-wrapper
Understand fdw: https://www.interdb.jp/pg/pgsql04.html
CREATE SERVER timescale
        FOREIGN DATA WRAPPER postgres_fdw
        OPTIONS (host 'localhost', port '5432', dbname 'profrac__data_timescale',use_remote_estimate 'TRUE', fetch_size '100000');
CREATE USER MAPPING FOR ekupd__timescale_syncer SERVER db1 OPTIONS(user 'ekupd__timescale_syncer',password 'ekutss'); --if superuse the OTIONS with password is not necessary !

*/

GRANT SELECT ON ALL TABLES IN SCHEMA public TO timescale_syncer;

CREATE SCHEMA ts;
GRANT USAGE,CREATE ON SCHEMA ts TO ekupd__timescale_syncer;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ts TO ekupd__timescale_syncer;


CREATE FOREIGN TABLE IF NOT EXISTS foreign_timescale_sync(
    uuid uuid DEFAULT uuid_generate_v4() NOT NULL,
    row uuid NOT NULL,
    time_utc TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    host VARCHAR(100),
    type VARCHAR(100),
    operation VARCHAR(10),
    synced BOOLEAN NOT NULL)
SERVER db1__cudd__data OPTIONS(schema_name 'public', table_name 'timescale_sync');

CREATE FOREIGN TABLE IF NOT EXISTS foreign_data(
    uuid uuid,
    time_utc TIMESTAMP WITHOUT TIME ZONE,
    time_mono BIGINT,
    rcvtime_utc TIMESTAMP WITHOUT TIME ZONE,
    rcvtime_mono BIGINT,
    source uuid,
    asset uuid,
    rcvnode uuid,
    type VARCHAR(100),
    data jsonb,
    validated BOOLEAN)
SERVER db1__cudd__data OPTIONS(schema_name 'public', table_name 'data');

CREATE TABLE timescale_types (
    typename VARCHAR(100) NOT NULL,
    keys VARCHAR(100)[],
    newtypenames VARCHAR(100)[],
    datatypes VARCHAR(20)[],
    PRIMARY KEY (typename)
);

INSERT INTO timescale_types (typename, keys, newtypenames, datatypes) VALUES 
('eku:power_module:battery.1','{voltage, stateofcharge, temperature, current, internal_resistance}',NULL,'{float8, float8, float8, float8, float8}'),
('eku:power_module:cranking.1','{coolant_temperature_min, time_max}',NULL,'{float8, float8}'), 
('eku:power_module:powertrain.1','{operation_state, conditioning_percentage}',NULL,'{varchar, float8}'),   
('eku:power_module:serials.1','{esc,scu,ruth,zeus_esc,zeus_heater}',NULL,'{varchar,varchar,varchar,varchar,varchar}'),
('eku:power_module:settings.1','{esc_auto_set_timer,warmup_delay_time,coolant_leak_monitor_enable,ready_functionality_enable}',NULL,'{float8, float8, float8, float8}'),
('oilandgas:frac-pump:oph:esc-mode.1','{active, engine, pumping, nonpumping, conditioning,ready}',NULL,'{float8, float8, float8, float8, float8, float8}'),
('oilandgas:frac-pump:oph:manual-mode.1','{active, engine, pumping, nonpumping, conditioning }',NULL,'{float8, float8, float8, float8, float8}'),
('oilandgas:frac-pump:powertrain:pump.1','{discharge_pressure,current_flow,hydraulic_power}',NULL,'{float8, float8, float8}'),
('oilandgas:frac-pump:pump.1','{discharge_pressure,current_flow,hydraulic_power}',NULL,'{float8, float8, float8}'),
('oilandgas:frac-pump:states.1','{unit}',NULL,'{varchar}'),
('powertrain:engine.1','{coolanttemp,fuelrate,oiltemp,load_current_speed,speed_rpm,speed_request,torque,oil_pressure,diesel_displacement,dual_fuel_mode}',NULL,'{float8, float8, float8, float8, float8, float8,float8, float8, float8, varchar}'),
('powertrain:transmission.1','{gear, oiltemp, output_shaft_speed, converter_oil_temp, converter_lockup}',NULL,'{varchar, float8, float8, float8, float8}');

('eku:power_module:versions.1')
('powertrain:starts.1')
('oilandgas:frac-pump:powertrain:starts.1','{}',NULL,'{}'),


--This function replaces the following characters : . - 1
CREATE OR REPLACE FUNCTION replaceCharacters(input VARCHAR)
RETURNS VARCHAR 
LANGUAGE 'plpgsql'
AS 
$$
DECLARE 
    regex VARCHAR;
BEGIN
    regex := regexp_replace(regexp_replace(regexp_replace(regexp_replace(input,':', '__','g'),'\.', '_','g'),'-','','g'),'1','','g'); --replace [: . -]
    RETURN regex;

END$$;


-- update the newsignalnames column in table timescale_types
CREATE OR REPLACE FUNCTION updateSignalNames()
RETURNS void 
LANGUAGE plpgsql
AS
$$
DECLARE
    temprow RECORD;
    arr_value VARCHAR;
    newname VARCHAR[];
BEGIN
    FOR temprow IN SELECT * FROM timescale_types
    LOOP
        IF (temprow.newtypenames IS NULL) THEN
            FOR i IN array_lower(temprow.keys, 1) .. array_upper(temprow.keys, 1) LOOP
                newname[i] = replaceCharacters(CONCAT(temprow.typename,temprow.keys[i]));
            END LOOP;
            EXECUTE format('UPDATE timescale_types SET newtypenames=%L WHERE typename = %L',newname, temprow.typename);
            newname := NULL;
        END IF;
    END LOOP;
END$$;

--#####################################################################################Do this on old database
CREATE SERVER db1__cudd__data
        FOREIGN DATA WRAPPER postgres_fdw
        OPTIONS (host 'localhost', port '5432', dbname 'cudd__data',use_remote_estimate 'TRUE', fetch_size '100000');
GRANT USAGE ON FOREIGN SERVER db1__cudd__data TO ekupd__timescale_syncer;
CREATE USER MAPPING FOR ekupd__timescale_syncer SERVER db1__cudd__data OPTIONS(user 'ekupd__timescale_syncer',password 'mypw'); --if superuse the OTIONS with password is not necessary !
CREATE SCHEMA foreign_ts; 
GRANT USAGE,CREATE ON SCHEMA foreign_ts TO ekupd__timescale_syncer;
--Access privileagues on schemas \dn+
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA foreign_ts TO ekupd__timescale_syncer;
-- now login as ekupd_timescale_syncer (because we need user mapping, this ist not available for root)
IMPORT FOREIGN SCHEMA ts FROM SERVER timescale INTO foreign_ts



CREATE FOREIGN TABLE IF NOT EXISTS foreign_timescale_types(
    typename VARCHAR(100) NOT NULL,
    keys VARCHAR(100)[],
    newtypenames VARCHAR(100)[],
    datatypes VARCHAR(20)[])
SERVER timescale OPTIONS(schema_name 'public', table_name 'timescale_types');


CREATE TABLE IF NOT EXISTS timescale_sync (
    uuid uuid DEFAULT uuid_generate_v4() NOT NULL,
    row uuid NOT NULL,
    time_utc TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    host VARCHAR(100),
    type VARCHAR(100),
    operation VARCHAR(10),
    synced BOOLEAN NOT NULL,
    PRIMARY KEY (uuid),
    --FOREIGN KEY (host) REFERENCES hosts(hostname),
    FOREIGN KEY (type) REFERENCES datatypes(typename)
);
CREATE INDEX ON timescale_sync(row);
CREATE INDEX ON timescale_sync(operation);  
CREATE INDEX ON timescale_sync(synced,type,operation);

--create trigger on data table 
CREATE OR REPLACE FUNCTION forward_to_timescale_sync() 
   RETURNS TRIGGER 
   LANGUAGE PLPGSQL
AS $$
DECLARE 
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO timescale_sync(row,time_utc,type,operation,synced) VALUES(NEW.uuid,NEW.time_utc,NEW.type,'INSERT',FALSE) ON CONFLICT DO NOTHING;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO timescale_sync(row,time_utc,type,operation,synced) VALUES(OLD.uuid,NOW(),OLD.type,'DELETE',FALSE) ON CONFLICT DO NOTHING;
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO timescale_sync(row,time_utc,type,operation,synced) VALUES(OLD.uuid,NOW(),NEW.type,'UPDATE',FALSE) ON CONFLICT DO NOTHING ;
        RETURN NEW;
    END IF;
END$$;

CREATE TRIGGER trigger_forward_to_timescale_sync
  AFTER UPDATE OR DELETE OR INSERT on data
  FOR EACH ROW
  EXECUTE PROCEDURE forward_to_timescale_sync()




--############################################################ timescale table setup for 1 table per base type (float, varchar) #################################################
INSERT INTO datatypes SELECT unnest(newtypenames) FROM timescale_types;
-- float8a
CREATE TABLE IF NOT EXISTS ts.data_float8 (
                        uuid uuid DEFAULT uuid_generate_v4() NOT NULL,
                        time_utc timestamp without time zone NOT NULL,
                        time_mono bigint,
                        rcvtime_utc timestamp without time zone DEFAULT now(),
                        rcvtime_mono bigint NOT NULL,
                        source uuid NOT NULL,
                        asset uuid,
                        rcvnode uuid,
                        type VARCHAR(100),
                        data float8,
                        validated boolean NOT NULL,
                        uuid_original uuid,
                        FOREIGN KEY (type) REFERENCES datatypes(typename)
                        );
SELECT create_hypertable('ts.data_float8','time_utc',chunk_time_interval => INTERVAL '1 month',if_not_exists => TRUE);
ALTER TABLE ts.data_float8 SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'asset,type'
);
SELECT add_compression_policy('ts.data_float8', INTERVAL '2 months');
CREATE INDEX ON ts.data_float8(asset,type, time_utc DESC);
CREATE INDEX ON ts.data_float8(asset, time_utc DESC);
ALTER TABLE ts.data_float8 OWNER TO cudd__data_adm;
GRANT INSERT, SELECT, UPDATE, DELETE ON ts.data_float8 TO cudd__data_rw,ekupd__timescale_syncer;
GRANT SELECT ON ts.data_float8 TO cudd__data_ro;

-- varchar
CREATE TABLE IF NOT EXISTS ts.data_varchar (
                        uuid uuid DEFAULT uuid_generate_v4() NOT NULL,
                        time_utc timestamp without time zone NOT NULL,
                        time_mono bigint,
                        rcvtime_utc timestamp without time zone DEFAULT now(),
                        rcvtime_mono bigint NOT NULL,
                        source uuid NOT NULL,
                        asset uuid,
                        rcvnode uuid,
                        type VARCHAR(100),
                        data varchar(100),
                        validated boolean NOT NULL,
                        uuid_original uuid,
                        FOREIGN KEY (type) REFERENCES datatypes(typename)
                        );
SELECT create_hypertable('ts.data_varchar','time_utc',chunk_time_interval => INTERVAL '1 month',if_not_exists => TRUE);
ALTER TABLE ts.data_varchar SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'asset,type'
);
SELECT add_compression_policy('ts.data_varchar', INTERVAL '2 months');
CREATE INDEX ON ts.data_varchar(asset,type, time_utc DESC);
CREATE INDEX ON ts.data_varchar(asset, time_utc DESC);
ALTER TABLE ts.data_varchar OWNER TO cudd__data_adm;
GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES,TRIGGER ON ts.data_varchar TO cudd__data_rw,ekupd__timescale_syncer;
GRANT SELECT ON ts.data_varchar TO cudd__data_ro;

CREATE MATERIALIZED VIEW ts.data_float8_hourly
WITH (timescaledb.continuous) AS
SELECT asset,
       type,
       time_bucket(INTERVAL '1 hour', time_utc) AS bucket,
       AVG(data) AS data
FROM ts.data_float8
GROUP BY asset,type, bucket;

CREATE MATERIALIZED VIEW ts.data_float8_5minutes
WITH (timescaledb.continuous) AS
SELECT asset,
       type,
       time_bucket(INTERVAL '5 minutes', time_utc) AS bucket,
       AVG(data) AS data
FROM ts.data_float8
GROUP BY asset,type, bucket;

--#####################################################################( timescale table setup for 1 table per sophia type #########################################################
CREATE OR REPLACE FUNCTION createTables1()
RETURNS void 
LANGUAGE plpgsql
AS
$$
DECLARE 
    temprow RECORD; --variable that holds one record of a select
BEGIN

    FOR temprow IN SELECT * FROM timescale_types
    LOOP
        IF (temprow.newtypenames = NULL) THEN
            RAISE INFO 'no newtypenames for typename %. Skipping...',temprow.typename;
        ELSIF (array_length(temprow.newtypenames,1) != array_length(temprow.datatypes,1)) THEN
            RAISE INFO 'keys and datatypes do not have the same length for typename %. Skipping...',temprow.typename;
        ELSIF (array_length(temprow.newtypenames,1) = array_length(temprow.datatypes,1)) THEN
            FOR i IN array_lower(temprow.newtypenames, 1) .. array_upper(temprow.newtypenames, 1) LOOP
                --create new table for each signal type
                EXECUTE format(
                    '
                        CREATE TABLE IF NOT EXISTS ts.%I (
                        uuid uuid DEFAULT uuid_generate_v4() NOT NULL,
                        time_utc timestamp without time zone NOT NULL,
                        time_mono bigint,
                        rcvtime_utc timestamp without time zone DEFAULT now(),
                        rcvtime_mono bigint NOT NULL,
                        source uuid NOT NULL,
                        asset uuid,
                        rcvnode uuid,
                        data %I,
                        validated boolean NOT NULL
                        );

                        SELECT create_hypertable(''ts.%I'',''time_utc'',chunk_time_interval => INTERVAL ''60 days'',if_not_exists => TRUE);
                        CREATE INDEX IF NOT EXISTS %I_asset_time_utc_index ON ts.%I(asset, time_utc DESC);
                        CREATE INDEX IF NOT EXISTS %I_asset ON ts.%I(asset);
                        ALTER TABLE ts.%I OWNER TO profrac__data_adm;
                        GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES,TRIGGER ON ts.%I TO profrac__data_rw,ekupd__timescale_syncer;
                        GRANT SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES,TRIGGER ON ts.%I TO profrac__data_ro;
                    '
                    ,temprow.newtypenames[i] ,temprow.datatypes[i], temprow.newtypenames[i],temprow.newtypenames[i],temprow.newtypenames[i],temprow.newtypenames[i], temprow.newtypenames[i], temprow.newtypenames[i],temprow.newtypenames[i],temprow.newtypenames[i]); 
            END LOOP;
        END IF;
    END LOOP;
END$$;