create table taps (
  tap_id integer primary key,
  beer_id text,
  last_updated integer,
  last_updated_by text,
  amount_poured integer default 0
);

insert into taps(tap_id) values(1);
insert into taps(tap_id) values(2);
insert into taps(tap_id) values(3);
insert into taps(tap_id) values(4);

create table tap_history (
  tap_id integer,
  update_time integer,
  beer_id text
);

create trigger update_tap after update of beer_id on taps
begin
  insert into tap_history(tap_id, update_time, beer_id) values(NEW.tap_id, strftime('%s', 'now'), NEW.beer_id);
end;

create table flowmeter (
  tap_id integer,
  flow_time integer,
  num_pulses integer
);

create index idx_flowmeter_id on flowmeter(tap_id);
create index idx_flowmeter_time on flowmeter(flow_time);

create trigger insert_flowmeter after insert on flowmeter
begin
  update taps set amount_poured = amount_poured + NEW.num_pulses where tap_id = NEW.tap_id;
end;

create table temperature (
  sensor_id integer primary key,
  deg_c numeric,
  last_reading integer
);
