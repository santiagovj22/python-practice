-----------------------
-- Schema definitions --
-----------------------
CREATE SCHEMA IF NOT EXISTS data_raw AUTHORIZATION trican__data_adm;
CREATE SCHEMA IF NOT EXISTS data_5min AUTHORIZATION trican__data_adm;
CREATE SCHEMA IF NOT EXISTS data_15min AUTHORIZATION trican__data_adm;
CREATE SCHEMA IF NOT EXISTS data_1hour AUTHORIZATION trican__data_adm;
CREATE SCHEMA IF NOT EXISTS data_1day AUTHORIZATION trican__data_adm;

CREATE SCHEMA IF NOT EXISTS data_meta_raw AUTHORIZATION trican__data_adm;

GRANT USAGE ON SCHEMA data_raw TO trican__data_ro;
GRANT USAGE ON SCHEMA data_5min TO trican__data_ro;
GRANT USAGE ON SCHEMA data_15min TO trican__data_ro;
GRANT USAGE ON SCHEMA data_1hour TO trican__data_ro;
GRANT USAGE ON SCHEMA data_1day TO trican__data_ro;

GRANT USAGE ON SCHEMA data_meta_raw TO trican__data_ro;
GRANT USAGE ON SCHEMA data_meta_5min TO trican__data_ro;
GRANT USAGE ON SCHEMA data_meta_15min TO trican__data_ro;
GRANT USAGE ON SCHEMA data_meta_1hour TO trican__data_ro;
GRANT USAGE ON SCHEMA data_meta_1day TO trican__data_ro;

GRANT USAGE,CREATE ON SCHEMA data_raw TO trican__data_rw;
GRANT USAGE,CREATE ON SCHEMA data_5min TO trican__data_rw;
GRANT USAGE,CREATE ON SCHEMA data_15min TO trican__data_rw;
GRANT USAGE,CREATE ON SCHEMA data_1hour TO trican__data_rw;
GRANT USAGE,CREATE ON SCHEMA data_1day To trican__data_rw;

GRANT USAGE,CREATE ON SCHEMA data_meta_raw TO trican__data_rw;

-----------------------
-- Table definitions --
-----------------------
--add uuid ?   
CREATE TABLE IF NOT EXISTS meta_source
(
    id BIGSERIAL PRIMARY KEY, 
    source jsonb NOT NULL
);
CREATE INDEX ON meta_source USING GIN (source);-- you have to use these operators for using gin index ?, ?&, ?|, or @>
ALTER TABLE meta_source OWNER TO trican__data_adm;
GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES,TRIGGER ON meta_source TO trican__data_rw,ekupd__timescale_syncer;
GRANT SELECT ON meta_source TO trican__data_ro;
GRANT USAGE, SELECT ON SEQUENCE meta_source_id_seq TO trican__data_rw,ekupd__timescale_syncer;
GRANT SELECT ON SEQUENCE meta_source_id_seq TO trican__data_ro;

--add uuid ?
CREATE TABLE IF NOT EXISTS meta_quality
(
    id BIGSERIAL,
    quality jsonb,
    UNIQUE(id)
);
ALTER TABLE meta_quality OWNER TO trican__data_adm;
GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES,TRIGGER ON meta_quality TO trican__data_rw,ekupd__timescale_syncer;
GRANT SELECT ON meta_quality TO trican__data_ro;
GRANT USAGE, SELECT ON SEQUENCE meta_quality_id_seq TO trican__data_rw,ekupd__timescale_syncer;
GRANT SELECT ON SEQUENCE meta_quality_id_seq TO trican__data_ro;

CREATE TABLE IF NOT EXISTS plot_types
(
    types VARCHAR(100) PRIMARY KEY
);
ALTER TABLE plot_types OWNER TO trican__data_adm;
GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES,TRIGGER ON plot_types TO trican__data_rw,ekupd__timescale_syncer;
GRANT SELECT ON plot_types TO trican__data_ro;
INSERT INTO plot_types VALUES('discrete'),('continuous');

CREATE TABLE IF NOT EXISTS schemas_buckets
(
    schema_name VARCHAR(20) PRIMARY KEY,
    bucket_size VARCHAR(20) 
);
ALTER TABLE schemas_buckets OWNER TO trican__data_adm;
GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES,TRIGGER ON schemas_buckets TO trican__data_rw,ekupd__timescale_syncer;
GRANT SELECT ON schemas_buckets TO trican__data_ro;
INSERT INTO schemas_buckets VALUES('data_5min','5 minutes'),('data_15min','15 minutes'),('data_1hour','1 hour'),('data_1day','1 day');


