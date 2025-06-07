"""
Module for the OPenGUI API
"""

# pylint: disable=no-self-use

import json
import yaml

import micro_logger

import flask
import flask_restx
import prometheus_flask_exporter
import redis

import relations
import relations_pymysql
import relations_restx

import unum_ledger
import unum_tehfeelz

WHO = "tehfeelz"
META = """
title: TehFeelz
channel: unum-tehfeelz
description: Tracks yours and others feelings and the relationships between.
help: |
  This does a lot of cool shit with your feelings
commands:
- name: state
  description: Record or list your state of mind, good or bad
  usages:
  - name: record
    meme: '!'
    description: Record your current state as {state}
    args:
    - name: state
      valids:
      - unable: I'm stuck. I need info
      - ❓: unable
      - good: I'm doing well, and growing
      - 👍: good
      - able: I'm doing even, not stuck or unstable
      - ♥️: able
      - bad: I've been better, but not hurting
      - 👎: bad
      - unstable: I'm hurting and need help
      - ❗: unstable
  - name: list_since
    meme: '?'
    description: List your states from {since} ago to now
    args:
    - name: since
      description: How far back to list
      format: duration
  - name: list_from_to
    meme: '?'
    description: List your states from {from} to {to}
    args:
    - name: from
      description: How far back to start listing
      format: duration
    - name: to
      description: How far back to stop listing
      format: duration
- name: mood
  description: Record or list your mood with an emoji
  usages:
  - name: record
    meme: '!'
    description: Record your current mood as {mood}
    args:
    - name: mood
      format: emoji
  - name: list_since
    meme: '?'
    description: List your moods from {since} ago to now
    args:
    - name: since
      description: How far back to list
      format: duration
  - name: list_from_to
    meme: '?'
    description: List your moods from {from} to {to}
    args:
    - name: from
      description: How far back to start listing
      format: duration
    - name: to
      description: How far back to stop listing
      format: duration
- name: diary
  description: Record or list your diary with some thoughts
  usages:
  - name: record
    meme: '!'
    description: Record your current diary as {thoughts}
    args:
    - name: thoughts
      format: remainder
  - name: list_since
    meme: '?'
    description: List your diaries from {since} ago to now
    args:
    - name: since
      description: How far back to list
      format: duration
  - name: list_from_to
    meme: '?'
    description: List your diaries from {from} to {to}
    args:
    - name: from
      description: How far back to start listing
      format: duration
    - name: to
      description: How far back to stop listing
      format: duration
- name: quepasa
  description: Manage me (bot) checking in on you
  usages:
  - name: start_every
    meme: '!'
    description: I will check on you every {every}
    args:
    - name: every
      format: duration
      description: Check in every {every}
  - name: start_from_to
    meme: '!'
    description: I will check on you from every {from} to every {to}
    args:
    - name: from
      description: Check in earliest every {from}
      format: duration
    - name: to
      description: Check in latest every {to}
      format: duration
  - name: stop
    meme: '!'
    description: I will not check on you
    args:
    - name: stop
      valids:
      - stop
  - name: current
    meme: '?'
    description: Shows your current quepasa
- name: fam
  description: Manage who can check in on you
  usages:
  - name: start
    meme: '!'
    description: Request a bond frmm {who} to you
    args:
    - name: who
      description: The person you're requesting
      format: user
  - name: stop
    meme: '!'
    description: Pause the bond from {who} to you
    args:
    - name: who
      description: The person you're requesting
      format: user
    - name: stop
      valids:
      - stop
  - name: current
    meme: '?'
    description: Shows your current fam
- name: ugood
  description: Manage fam checking in on you
  usages:
  - name: start_from_to
    meme: '!'
    description: Request {who} check on you from every {from} to every {to}
    args:
    - name: who
      description: The person you're requesting
      format: user
    - name: from
      description: Check in earliest every {from}
      format: duration
    - name: to
      description: Check in latest every {to}
      format: duration
    reactions:
    - meme: '+'
      value: good
      description: I will check on 
    - meme: '-'
      value: bad
      description: I'm doing worse than expected.
  - name: start_every
    meme: '!'
    description: Request {who} check on you every {every}
    args:
    - name: who
      description: The person you're requesting
      format: user
    - name: every
      format: duration
      description: Check in every {every}
  - name: stop
    meme: '!'
    description: Pause {who} checking on you
    args:
    - name: who
      description: The person you're requesting
      format: user
    - name: stop
      valids:
      - stop
  - name: current
    meme: '?'
    description: Shows your current ugood
- name: muybien
  description: Manage bad states increases your check ins from others
  usages:
  - name: start
    meme: '!'
    description: For every bad state take {amount} from the next ugood check in
    args:
    - name: amount
      description: Check in every {amount}
      format: duration
  - name: stop
    meme: '!'
    description: Stops your current muybien
    args:
    - name: stop
      valids:
      - stop
  - name: current
    meme: '?'
    description: Shows your current muybien
- name: quepasacheck
  user: false
  reactions:
  - meme: '?'
    value: unable
    description: I can't move forward. I'm stuck. 
  - meme: '+'
    value: good
    description: I'm doing better than expected.
  - meme: '*'
    value: able
    description: I'm doing as well as expected.
  - meme: '-'
    value: bad
    description: I'm doing worse than expected.
  - meme: '!'
    value: unstable
    description: Something is wrong. I'm hurting.
- name: quepasacheck
  user: false
  reactions:
  - meme: '?'
    value: unable
    description: I can't move forward. I'm stuck. 
  - meme: '+'
    value: good
    description: I'm doing better than expected.
  - meme: '*'
    value: able
    description: I'm doing as well as expected.
  - meme: '-'
    value: bad
    description: I'm doing worse than expected.
  - meme: '!'
    value: unstable
    description: Something is wrong. I'm hurting.
"""

NAME = f"{WHO}-api"

metrics = prometheus_flask_exporter.PrometheusMetrics.for_app_factory()

def build():
    """
    Builds the Flask App
    """

    import service # pylint: disable=import-outside-toplevel

    app = flask.Flask(service.NAME)

    app.logger = micro_logger.getLogger(service.NAME)
    app.unifist = unum_tehfeelz.Base.SOURCE
    app.schema = app.unifist.replace('-', '_')

    metrics.init_app(app)

    api = flask_restx.Api(app)

    with open("/opt/service/secret/mysql.json", "r") as mysql_file:
        creds = json.loads(mysql_file.read())

        relations_pymysql.Source(
            unum_ledger.Base.SOURCE, schema=unum_ledger.Base.SOURCE.replace('-', '_'), autocommit=True, **creds
        )

        app.source = relations_pymysql.Source(
            app.unifist, schema=app.schema, autocommit=True, **creds
        )

    if not unum_ledger.App.one(who="tehfeelz").retrieve(False):
        unum_ledger.App(who="tehfeelz").create()

    unum_ledger.App.one(who=WHO).set(meta=yaml.safe_load(META)).update()

    def ping():
        app.source.connection.ping(True)

    app.before_request(ping)

    api.add_resource(Health, '/health')

    relations_restx.attach(api, service, relations.models(unum_tehfeelz, unum_tehfeelz.Base))

    return app

class Health(flask_restx.Resource):
    """
    Class for Health checks
    """

    def get(self):
        """
        Just return ok
        """
        return {"message": "OK"}
