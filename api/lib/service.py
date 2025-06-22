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

import unum_base
import unum_ledger
import unum_feelz

WHO = "feelz"
META = """
title: feelz
channel: unum-feelz
description: Tracks yours and others feelings and the relationships between.
help: |
  The Feelz App is about improving our feelings in an Unum.

  It tracks how we feel at times, who we feel safe enough to consider Fam, even ways of having me or other check in on you.

  The overall goal is to get data on how we feel and what affects those feelings.
commands:
- name: state
  description: Record or list your state of mind, good or bad
  help: |
    This is a very simply tracking mechansim, only recording your state of mind, commomn understanding feelings.

    There's five states to chose from and the simplicity is the point. We can over all the complex reasons to how we got here, but at the beginnning of the day, we need to see how we're doing overall.
  examples:
  - meme: '!'
    args: good
    description: Record you state as good by name
  - meme: '!'
    channel: unum-feelz
    args: 👍
    description: Record you state as good by eomji
  - meme: '!'
    kind: private
    args: +
    description: Record you state as good by meme
  - meme: '?'
    args: 1d
    description: List your states in the past day
  - meme: '?'
    args: 3d 2d
    description: List your states from three days ago to two days ago
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
  help: |
    This is a simple but expressive way of recording our partciluar, unique moods.

    Simply give an emoji that best describes your mood. This info should summarize the overall vibe.
  examples:
  - meme: '!'
    args: 🤣
    description: Record you mood as 🤣
  - meme: '?'
    args: 1d
    description: List your moods in the past day
  - meme: '?'
    args: 3d 2d
    description: List your moods from three days ago to two days ago
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
  help: |
    This is a very expressive wya to record our exact thoughts.

    Let loose how you feel. Record what brought here or just what you're thinking.
  examples:
  - meme: '!'
    args: not so bad
    description: Record you diary as not so bad
  - meme: '?'
    args: 1d
    description: List your diaries in the past day
  - meme: '?'
    args: 3d 2d
    description: List your diaries from three days ago to two days ago
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
  help: |
    Rather that you initiate recording your State, Mood, or Diary, I can reach to you and you only need to respond. The goal here is to regularly track your feelings without having to remember to do so (and making it easy).

    React with any of the emojis from State, and I'll record that as your State. React with any other emoji and I'll record that as your Mood. Any reply with words, I'll record that as your Diary.
  examples:
  - meme: '!'
    args: 1m
    description: Have me check on you every minute
  - meme: '!'
    args: 1m 5m
    description: Have me check on you every 1 to 5 minutes
  - meme: '!'
    args: stop
    description: Have me stop checking in on you
  - meme: '?'
    description: See whether I'm checking in on you
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
  help: |
    Saying someone is Fam means you're willing to have them check in on you. You make the request, I'll ask them if they're cool with it, and if they accept, you're Fam.

    Once someone is Fam you can request they check in on you via Ugood.
  examples:
  - meme: '!'
    args: '@'
    description: Fam someone in the channel
  - meme: '?'
    description: See woh your current fam is
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
  help: |
    Having me check in on you is nice, but it's even better if another human does it. Ugood enables you you to ask someone to check in on you. Like QuePasa, simply responding to my comment will indicate Feelings.

    But unlike QuePasa, if you're the one checking in on someone else, your response indicate their mood, not yours. If you're being checked on, it'll still record your reactions as your feelings.
  examples:
  - meme: '!'
    args: '@ 1d'
    description: Have someone check in on you every day or so
  - meme: '!'
    args: '@ 1d 3d'
    description: Have someone check in on you every one to three days or so
  - meme: '!'
    args: '@ stop'
    description: Have someone stop cehcking in on you
  - meme: '?'
    description: See who's checking in on you
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
  help: |
    When you're not doing great, someone should check in on you sooner than later. MuyBien allows you to make that happen.

    For every negative State, MuyBien can make the next Ugood check in closer by some time determinded by you.
  examples:
  - meme: '!'
    args: 1h
    description: Have every bad state substract 1 hour from your next ugood check in
  - meme: '!'
    args: stop
    description: Have me stop using bad state to increaes ugood check in
  - meme: '?'
    description: See if bad states are affecting your ugood check ins
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
requests:
- name: quepasacheck
  description: Me checking in on you
  usages:
  - name: check
    meme: '?'
    description: Request for state, mood, or diary
    responses:
    - kind: meme
      name: state
      description: Indicates your state
    - kind: emoji
      name: mood
      description: Indicates your mood
    - kind: reply
      name: diary
      description: Indicates your thoughts
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
    app.unifist = unum_feelz.Base.SOURCE
    app.schema = app.unifist.replace('-', '_')

    metrics.init_app(app)

    api = flask_restx.Api(app)

    app.redis = redis.Redis(host=f'redis.ledger', encoding="utf-8", decode_responses=True)

    with open("/opt/service/secret/mysql.json", "r") as mysql_file:
        creds = json.loads(mysql_file.read())

        relations_pymysql.Source(
            unum_ledger.Base.SOURCE, schema=unum_ledger.Base.SOURCE.replace('-', '_'), autocommit=True, **creds
        )

        app.source = relations_pymysql.Source(
            app.unifist, schema=app.schema, autocommit=True, **creds
        )

    unum_source = unum_base.AppSource(app.logger, app.redis)

    unum_app = unum_ledger.App.one(who=WHO).retrieve(False)

    if not unum_app:
        unum_app = unum_source.journal_change("create", unum_ledger.App(who=WHO))

    unum_source.journal_change("update", unum_app, {"meta": yaml.safe_load(META)})

    def ping():
        app.source.connection.ping(True)

    app.before_request(ping)

    api.add_resource(Health, '/health')

    relations_restx.attach(api, service, relations.models(unum_feelz, unum_feelz.Base))

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