CREATE TABLE IF NOT EXISTS datatypes
(
   typename VARCHAR(63) PRIMARY KEY,
   display_name VARCHAR(63) NOT NULL UNIQUE,
   old_typename VARCHAR(100),
   old_key VARCHAR(100),
   datatype VARCHAR(20),
   plottype VARCHAR(100),
   unit VARCHAR(20),
   description TEXT,
   autodiscover BOOLEAN,
   json_getter VARCHAR(100),
   chunk_size VARCHAR(20),
   hypertable BOOLEAN NOT NULL,
   FOREIGN KEY(plottype) REFERENCES plot_types(types)
);
ALTER TABLE datatypes OWNER TO trican__data_adm;
GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES,TRIGGER ON datatypes TO trican__data_rw,ekupd__timescale_syncer;
GRANT SELECT ON datatypes TO trican__data_ro;
INSERT INTO datatypes VALUES('eku__power_module_battery_voltage','battery_voltage','eku:power_module:battery.1','voltage','float8','continuous',NULL,NULL,NULL,'(data->''voltage''->>''value'')::float8',NULL,TRUE),
('eku__power_module_battery_stateofcharge','battery_stateofcharge','eku:power_module:battery.1','stateofcharge','float8','continuous',NULL,NULL,NULL,'(data->''stateofcharge''->>''value'')::float8',NULL,TRUE),
('eku__power_module_battery_temperature','battery_temperature','eku:power_module:battery.1','temperature','float8','continuous',NULL,NULL,NULL,'(data->''temperature''->>''value'')::float8',NULL,TRUE),
('eku__power_module_battery_current','battery_current','eku:power_module:battery.1','current','float8','continuous',NULL,NULL,NULL,'(data->''current''->>''value'')::float8',NULL,TRUE),
('eku__power_module_battery_internal_resistance','battery_internal_resistance','eku:power_module:battery.1','internal_resistance','float8','continuous',NULL,NULL,NULL,'(data->''internal_resistance''->>''value'')::float8',NULL,TRUE),
('eku__power_module_cranking_coolant_temperature_min','cranking_coolant_temperature_min','eku:power_module:cranking.1','coolant_temperature_min','float8','continuous',NULL,NULL,NULL,'(data->''coolant_temperature_min''->>''value'')::float8',NULL,TRUE), 
('eku__power_module_cranking_time_max','cranking_time_max','eku:power_module:cranking.1','time_max','float8','continuous',NULL,NULL,NULL,'(data->''time_max''->>''value'')::float8',NULL,TRUE),
('eku__power_module_powertrain_operation_state','powertrain_state','eku:power_module:powertrain.1','operation_state','varchar(30)','discrete',NULL,NULL,NULL,'(data->''operation_state''->>''value'')::varchar',NULL,TRUE),   
('eku__power_module_powertrain_conditioning_percentage','powertrain_conditioning_percentage','eku:power_module:powertrain.1','conditioning_percentage','float8','continuous',NULL,NULL,NULL,'(data->''conditioning_percentage''->>''value'')::float8',NULL,TRUE),   
('oilandgas__frac_pump_oph_manual_mode_active','oph_manual_active','oilandgas:frac-pump:oph:manual-mode.1','active','float8','continuous',NULL,NULL,NULL,'(data->''active''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_oph_manual_mode_engine','oph_manual_engine','oilandgas:frac-pump:oph:manual-mode.1','engine','float8','continuous',NULL,NULL,NULL,'(data->''engine''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_oph_manual_mode_pumping','oph_manual_pumping','oilandgas:frac-pump:oph:manual-mode.1','pumping','float8','continuous',NULL,NULL,NULL,'(data->''pumping''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_oph_manual_mode_nonpumping','oph_manual_nonpumping','oilandgas:frac-pump:oph:manual-mode.1','nonpumping','float8','continuous',NULL,NULL,NULL,'(data->''nonpumping''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_oph_manual_mode_conditioning','oph_manual_conditioning','oilandgas:frac-pump:oph:manual-mode.1','conditioning','float8','continuous',NULL,NULL,NULL,'(data->''conditioning''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_oph_esc_mode_active','oph_esc_active','oilandgas:frac-pump:oph:esc-mode.1','active','float8','continuous',NULL,NULL,NULL,'(data->''active''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_oph_esc_mode_engine','oph_esc_engine','oilandgas:frac-pump:oph:esc-mode.1','engine','float8','continuous',NULL,NULL,NULL,'(data->''engine''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_oph_esc_mode_pumping','oph_esc_pumping','oilandgas:frac-pump:oph:esc-mode.1','pumping','float8','continuous',NULL,NULL,NULL,'(data->''pumping''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_oph_esc_mode_nonpumping','oph_esc_nonpumping','oilandgas:frac-pump:oph:esc-mode.1','nonpumping','float8','continuous',NULL,NULL,NULL,'(data->''nonpumping''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_oph_esc_mode_conditioning','oph_esc_conditioning','oilandgas:frac-pump:oph:esc-mode.1','conditioning','float8','continuous',NULL,NULL,NULL,'(data->''conditioning''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_oph_esc_mode_ready','oph_esc_ready','oilandgas:frac-pump:oph:esc-mode.1','ready','float8','continuous',NULL,NULL,NULL,'(data->''ready''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_powertrain_discharge_pressure','pump_discharge_pressure','oilandgas:frac-pump:pump.1','discharge_pressure','float8','continuous',NULL,NULL,NULL,'(data->''discharge_pressure''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_powertrain_current_flow','pump_current_flow','oilandgas:frac-pump:pump.1','current_flow','float8','continuous',NULL,NULL,NULL,'(data->''current_flow''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_powertrain_hydraulic_power','pump_hydraulic_power','oilandgas:frac-pump:pump.1','hydraulic_power','float8','continuous',NULL,NULL,NULL,'(data->''hydraulic_power''->>''value'')::float8',NULL,TRUE),
('oilandgas__frac_pump_states','pump_states','oilandgas:frac-pump:states.1','unit','varchar(30)','discrete',NULL,NULL,NULL,'(data->''unit''->>''value'')::varchar',NULL,TRUE),
('powertrain__engine_coolanttemp','powertrain_engine_coolanttemp','powertrain:engine.1','coolanttemp','float8','continuous',NULL,NULL,NULL,'(data->''coolanttemp''->>''value'')::float8',NULL,TRUE),
('powertrain__engine_fuelrate','powertrain_engine_fuelrate','powertrain:engine.1','fuelrate','float8','continuous',NULL,NULL,NULL,'(data->''fuelrate''->>''value'')::float8',NULL,TRUE),
('powertrain__engine_oiltemp','powertrain_engine_oiltemp','powertrain:engine.1','oiltemp','float8','continuous',NULL,NULL,NULL,'(data->''oiltemp''->>''value'')::float8',NULL,TRUE),
('powertrain__engine_load_current_speed','powertrain_engine_load_current_speed','powertrain:engine.1','load_current_speed','float8','continuous',NULL,NULL,NULL,'(data->''load_current_speed''->>''value'')::float8',NULL,TRUE),
('powertrain__engine_speed_rpm','powertrain_engine_speed_rpm','powertrain:engine.1','speed_rpm','float8','continuous',NULL,NULL,NULL,'(data->''speed_rpm''->>''value'')::float8',NULL,TRUE),
('powertrain__engine_speed_request','powertrain_engine_speed_request','powertrain:engine.1','speed_request','float8','continuous',NULL,NULL,NULL,'(data->''speed_request''->>''value'')::float8',NULL,TRUE),
('powertrain__engine_torque','powertrain_engine_torque','powertrain:engine.1','torque','float8','continuous',NULL,NULL,NULL,'(data->''torque''->>''value'')::float8',NULL,TRUE),
('powertrain__engine_oil_pressure','powertrain_engine_oil_pressure','powertrain:engine.1','oil_pressure','float8','continuous',NULL,NULL,NULL,'(data->''oil_pressure''->>''value'')::float8',NULL,TRUE),
('powertrain__engine_diesel_displacement','powertrain_engine_diesel_displacement','powertrain:engine.1','diesel_displacement','float8','continuous',NULL,NULL,NULL,'(data->''diesel_displacement''->>''value'')::float8',NULL,TRUE),
('powertrain__engine_dual_fuel_mode','powertrain_engine_dual_fuel_mode','powertrain:engine.1','dual_fuel_mode','varchar(40)','discrete',NULL,NULL,NULL,'(data->''dual_fuel_mode''->>''value'')::varchar',NULL,TRUE),
('powertrain__transmission_gear','transmission_gear','powertrain:transmission.1','gear','varchar(30)','discrete',NULL,NULL,NULL,'(data->''gear''->>''value'')::varchar',NULL,TRUE),
('powertrain__transmission_oiltemp','transmission_oiltemp','powertrain:transmission.1','oiltemp','float8','continuous',NULL,NULL,NULL,'(data->''oiltemp''->>''value'')::float8',NULL,TRUE),
('powertrain__transmission_output_shaft_speed','transmission_output_shaft_speed','powertrain:transmission.1','output_shaft_speed','float8','continuous',NULL,NULL,NULL,'(data->''output_shaft_speed''->>''value'')::float8',NULL,TRUE),
('powertrain__transmission_converter_oil_temp','transmission_converter_oil_temp','powertrain:transmission.1','converter_oil_temp','float8','continuous',NULL,NULL,NULL,'(data->''converter_oil_temp''->>''value'')::float8',NULL,TRUE),
('powertrain__transmission_converter_lockup','transmission_converter_lockup','powertrain:transmission.1','converter_lockup','float8','continuous',NULL,NULL,NULL,'(data->''converter_lockup''->>''value'')::float8',NULL,TRUE),
('eku__power_module_settings','power_module_settings','eku:power_module:settings.1',NULL,'jsonb','discrete',NULL,NULL,NULL,'data',NULL,FALSE),
('eku__power_module_serials','power_module_serials','eku:power_module:serials.1',NULL,'jsonb','discrete',NULL,NULL,NULL,'data',NULL,FALSE),
('eku__power_module_versions','power_module_versions','eku:power_module:versions.1',NULL,'jsonb','discrete',NULL,NULL,NULL,'data',NULL,FALSE),
('powertrain__starts','powertrain_starts','powertrain:starts.1',NULL,'jsonb','discrete',NULL,NULL,NULL,'data',NULL,FALSE);



/*
('eku:power_module:battery.1','{voltage, stateofcharge, temperature, current, internal_resistance}',NULL,'{float8, float8, float8, float8, float8}');
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
*/
