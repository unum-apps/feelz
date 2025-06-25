#!/usr/bin/env python

import relations
import relations_pymysql

import unum_feelz

unifist = unum_feelz.Base.SOURCE

source = relations_pymysql.Source(unifist, schema=unifist.replace('-', '_'), connection=False)

migrations = relations.Migrations()

migrations.generate(relations.models(unum_feelz, unum_feelz.Base))
migrations.convert(unifist)
