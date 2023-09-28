from ophyd import Device, EpicsMotor
from ophyd import Component as Cpt

import bluesky.plan_stubs as bsps
from bluesky.run_engine import RunEngine
from bluesky.utils import PersistentDict
import os

from databroker import Broker

RE = RunEngine()
print("Initialized RE")
beamline = os.environ["BEAMLINE_ID"]
configdir = os.environ["CONFIGDIR"]
RE.md = PersistentDict("%s%s_bluesky_config" % (configdir, beamline))

db = Broker.named(beamline)
print("Initialized databroker")
RE.subscribe(db.insert)
print("Initialized databroker")

from bluesky.log import config_bluesky_logging

config_bluesky_logging()
print("bluesky logging")

if beamline == "fmx":
    # gonio2 = Gonio2("XF:17IDC-ES:FMX{Gon:1-Ax", name="gonio2")
    # light = YMotor('XF:17IDC-ES:FMX{Light:1', name='light')
