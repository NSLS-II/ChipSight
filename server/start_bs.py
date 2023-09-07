from ophyd import Device, EpicsMotor
from ophyd import Component as Cpt

import bluesky.plans as bp
import bluesky.plan_stubs as bsps
from bluesky.run_engine import RunEngine
from bluesky.utils import PersistentDict
import os

class Gonio2(Device):
    x = Cpt(EpicsMotor, ':GX}Mtr')
    y = Cpt(EpicsMotor, ':PY}Mtr')
    z = Cpt(EpicsMotor, ':PZ}Mtr')

    def move_gonio(self, x, y, z):
        yield from bsps.mv([self.x, x, self.y, y, self.z])

RE = RunEngine()
beamline = os.environ["BEAMLINE_ID"]
configdir = os.environ['CONFIGDIR']
RE.md = PersistentDict('%s%s_bluesky_config' % (configdir, beamline))
from databroker import Broker
db = Broker.named(beamline)

RE.subscribe(db.insert)

from bluesky.log import config_bluesky_logging
config_bluesky_logging()

if beamline == "fmx":
    gonio2 = Gonio2("XF:17IDC-ES:FMX{Gon:1-Ax", name="gonio2")
