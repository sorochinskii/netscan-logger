from datetime import datetime
from enum import Enum
from ipaddress import (IPv4Address, IPv4Interface, IPv4Network, ip_network,
                       summarize_address_range)

from fastapi import FastAPI
from pydantic import BaseModel


class Starter(Enum):
    MANUAL = 'manual'
    SCHEDULER = 'scheduler'
    API = 'api'


class Device(BaseModel):
    id: int
    ipv4: bool
    ip: IPv4Address
    mac: str
    vendor: str
    hostname: str
    scan_id: int


class Scan(BaseModel):
    id: int
    task_id: int
    start: datetime
    finish: datetime
    starter: Starter
