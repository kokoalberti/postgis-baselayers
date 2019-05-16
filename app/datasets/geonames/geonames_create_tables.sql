drop table if exists geoname;
create table geoname (
    geonameid   int,
    name varchar(200),
    asciiname varchar(200),
    alternatenames text,
    latitude float,
    longitude float,
    fclass char(1),
    fcode varchar(10),
    country varchar(2),
    cc2 varchar(200),
    admin1 varchar(20),
    admin2 varchar(80),
    admin3 varchar(20),
    admin4 varchar(20),
    population bigint,
    elevation int,
    gtopo30 int,
    timezone varchar(40),
    moddate date
 );
drop table if exists alternatename;
create table alternatename (
    alternatenameId int,
    geonameid int,
    isoLanguage varchar(7),
    alternateName varchar(200),
    isPreferredName boolean,
    isShortName boolean,
    isColloquial boolean,
    isHistoric boolean
 );
drop table if exists countryinfo;
create table "countryinfo" (
    iso_alpha2 char(2),
    iso_alpha3 char(3),
    iso_numeric integer,
    fips_code varchar(3),
    name varchar(200),
    capital varchar(200),
    areainsqkm double precision,
    population integer,
    continent varchar(2),
    tld varchar(10),
    currencycode varchar(3),
    currencyname varchar(20),
    phone varchar(20),
    postalcode varchar(100),
    postalcoderegex varchar(200),
    languages varchar(200),
    geonameId int,
    neighbors varchar(50),
    equivfipscode varchar(3)
);
