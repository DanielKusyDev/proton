drop table if exists authtoken;

drop table if exists post;

drop table if exists user;

create table user
(
    id       integer      not null
        constraint user_pk
            primary key autoincrement,
    username varchar(256) not null,
    password varchar(512) not null
);

create table authtoken
(
    id      integer not null
        constraint authtoken_pk
            primary key autoincrement,
    user_id integer
        references user
            on update cascade on delete cascade,
    token   varchar(40),
    expires datetime
);

create unique index authtoken_id_uindex
    on authtoken (id);

create table post
(
    id          integer not null
        constraint post_pk
            primary key autoincrement,
    image       varchar(1024),
    description varchar,
    header      varchar(1024),
    user_id     integer
        references user
            on update cascade on delete cascade
);

create unique index post_int_uindex
    on post (id);

create unique index user_id_uindex
    on user (id);

