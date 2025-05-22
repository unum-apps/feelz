"""
Contains the Models for tehfeelz
"""

import relations
import unum_ledger

class Base(relations.Model):
    """
    Base class for tehfeelz models
    """

    SOURCE = "tehfeelz"

class State(Base):
    """
    How one person is doing at one moment
    """

    id = int
    entity_id = int # Entity checked on
    when = int      # When the check happened
    what = [        # Current state whether good or bad
        "unable",
        "good",
        "able",
        "bad",
        "unstable"
    ]
    meta = dict       # Any special weird data

    UNIQUE = False
    INDEX = "when"
    ORDER = "-when"

relations.OneToMany(unum_ledger.Entity, State)

class Mood(Base):
    """
    How one person is doing at one moment i terms of an emoji
    """

    id = int
    entity_id = int   # Entity checked on
    when = int        # When the check happened
    what = str        # Current mood in terms of emoji
    meta = dict       # Any special weird data

    UNIQUE = False
    INDEX = "when"
    ORDER = "-when"

relations.OneToMany(unum_ledger.Entity, Mood)

class Diary(Base):
    """
    How one person is doing at one moment i terms of words
    """

    id = int
    entity_id = int   # Entity checked on
    when = int        # When the check happened
    what = dict       # Current state in terms of words
    meta = dict       # Any special weird data

    UNIQUE = False
    INDEX = "when"
    ORDER = "-when"

relations.OneToMany(unum_ledger.Entity, Diary)

class Fam(Base):
    """
    One person considers another fam
    """

    id = int
    from_id = int     # Entity reaching out
    to_id = int       # Entity accepting
    status = [        # Current status of the relationship
        "requested",
        "active",
        "inactive",
        "rejected",
        "excepted"
    ]
    meta = dict       # Any special weird data

    UNIQUE = ["from_id", "to_id"]

relations.OneToMany(unum_ledger.Entity, Fam, parent_child="fam_from", child_parent="from_entity", child_field="from_id")
relations.OneToMany(unum_ledger.Entity, Fam, parent_child="fam_to", child_parent="to_entity", child_field="to_id")

class QuePasa(Base):
    """
    The bot will check in on you
    """

    id = int
    entity_id = int   # Entity  accepting
    when_min = int    # Min time to wait before checking in
    when_max = int    # Max time to wait before checking in
    status = [        # Current status of the relationship
        "requested",
        "active",
        "inactive",
        "rejected",
        "excepted"
    ]
    meta = dict       # Any special weird data

    UNIQUE = ["entity_id"]

relations.OneToMany(unum_ledger.Entity, QuePasa)

class QuePasaCheck(Base):
    """
    The bot will check in on you
    """

    id = int
    entity_id = int   # Entity  accepting
    when = int        # Time of the check in
    status = [        # Current status of the check in
        "requested",
        "active",
        "inactive",
        "rejected",
        "excepted"
    ]
    meta = dict       # Any special weird data

    UNIQUE = ["entity_id", "when"]
    INDEX = "when"
    ORDER = "-when"

relations.OneToMany(unum_ledger.Entity, QuePasaCheck)

class Ugood(Base):
    """
    One person will check in on another
    """

    id = int
    from_id = int     # Entity reaching out
    to_id = int       # Entity accepting
    when_min = int    # Min time to wait before checking in
    when_max = int    # Max time to wait before checking in
    status = [        # Current status of the relationship
        "requested",
        "active",
        "inactive",
        "rejected",
        "excepted"
    ]
    meta = dict       # Any special weird data

    UNIQUE = ["from_id", "to_id"]

relations.OneToMany(unum_ledger.Entity, Ugood, parent_child="ugood_from", child_parent="from_entity", child_field="from_id")
relations.OneToMany(unum_ledger.Entity, Ugood, parent_child="ugood_to", child_parent="to_entity", child_field="to_id")

class UgoodCheck(Base):
    """
    One person checking in on another
    """

    id = int
    from_id = int     # Entity reaching out
    to_id = int       # Entity accepting
    when = int        # Time of the check in
    status = [        # Current status of the check in
        "requested",
        "active",
        "inactive",
        "rejected",
        "excepted"
    ]
    meta = dict       # Any special weird data

    UNIQUE = ["from_id", "to_id", "when"]
    INDEX = "when"
    ORDER = "-when"

relations.OneToMany(unum_ledger.Entity, UgoodCheck, parent_child="ugood_check_from", child_parent="from_entity", child_field="from_id")
relations.OneToMany(unum_ledger.Entity, UgoodCheck, parent_child="ugood_check_to", child_parent="to_entity", child_field="to_id")

class MuyBien(Base):
    """
    Have the bots checks in trigger a human check in
    """

    id = int
    entity_id = int   # Entity  accepting
    status = [        # Current status of the relationship
        "requested",
        "active",
        "inactive",
        "rejected",
        "excepted"
    ]
    when = int        # Within a duration of time
    meta = dict       # Any special weird data

    UNIQUE = ["entity_id"]

relations.OneToMany(unum_ledger.Entity, MuyBien)

class Dispute(Base):
    """
    One person has an issue with another
    """

    id = int
    from_id = int     # Entity reaching out
    to_id = int       # Entity accepting
    when = int        # Time of the dispute
    status = [        # Current status of the dispute
        "requested",
        "active",
        "inactive",
        "rejected",
        "excepted"
    ]
    meta = dict       # Any special weird data

    UNIQUE = ["from_id", "to_id", "when"]

relations.OneToMany(unum_ledger.Entity, Dispute, parent_child="dispute_from", child_parent="from_entity", child_field="from_id")
relations.OneToMany(unum_ledger.Entity, Dispute, parent_child="dispute_to", child_parent="to_entity", child_field="to_id")

class Mediation(Base):
    """
    One person will help resolve the dispute
    """

    id = int
    dispute_id = int  # The dispute in question
    entity_id = int   # Entity accepting
    status = [        # Current status of the mediation
        "requested",
        "active",
        "inactive",
        "rejected",
        "excepted"
    ]
    meta = dict       # Any special weird data

    UNIQUE = ["dispute_id", "entity_id"]

relations.OneToMany(Dispute, Mediation)
relations.OneToMany(unum_ledger.Entity, Mediation)
