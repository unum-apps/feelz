"""
Module for the Daemon
"""

# pylint: disable=no-self-use,too-many-locals,too-many-branches,too-many-statements,len-as-condition,line-too-long

import os
import time

import micro_logger
import json
import yaml
import redis

import relations_rest

import prometheus_client

import unum_base
import unum_ledger
import unum_feelz

PROCESS = prometheus_client.Gauge("process_seconds", "Time to complete a processing task")
FACTS = prometheus_client.Summary("facts_processed", "Facts processed")
ACTS = prometheus_client.Summary("acts_created", "Acts created")

WHO = "feelz"
NAME = f"{WHO}-daemon"
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

STATUS_EMOJIS = {
    "requested": "❓",
    "active": "👍",
    "inactive": "♥️",
    "rejected": "👎",
    "excepted": "❗"
}

EMOJI_STATES = {
    "❓": "unable",
    "👍": "good",
    "♥️": "able",
    "👎": "bad",
    "❗": "unstable",
    "?": "unable",
    "+": "good",
    "*": "able",
    "-": "bad",
    "!": "unstable"
}

class Daemon(unum_base.AppSource): # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """
    Daemon class
    """

    def __init__(self):

        self.name = self.group = NAME
        self.unifist = unum_feelz.Base.SOURCE
        self.group_id = os.environ["K8S_POD"]

        self.sleep = int(os.environ.get("SLEEP", 5))

        self.logger = micro_logger.getLogger(self.name)

        relations_rest.Source(unum_ledger.Base.SOURCE, url=f"http://api.{unum_ledger.Base.SOURCE}")
        self.source = relations_rest.Source(self.unifist, url=f"http://api.{self.unifist}")

        self.redis = redis.Redis(host=f'redis.{unum_ledger.Base.SOURCE}', encoding="utf-8", decode_responses=True)

        self.app = unum_ledger.App.one(who=WHO).retrieve(False)

        if not self.app:
            self.app = self.journal_change("create", unum_ledger.App(who=WHO))

        self.journal_change("update", self.app, {"meta": yaml.safe_load(META)})

        if (
            not self.redis.exists("ledger/fact") or
            self.group  not in [group["name"] for group in self.redis.xinfo_groups("ledger/fact")]
        ):
            self.redis.xgroup_create("ledger/fact", self.group, mkstream=True)

    def is_fam(self, from_id, to_id):
        """
        Checks to see from from to to is fam
        """

        # Connected and active

        return unum_feelz.Fam.one(
            from_id=from_id,
            to_id=to_id,
            status="active"
        ).retrieve(False) is not None

    def command_state(self, instance):
        """
        Processes a state
        """

        # Get the common values and throw them into local vars for good DX

        entity_id = instance["entity_id"]
        usage = instance["what"]["usage"]
        values = instance["what"].get("values", {})
        base = "statement"
        meme = "*"

        # Assume there's not a related muy bien

        muy_bien = False

        # If we're recording a state

        if usage == "record":

            # Set what to a variable cuz ezer

            what = EMOJI_STATES.get(values["state"][0], values["state"])

            # Create the state with now as when

            state = self.journal_change("create", unum_feelz.State(
                entity_id=entity_id,
                when=time.time(),
                what=what
            ))

            # Log and message it

            self.logger.info("state", extra={"state": state.export()})
            text = f"recorded your current state as {what}."
            base = "reaction"
            meme = "+"

            if what in ["bad", "unstable"]:
                muy_bien = True

        elif usage.startswith("list"):

            now = time.time()
            when_min = when_max = 0

            if usage == "list_since":

                when_min = values["since"]
                text = f"your states from {self.encode_time(when_min) or 'now'} are:"

            elif usage == "list_from_to":

                when_min = values["from"]
                when_max = values["to"]
                when_from = self.encode_time(when_min) or 'now'
                when_to = self.encode_time(when_max) or 'now'
                text = f"your states from {when_from} to {when_to} are:"

            for state in unum_feelz.State.many(
                entity_id=entity_id,
                when__gte=now - when_min,
                when__lte=now - when_max
            ):
                when = self.encode_time(now - state.when) or "now"
                text += f"\n- {when} - {state.what}"

        self.create_act(
            entity_id=entity_id,
            app_id=self.app.id,
            when=int(time.time()),
            what={
                "base": base,
                "meme": meme,
                "text": text
            },
            meta={"ancestor": instance["meta"]}
        )

        if muy_bien:
            self.do_muybien(entity_id, instance["meta"])

    def command_mood(self, instance):
        """
        Processes a mood
        """

        entity_id = instance["entity_id"]
        usage = instance["what"]["usage"]
        values = instance["what"].get("values", {})
        base = "statement"
        meme = "*"

        if usage == "record":

            what = values["mood"]

            mood = self.journal_change("create", unum_feelz.Mood(
                entity_id=entity_id,
                when=time.time(),
                what=what
            ))

            self.logger.info("mood", extra={"mood": mood.export()})

            text = f"recorded your current mood as {what}."
            base = "reaction"
            meme = "+"

        else:

            now = time.time()
            when_min = when_max = 0

            if usage == "list_since":

                when_min = values["since"]
                text = f"your moods from {self.encode_time(when_min) or 'now'} are:"

            elif usage == "list_from_to":

                when_min = values["from"]
                when_max = values["to"]
                text = f"your moods from {self.encode_time(when_min) or 'now'} to {self.encode_time(when_max) or 'now'} are:"

            for mood in unum_feelz.Mood.many(
                entity_id=entity_id,
                when__gte=now - when_min,
                when__lte=now - when_max
            ):
                when = self.encode_time(now - mood.when) or "now"
                text += f"\n- {mood.what} - {when}"

        self.create_act(
            entity_id=entity_id,
            app_id=self.app.id,
            when=int(time.time()),
            what={
                "base": base,
                "meme": meme,
                "text": text
            },
            meta={"ancestor": instance["meta"]}
        )

    def command_diary(self, instance):
        """
        Processes a mood
        """

        entity_id = instance["entity_id"]
        usage = instance["what"]["usage"]
        values = instance["what"].get("values", {})
        base = "statement"
        meme = "*"

        if usage == "record":

            what = values["thoughts"]

            diary = self.journal_change("create", unum_feelz.Diary(
                entity_id=entity_id,
                when=time.time(),
                what={"text": what}
            ))

            self.logger.info("diary", extra={"diary": diary.export()})

            text = f"recorded your current diary - {what}"
            base = "reaction"
            meme = "+"

        elif usage.startswith("list"):

            now = time.time()
            when_min = when_max = 0

            if usage == "list_since":

                when_min = values["since"]
                text = f"your diaries from {self.encode_time(when_min) or 'now'} are:"

            elif usage == "list_from_to":

                when_min = values["from"]
                when_max = values["to"]
                text = f"your diaries from {self.encode_time(when_min) or 'now'} to {self.encode_time(when_max) or 'now'} are:"

            for diary in unum_feelz.Diary.many(
                entity_id=entity_id,
                when__gte=now - when_min,
                when__lte=now - when_max
            ):
                when = self.encode_time(now - diary.when) or "now"
                text += f"\n- {when} - {diary.what__text}"

        self.create_act(
            entity_id=entity_id,
            app_id=self.app.id,
            when=int(time.time()),
            what={
                "base": base,
                "meme": meme,
                "text": text
            },
            meta={"ancestor": instance["meta"]}
        )

    def command_quepasa(self, instance):
        """
        Processes a quepasa
        """

        entity_id = instance["entity_id"]
        usage = instance["what"]["usage"]
        values = instance["what"].get("values", {})
        base = "reaction"
        meme = "+"

        quepasa = unum_feelz.QuePasa.one(entity_id=entity_id).retrieve(False)

        if usage.startswith("start"):

            when_min = when_max = 0
            before = "8h"
            after = "20h"

            if usage == "start_every":

                when_min = when_max = values["every"]
                when_every = self.encode_time(when_min)
                text = f"I will check on you every {when_every}"

            elif usage == "start_from_to":

                when_min = values["from"]
                when_max = values["to"]
                when_from = self.encode_time(when_min)
                when_to = self.encode_time(when_max)
                text = f"I will check on you from every {when_from} to every {when_to}"

            if quepasa:

                self.journal_change("update", quepasa, change={
                    "when_min": when_min,
                    "when_max": when_max,
                    "status": "active"
                })

            else:

                quepasa = self.journal_change("create", unum_feelz.QuePasa(
                    entity_id=entity_id,
                    when_min=when_min,
                    when_max=when_max,
                    status="active",
                    meta={
                        "before": self.decode_time("8h"),
                        "after": self.decode_time("20h")
                    }
                ))

        elif usage == "stop":

            if not quepasa:

                text = "I have never checked in on you."

            elif quepasa.status == "inactive":

                text = "I am not checking in on you."

            elif quepasa.status == "active":

                self.journal_change("update", quepasa, change={
                    "status": "inactive"
                })

                text = "I will not check on you."

        elif usage == "current":

            base = "statement"
            meme = "*"

            if not quepasa or quepasa.status == "inactive":

                text = "I am not checking in on you."

            elif quepasa.status == "active":

                if quepasa.when_min == quepasa.when_max:

                    when_every = self.encode_time(quepasa.when_min)
                    text = f"I will check on you every {when_every}"

                else:

                    when_from = self.encode_time(quepasa.when_min)
                    when_to = self.encode_time(quepasa.when_max)
                    text = f"I will check on you from every {when_from} to every {when_to}"

                now = int(time.time())

                quepasa_check = unum_feelz.QuePasaCheck.one(
                    entity_id=quepasa.entity_id,
                    status="scheduled"
                ).retrieve(False)

                if quepasa_check:
                    next = self.encode_time(max(quepasa_check.when - now, 0)) or "now"
                    text += f" - next check {next}"

        self.create_act(
            entity_id=entity_id,
            app_id=self.app.id,
            when=int(time.time()),
            what={
                "base": base,
                "meme": meme,
                "text": text
            },
            meta={"ancestor": instance["meta"]}
        )

    def command_fam(self, instance):
        """
        Processes an is fam
        """

        entity_id = instance["entity_id"]
        usage = instance["what"]["usage"]
        values = instance["what"].get("values", {})
        base = "statement"
        meme = "*"

        if usage in ["start", "stop"]:

            from_id = entity_id
            to_id = entity_id = values["who"]

            fam = unum_feelz.Fam.one(from_id=from_id, to_id=to_id).retrieve(False)

            if usage == "start":

                base = "reaction"

                if not self.is_active(to_id):

                    meme = "-"
                    text = f"{{entity:{to_id}}} is not a member of {self.app.meta__title}"

                else:

                    if fam:

                        if fam.status not in ["requested", "active"]:
                            self.journal_change("update", fam, change={"status": "requested"})

                    else:

                        fam = self.journal_change("create", unum_feelz.Fam(from_id=from_id, to_id=to_id, status="requested"))

                    self.logger.info("fam", extra={"fam": fam.export()})

                    meme = "?"
                    text = f"{{entity:{from_id}}} requests you're fam. 👍 to confirm, 👎 to deny"

            elif usage == "stop":

                meme = "+"

                if fam:

                    if fam.status == "active":
                        self.journal_change("update", fam, change={"status": "inactive"})

                    text = f"{{entity:{to_id}}} is not currently fam."

                else:

                    text = f"{{entity:{to_id}}} was never fam."

                self.logger.info("fam", extra={"fam": fam.export()})

        elif usage == "current":

            text = "your current fam are:"

            for fam in unum_feelz.Fam.many(from_id=entity_id):
                entity = unum_ledger.Entity.one(fam.to_id)
                text += f"\n{STATUS_EMOJIS[fam.status]} {entity.who} - {fam.status}"

        self.create_act(
            entity_id=entity_id,
            app_id=self.app.id,
            when=int(time.time()),
            what={
                "base": base,
                "meme": meme,
                "text": text
            },
            meta={"ancestor": instance["meta"]}
        )

    def reaction_fam(self, instance):
        """
        Processes an is fam
        """

        usage = instance["what"]["ancestor"]["usage"]

        # We're only reacting to starts

        if usage != "start":
            return

        entity_id = instance["entity_id"]           # Who reacted
        ancestor = instance["what"]["ancestor"]    # What was reacted to
        from_id = ancestor["entity_id"]             # Who reqested the fam
        values = ancestor.get("values", {})
        to_id = values["who"]                       # Who was requested to
        base = "reaction"
        meme = "+"

        # We only care about the reaction from the person who is being requested to

        if to_id != entity_id:
            return

        # If the person being requested to is no longer active, we can't do this

        if not self.is_active(to_id):

            meme = "-"
            text = f"{{entity:{to_id}}} is not a member of {self.app.meta__title}"

        else:

            # Get the fam in requested mode

            fam = unum_feelz.Fam.one(from_id=from_id, to_id=to_id).retrieve()

            # Figure out the decision or bail if still undecided

            if instance["what"]["meme"] == "+":
                self.journal_change("update", fam, change={"status": "active"})
            elif instance["what"]["meme"] == "-":
                self.journal_change("update", fam, change={"status": "rejected"})
            else:
                return

            # Update it, log it, message it

            self.logger.info("fam", extra={"fam": fam.export()})
            text = f"{fam.status} fam with {{entity:{from_id}}}"

        # Respond to the original message

        self.create_act(
            entity_id=to_id,
            app_id=self.app.id,
            when=int(time.time()),
            what={
                "base": base,
                "meme": meme,
                "text": text
            },
            meta={"ancestor": instance["meta"]["ancestor"]}
        )

    def command_ugood(self, instance):
        """
        Requests confirmation for an ugood
        """

        # Get the common values and throw them into local vars for good DX

        entity_id = instance["entity_id"]
        usage = instance["what"]["usage"]
        values = instance["what"].get("values", {})
        meme_in = instance["what"]["meme"]
        base = "reaction"
        meme_out = "*"

        if meme_in == "!":

            from_id = entity_id
            to_id = values["who"]

            ugood = unum_feelz.Ugood.one(from_id=from_id, to_id=to_id).retrieve(False)

            if usage.startswith("start"):

                entity_id = to_id

                if not self.is_active(to_id):

                    meme_out = "-"
                    text = f"{{entity:{to_id}}} is not a member of {self.app.meta__title}"

                elif not self.is_fam(from_id, to_id):

                    meme_out = "-"
                    text = f"{{entity:{to_id}}} is not fam"

                else:

                    meme_out = "?"
                    when_min = when_max = 0

                    if usage == "start_every":

                        when_min = when_max = values["every"]
                        text = f"{{entity:{from_id}}} requets a ugood every {self.encode_time(when_min)}."

                    elif usage == "start_from_to":

                        when_min = values["from"]
                        when_max = values["to"]
                        text = f"{{entity:{from_id}}} requests a ugood every {self.encode_time(when_min)} to every {self.encode_time(when_max)}"

                    if ugood:

                        self.journal_change("update", ugood, change={
                            "when_min": when_min,
                            "when_max": when_max,
                            "status": "requested"
                        })

                    else:

                        ugood = self.journal_change("create", unum_feelz.Ugood(
                            from_id=from_id,
                            to_id=to_id,
                            when_min=when_min,
                            when_max=when_max,
                            status="requested"
                        ))

                    self.logger.info("ugood", extra={"ugood": ugood.export()})

                    text += " 👍 to confirm, 👎 to deny"

            elif usage == "stop":

                meme_out = "+"

                if ugood:

                    self.journal_change("update", ugood, change={"status": "inactive"})

                    text = f"{{entity:{to_id}}} will not check in on you"

                else:

                    text = f"{{entity:{to_id}}} was not checking in on you."

                self.logger.info("ugood", extra={"ugood": ugood.export()})

        elif usage == "current":

            base = "statement"

            text = "your current ugood are:"

            for ugood in unum_feelz.Ugood.many(from_id=entity_id):

                entity = unum_ledger.Entity.one(ugood.to_id)

                if ugood.when_min == ugood.when_max:

                    when_every = self.encode_time(ugood.when_min)
                    text = f"\n- {STATUS_EMOJIS[ugood.status]} {entity.who} will check on you every {when_every} - {ugood.status}"

                else:

                    when_from = self.encode_time(ugood.when_min)
                    when_to = self.encode_time(ugood.when_max)
                    text = f"- {STATUS_EMOJIS[ugood.status]} {entity.who} will check on you from every {when_from} to every {when_to} - {ugood.status}"

                if ugood.status == "active":

                    now = int(time.time())

                    ugood_check = unum_feelz.UgoodCheck.one(
                        from_id=ugood.from_id,
                        to_id=ugood.to_id,
                        status="requested",
                        when__gt=now
                    ).retrieve(False)

                    if ugood_check:
                        next = self.encode_time(max(ugood_check.when - now, 0)) or "now"
                        text += f" - next check {next}"

        self.create_act(
            entity_id=entity_id,
            app_id=self.app.id,
            when=int(time.time()),
            what={
                "meme": meme_out,
                "base": base,
                "text": text
            },
            meta={"ancestor": instance["meta"]}
        )

    def reaction_ugood(self, instance):
        """
        Comletes an ugood
        """

        usage = instance["what"]["ancestor"]["usage"]

        # We're only reacting to starts

        if not usage.startswith("start"):
            return

        entity_id = instance["entity_id"]           # Who reacted
        ancestor = instance["what"]["ancestor"]    # What was reacted to
        from_id = ancestor["entity_id"]             # Who reqested the fam
        values = ancestor.get("values", {})
        to_id = values["who"]                       # Who was requested to
        base = "reaction"
        meme_in = instance["what"]["meme"]
        meme_out = "-"

        # We only care about the reaction from the person who is being requested to

        if to_id != entity_id:
            return

        # If the person being requested to is no longer active, we can't do this

        if not self.is_active(to_id):

            text = f"{{entity:{to_id}}} is not a member of {self.app.meta__title}"

        elif not self.is_fam(from_id, to_id):

            text = f"{{entity:{to_id}}} is not fam."

        else:

            # Get the fam in requested mode

            ugood = unum_feelz.Ugood.one(from_id=from_id, to_id=to_id).retrieve()

            # Figure out the decision or bail if still undecided

            if meme_in == "+":
                self.journal_change("update", ugood, change={"status": "active"})
                meme_out = "+"
                text = f"{{entity:{to_id}}} will check in on you"
            elif meme_in == "-":
                self.journal_change("update", ugood, change={"status": "rejected"})
                text = f"{{entity:{to_id}}} will not check in on you"
            else:
                return

            # Update it, log it, message it

            self.logger.info("ugood", extra={"ugood": ugood.export()})

        # Respond to the original message

        self.create_act(
            entity_id=from_id,
            app_id=self.app.id,
            when=int(time.time()),
            what={
                "base": base,
                "meme": meme_out,
                "text": text
            },
            meta={"ancestor": instance["meta"]["ancestor"]}
        )

    def reaction_quepasacheck(self, instance):
        """
        Reacts to a queue pasa check
        """

        entity_id = instance["entity_id"]          # Who reacted
        ancestor = instance["what"]["ancestor"]    # What was reacted to
        id = ancestor["id"]                        # What was requested
        emoji = instance["what"].get("emoji")
        text = instance["what"].get("text")
        base_in = instance["what"]["base"]
        base_out = "reaction"
        meme_in = instance["what"]["meme"]
        meme_out = "+"

        # Assume there's not a related muy bien

        muy_bien = False

        # Get the check

        quepasa_check = unum_feelz.QuePasaCheck.one(id=id)

        # If it doesn't match, bail

        if entity_id != quepasa_check.entity_id:
            return

        # IF we're recieving someting the request is fulfilled,
        # more can be added, but this is a success

        if quepasa_check.status != "inactive":
            self.journal_change("update", quepasa_check, change={"status": "inactive"})

        # Set up the reference

        meta = {"quepasa_check":  quepasa_check.id}

        if base_in == "reaction":

            if meme_in in EMOJI_STATES and emoji in EMOJI_STATES:

                what = EMOJI_STATES[meme_in]

                state = self.journal_change("create", unum_feelz.State(
                    entity_id=entity_id,
                    when=time.time(),
                    what=what,
                    meta=meta
                ))

                if what in ["bad", "unstable"]:
                    muy_bien = True

                self.logger.info("state", extra={
                    "state": state.export(),
                    "muy_bien": muy_bien
                })

                text = f"recorded your current state as {what}."

            else:

                what = emoji

                mood = self.journal_change("create", unum_feelz.Mood(
                    entity_id=entity_id,
                    when=time.time(),
                    what=what,
                    meta=meta
                ))

                self.logger.info("mood", extra={"mood": mood.export()})

                text = f"recorded your current mood as {what}."

        else:

            what = instance["what"]["text"]

            diary = self.journal_change("create", unum_feelz.Diary(
                entity_id=entity_id,
                when=time.time(),
                what={"text": what},
                meta=meta
            ))

            self.logger.info("diary", extra={"diary": diary.export()})

            text = f"recorded your thoughts - {what}"

        self.create_act(
            entity_id=entity_id,
            app_id=self.app.id,
            when=int(time.time()),
            what={
                "base": base_out,
                "meme": meme_out,
                "text": text
            },
            meta={"ancestor": instance["meta"]["ancestor"]}
        )

        if muy_bien:
            self.do_muybien(entity_id, instance["meta"]["ancestor"])

    def reaction_ugoodcheck(self, instance):
        """
        Reacts to a ugood a check
        """

        entity_id = instance["entity_id"]          # Who reacted
        ancestor = instance["what"]["ancestor"]    # What was reacted to
        id = ancestor["id"]                        # What was requested
        emoji = instance["what"].get("emoji")
        text = instance["what"].get("text")
        base_in = instance["what"]["base"]
        base_out = "reaction"
        meme_in = instance["what"]["meme"]
        meme_out = "+"

        # Assume there's not a related muy bien

        muy_bien = False

        if not self.is_active(entity_id):
            return

        ugood_check = unum_feelz.UgoodCheck.one(id=id)

        if entity_id not in [ugood_check.from_id, ugood_check.to_id]:
            return

        if ugood_check.status != "inactive":
            self.journal_change("update", ugood_check, change={"status": "inactive"})

        meta = {"ugood_check":  ugood_check.id}

        whose = "your"

        if entity_id != ugood_check.from_id:
            meta["entity_id"] = entity_id
            whose = f"{{entity:{ugood_check.from_id}}}'s"

        if base_in == "reaction":

            if meme_in in EMOJI_STATES and emoji in EMOJI_STATES:

                what = EMOJI_STATES[meme_in]

                state = self.journal_change("create", unum_feelz.State(
                    entity_id=ugood_check.from_id,
                    when=time.time(),
                    what=what,
                    meta=meta
                ))

                if what in ["bad", "unstable"]:
                    muy_bien = True

                self.logger.info("state", extra={
                    "state": state.export(),
                    "muy_bien": muy_bien
                })

                text = f"recorded {whose} current state as {what}."

            else:

                what = emoji

                mood = self.journal_change("create", unum_feelz.Mood(
                    entity_id=ugood_check.from_id,
                    when=time.time(),
                    what=what,
                    meta=meta
                ))

                self.logger.info("mood", extra={"mood": mood.export()})

                text = f"recorded {whose} current mood as {what}."

        else:

            what = instance["what"]["text"]

            diary = self.journal_change("create", unum_feelz.Diary(
                entity_id=ugood_check.from_id,
                when=time.time(),
                what={"text": what},
                meta=meta
            ))

            self.logger.info("diary", extra={"diary": diary.export()})

            text = f"recorded {whose} thoughts - {what}"

        self.create_act(
            entity_id=entity_id,
            app_id=self.app.id,
            when=int(time.time()),
            what={
                "base": base_out,
                "meme": meme_out,
                "text": text
            },
            meta={"ancestor": instance["meta"]["ancestor"]}
        )

        if muy_bien:
            self.do_muybien(entity_id, instance["meta"]["ancestor"])

    def command_muybien(self, instance):
        """
        Processes a muybien
        """

        entity_id = instance["entity_id"]
        usage = instance["what"]["usage"]
        values = instance["what"].get("values", {})
        base = "reaction"
        meme = "+"

        muybien = unum_feelz.MuyBien.one(entity_id=entity_id).retrieve(False)

        if usage == "start":

            when = values["amount"]
            deduct = self.encode_time(when)

            text = f"for every bad state, I will deduct {deduct} from your next ugood check"

            if muybien:

                self.journal_change("update", muybien, change={"when": when, "status": "active"})

            else:

                muybien = self.journal_change("create", unum_feelz.MuyBien(
                    entity_id=entity_id,
                    when=when,
                    status="active"
                ))

        elif usage == "stop":

            if not muybien:

                text = "I have never adjusted ugood checks for you."

            elif muybien.status == "inactive":

                text = "I am not adjusting ugood checks for you."

            elif muybien.status == "active":

                self.journal_change("update", muybien, change={"status": "inactive"})
                text = "I will not adjust ugood checks for you."

        elif usage == "current":

            meme = "*"

            if not muybien or muybien.status == "inactive":

                text = "I am not adjusting ugood checks for you."

            elif muybien.status == "active":

                deduct = self.encode_time(muybien.when)
                text = "for every bad state, I will deduct {deduct} from your next ugood check"

        self.create_act(
            entity_id=entity_id,
            app_id=self.app.id,
            when=int(time.time()),
            what={
                "meme": meme,
                "base": base,
                "text": text
            },
            meta={"ancestor": instance["meta"]}
        )

    def do_muybien(self, entity_id, reference):
        """
        See if there's a muy bien and execute if so
        """

        muybien = unum_feelz.MuyBien.one(entity_id=entity_id, status="active").retrieve(False)

        if not muybien:
            return

        ugood_checks = unum_feelz.UgoodCheck.many(from_id=entity_id, status="requested").sort("when")

        if not len(ugood_checks):
            return

        ugood_check = ugood_checks[0]
        self.journal_change("update", ugood_check, change={"when": ugood_check.when - muybien.when})

        now = int(time.time())

        by = self.encode_time(muybien.when)
        next = self.encode_time(max(ugood_check.when - now, 0)) or "now"
        to_id = ugood_check.to_id

        text = f"I reduced {{entity:{to_id}}}'s next check by {by} to {next}"

        self.create_act(
            entity_id=entity_id,
            app_id=self.app.id,
            when=int(time.time()),
            what={
                "meme": "+",
                "base": "reaction",
                "text": text
            },
            meta={"ancestor": reference}
        )

    def do_command(self, instance):
        """
        Perform the command
        """

        name = instance["what"]["command"]

        if name == "state":
            self.command_state(instance)
        elif name == "mood":
            self.command_mood(instance)
        elif name == "diary":
            self.command_diary(instance)
        elif name == "fam":
            self.command_fam(instance)
        elif name == "quepasa":
            self.command_quepasa(instance)
        elif name == "ugood":
            self.command_ugood(instance)
        elif name == "muybien":
            self.command_muybien(instance)

    def do_reaction(self, instance):
        """
        Perform the who
        """

        name = instance["what"]["ancestor"]["command"]

        if name == "fam":
            self.reaction_fam(instance)
        elif name == "ugood":
            self.reaction_ugood(instance)
        elif name == "quepasacheck":
            self.reaction_quepasacheck(instance)
        elif name == "ugoodcheck":
            self.reaction_ugoodcheck(instance)

    @PROCESS.time()
    def process(self):
        """
        Reads people off the queue and logs them
        """

        message = self.redis.xreadgroup(self.group, self.group_id, {"ledger/fact": ">"}, count=1, block=1000*self.sleep)

        if not message:
            return

        if "fact" in message[0][1][0][1]:

            instance = json.loads(message[0][1][0][1]["fact"])
            self.logger.info("fact", extra={"fact": instance})
            FACTS.observe(1)

            # Need to be cleared to see this person's data and avoid errors

            if (
                not self.is_active(instance["what"].get("entity_id")) or
                instance["what"].get("error") or
                instance["what"].get("errors")
            ):
                return

            # If we are responding to a command, do that

            if (
                instance["what"].get("ancestor", {}).get("base") == "command" and
                WHO in instance["what"].get("ancestor", {}).get("apps", [])
            ):
                self.do_reaction(instance)

            # Else if we are a command do that

            elif (
                instance["what"]["base"] == "command" and
                WHO in instance["what"].get("apps", [])
            ):
                self.do_command(instance)

        self.redis.xack("ledger/fact", self.group, message[0][1][0][0])

    def run(self):
        """
        Main loop with sleep
        """

        prometheus_client.start_http_server(80)

        while True:

            self.process()
