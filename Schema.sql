
create table task (
    taskid integer primary key autoincrement,
    user_id INTEGER not null,
    task_name text not null,
    task_date text not null,
    task_category text not null,
    task_status BOOLEAN
);

create table user (
    user_id integer primary key autoincrement,
    email text not null,
    password text not null,
    water_count INTEGER not null,
    plant_water_count INTEGER not null
);