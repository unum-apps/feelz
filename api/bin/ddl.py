#!/usr/bin/env python

import relations
import relations_pymysql

import unum_tehfeelz

unifist = unum_tehfeelz.Base.SOURCE

source = relations_pymysql.Source(unifist, schema=unifist.replace('-', '_'), connection=False)

migrations = relations.Migrations()

migrations.generate(relations.models(unum_tehfeelz, unum_tehfeelz.Base))
migrations.convert(unifist)
