import datetime

import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy_utils as su

metadata = sa.MetaData()
Base = orm.declarative_base()


class Device(Base):
    __tablename__ = "device"

    id = sa.Column(sa.Integer, primary_key=True)
    ipv4 = sa.Column(sa.Boolean, default=True)
    ip = sa.Column(su.IPAddressType)
    mac = sa.Column(sa.String)
    vendor = sa.Column(sa.String)
    hostname = sa.Column(sa.String)
    scan_id = sa.Column("Scan", sa.ForeignKey("scan.id"))


class Scan(Base):
    STARTER = [
        ('manual', 'Manual'),
        ('scheduler', 'Scheduler'),
        ('api', 'API')
    ]

    __tablename__ = "scan"

    id = sa.Column(sa.Integer, primary_key=True)
    start = sa.Column(sa.DateTime)
    finish = sa.Column(sa.DateTime)
    starter = sa.Column(su.ChoiceType(STARTER))
