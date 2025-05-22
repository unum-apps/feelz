#!/usr/bin/env python

import json

import micro_logger

import relations
import relations_pymysql

import unum_tehfeelz

unifist = unum_tehfeelz.Base.SOURCE
schema = unifist.replace('-', '_')

logger = micro_logger.getLogger("tehfeelz-api")

with open("/opt/service/secret/mysql.json", "r") as mysql_file:
    source = relations_pymysql.Source(unifist, schema=schema, autocommit=True, **json.loads(mysql_file.read()))

cursor = source.connection.cursor()

cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{schema}`")

migrations = relations.Migrations()

logger.info("migrations", extra={"migrated": migrations.apply(unifist)})
