"""
Module for the Subnet Queue
"""

# pylint: disable=no-self-use

import time
import random
import datetime

import redis

import micro_logger
import relations_rest

import unum_base
import unum_ledger
import unum_feelz

import prometheus_client

REGISTRY = prometheus_client.CollectorRegistry()

PROCESS = prometheus_client.Gauge("process_seconds", "Time to complete a processing task", registry=REGISTRY)
ACTS = prometheus_client.Summary("acts_created", "Acts created")

WHO = "feelz"
NAME = f"{WHO}-cron"

class Cron(unum_base.AppSource): # pylint: disable=too-few-public-methods
    """
    Cron class to run the processing
    """

    app = None

    def __init__(self):

        self.name = NAME
        self.unifist = unum_feelz.Base.SOURCE

        self.logger = micro_logger.getLogger(self.name)

        relations_rest.Source(unum_ledger.Base.SOURCE, url=f"http://api.{unum_ledger.Base.SOURCE}")
        self.source = relations_rest.Source(self.unifist, url=f"http://api.{self.unifist}")

        self.redis = redis.Redis(host=f'redis.{unum_ledger.Base.SOURCE}', encoding="utf-8", decode_responses=True)

    def is_active(self, entity_id):
        """
        Checks to see if an enity is active at this time
        """

        entity = unum_ledger.Entity.one(
            id=entity_id,
            status="active"
        ).retrieve(False)

        if not entity:
            return False

        if not unum_ledger.Herald.one(
            entity_id=entity_id,
            app_id=self.app.id,
            status="active"
        ).retrieve(False):
            return False

        now = datetime.datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds = (now - midnight).seconds

        if entity.meta__talk__after and seconds < entity.meta__talk__after:
            return False

        if entity.meta__talk__before and seconds > entity.meta__talk__before:
            return False

        return True

    def schedule_quepasachecks(self):
        """
        Schedules quepasa check ins
        """

        now = time.time()

        for quepasa in unum_feelz.QuePasa.many(status="active"):

            if not self.is_active(quepasa.entity_id):
                continue

            if unum_feelz.QuePasaCheck.one(
                entity_id=quepasa.entity_id,
                when__gt=now,
                when__lt=now+quepasa.when_max
            ).retrieve(False) is None:

                # Create a new check in

                quepasacheck = self.journal_change("create", unum_feelz.QuePasaCheck(
                    entity_id=quepasa.entity_id,
                    when=now+random.randint(quepasa.when_min, quepasa.when_max),
                    status="requested"
                ))

                # And reject any old ones still out that

                rejected = 0

                for old in unum_feelz.QuePasaCheck.many(
                    entity_id=quepasa.entity_id,
                    when__lt=now,
                    status="active"
                ):
                    rejected += self.journal_change("update", old, {"status": "rejected"})

                self.logger.info("quepasacheck", extra={
                    "quepasacheck": quepasacheck.export(),
                    "rejected": rejected
                })

    def activate_quepasachecks(self):
        """
        Activates the request for input
        """

        now = time.time()

        for quepasacheck in unum_feelz.QuePasaCheck.many(status="requested", when__lte=now):

            if not self.is_active(quepasacheck.entity_id):
                continue

            if unum_feelz.QuePasa.one(
                entity_id=quepasacheck.entity_id,
                status="active"
            ).retrieve(False) is None:
                continue

            text = "how are you?"

            self.create_act(
                entity_id=quepasacheck.entity_id,
                app_id=self.app.id,
                when=int(time.time()),
                what={
                    "base": "statement",
                    "command": "quepasacheck",
                    "id": quepasacheck.id,
                    "meme": "?",
                    "text": text
                }
            )

            self.journal_change("update", quepasacheck, {"status": "active"})

    def schedule_ugoodchecks(self):
        """
        Schedules ugood check ins
        """

        now = time.time()

        for ugood in unum_feelz.Ugood.many(status="active"):

            if not self.is_active(ugood.to_id):
                continue

            if unum_feelz.UgoodCheck.one(
                from_id=ugood.from_id,
                to_id=ugood.to_id,
                when__gt=now,
                when__lt=now+ugood.when_max
            ).retrieve(False) is None:

                ugoodcheck = self.journal_change("create", unum_feelz.UgoodCheck(
                    from_id=ugood.from_id,
                    to_id=ugood.to_id,
                    when=now+random.randint(ugood.when_min, ugood.when_max),
                    status="requested"
                ))

                for old in unum_feelz.UgoodCheck.many(
                    from_id=ugood.from_id,
                    to_id=ugood.to_id,
                    when__lt=now,
                    status="active"
                ):
                    rejected += self.journal_change("update", old, {"status": "rejected"})

                self.logger.info("ugoodcheck", extra={
                    "ugoodcheck": ugoodcheck.export(),
                    "rejected": rejected
                })

    def activate_ugoodchecks(self):
        """
        Requests ugood check ins
        """

        now = time.time()

        for ugoodcheck in unum_feelz.UgoodCheck.many(status="requested", when__lte=now):

            if not self.is_active(ugoodcheck.to_id):
                continue

            if unum_feelz.Ugood.one(
                from_id=ugoodcheck.from_id,
                to_id=ugoodcheck.to_id,
                status="active"
            ).retrieve(False) is None:
                continue

            text = f"how is {{entity:{ugoodcheck.from_id}}}?"

            self.create_act(
                entity_id=ugoodcheck.to_id,
                app_id=self.app.id,
                when=int(time.time()),
                what={
                    "base": "statement",
                    "command": "ugoodcheck",
                    "id": ugoodcheck.id,
                    "meme": "?",
                    "text": text
                }
            )

            self.journal_change("update", ugoodcheck, {"status": "active"})

    @PROCESS.time()
    def process(self):
        """
        Loads subnets and pushes onto the queue
        """

        self.schedule_quepasachecks()
        self.activate_quepasachecks()
        self.schedule_ugoodchecks()
        self.activate_ugoodchecks()

    def run(self):
        """
        Runs through s process
        """

        self.app = unum_ledger.App.one(who=WHO).retrieve()
        self.process()

        #prometheus_client.push_to_gateway("push.prometheus:9091", "feelz/cron", registry=REGISTRY)
