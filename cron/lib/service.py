"""
Module for the Subnet Queue
"""

# pylint: disable=no-self-use

import time
import json
import random
import datetime

import redis

import micro_logger
import relations_rest

import unum_ledger
import unum_tehfeelz

import prometheus_client

REGISTRY = prometheus_client.CollectorRegistry()

PROCESS = prometheus_client.Gauge("process_seconds", "Time to complete a processing task", registry=REGISTRY)
ACTS = prometheus_client.Summary("acts_created", "Acts created")

WHO = "tehfeelz"
NAME = f"{WHO}-daemon"

class Cron: # pylint: disable=too-few-public-methods
    """
    Cron class to run the processing
    """

    def __init__(self):

        self.name = NAME
        self.unifist = unum_tehfeelz.Base.SOURCE

        self.logger = micro_logger.getLogger(self.name)

        relations_rest.Source(unum_ledger.Base.SOURCE, url=f"http://api.{unum_ledger.Base.SOURCE}")
        self.source = relations_rest.Source(self.unifist, url=f"http://api.{self.unifist}")

        self.app = unum_ledger.App.one(who=WHO).retrieve()

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

    def act(self, **act):
        """
        Creates an act if needed
        """

        if unum_ledger.Herald.one(
            entity_id=act["entity_id"],
            app_id=self.app.id
        ).retrieve(False) is None:
            return

        act = unum_ledger.Act(**act).create()

        self.logger.info("act", extra={"act": {"id": act.id}})
        ACTS.observe(1)
        self.redis.xadd("ledger/act", fields={"act": json.dumps(act.export())})

    def schedule_quepasachecks(self):
        """
        Schedules quepasa check ins
        """

        now = time.time()

        for quqpasa in unum_tehfeelz.QuePasa.many(status="active"):

            if not self.is_active(quqpasa.entity_id):
                continue

            if unum_tehfeelz.QuePasaCheck.one(
                entity_id=quqpasa.entity_id,
                when__gt=now
            ).retrieve(False) is None:

                # Create a new check in

                quepasa_check = unum_tehfeelz.QuePasaCheck(
                    entity_id=quqpasa.entity_id,
                    when=now+random.randint(quqpasa.when_min, quqpasa.when_max),
                    status="requested"
                ).create()

                # And reject any old ones still out that

                rejected = unum_tehfeelz.QuePasaCheck.many(
                    entity_id=quqpasa.entity_id,
                    when__lt=now,
                    status="active"
                ).set(status="rejected").update()

                self.logger.info("quepasa_check", extra={
                    "quepasa_check": quepasa_check.export(),
                    "rejected": rejected
                })

    def activate_quepasachecks(self):
        """
        Activates the request for input
        """

        now = time.time()

        for quepasa_check in unum_tehfeelz.QuePasaCheck.many(status="requested", when__lte=now):

            if not self.is_active(quepasa_check.entity_id):
                continue

            if unum_tehfeelz.QuePasa.one(
                entity_id=quepasa_check.entity_id,
                status="active"
            ).retrieve(False) is None:
                continue

            text = f"how are you?"

            self.act(
                entity_id=quepasa_check.entity_id,
                app_id=self.app.id,
                when=int(time.time()),
                what={
                    "base": "statement",
                    "command": "quepasacheck",
                    "id": quepasa_check.id,
                    "meme": "?",
                    "text": text
                }
            )

            quepasa_check.status = "active"
            quepasa_check.update()

    def schedule_ugoodchecks(self):
        """
        Schedules ugood check ins
        """

        now = time.time()

        for ugood in unum_tehfeelz.Ugood.many(status="active"):

            if not self.is_active(ugood.to_id):
                continue

            if unum_tehfeelz.UgoodCheck.one(
                from_id=ugood.from_id,
                to_id=ugood.to_id,
                when__gt=now
            ).retrieve(False) is None:

                ugood_check = unum_tehfeelz.UgoodCheck(
                    from_id=ugood.from_id,
                    to_id=ugood.to_id,
                    when=now+random.randint(ugood.when_min, ugood.when_max),
                    status="requested"
                ).create()

                rejected = unum_tehfeelz.UgoodCheck.many(
                    from_id=ugood.from_id,
                    to_id=ugood.to_id,
                    when__lt=now,
                    status="active"
                ).set(status="rejected").update()

                self.logger.info("ugood_check", extra={
                    "ugood_check": ugood_check.export(),
                    "rejected": rejected
                })

    def activate_ugoodchecks(self):
        """
        Requests ugood check ins
        """

        now = time.time()

        for ugood_check in unum_tehfeelz.UgoodCheck.many(status="requested", when__lte=now):

            if not self.is_active(ugood_check.to_id):
                continue

            if unum_tehfeelz.Ugood.one(
                from_id=ugood_check.from_id,
                to_id=ugood_check.to_id,
                status="active"
            ).retrieve(False) is None:
                continue

            text = f"how is {{entity:{ugood_check.from_id}}}?"

            self.act(
                entity_id=ugood_check.to_id,
                app_id=self.app.id,
                when=int(time.time()),
                what={
                    "base": "statement",
                    "command": "ugoodcheck",
                    "id": ugood_check.id,
                    "meme": "?",
                    "text": text
                }
            )

            ugood_check.status = "active"
            ugood_check.update()

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

        self.process()


        #prometheus_client.push_to_gateway("push.prometheus:9091", "tehfeelz/cron", registry=REGISTRY)
