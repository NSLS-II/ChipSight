from ophyd import Device, EpicsMotor
from ophyd import Component as Cpt

import bluesky.plan_stubs as bsps
from bluesky.run_engine import RunEngine
from bluesky.utils import PersistentDict
import os

class Gonio2(Device):
    x = Cpt(EpicsMotor, ':GX}Mtr')
    y = Cpt(EpicsMotor, ':PY}Mtr')
    z = Cpt(EpicsMotor, ':PZ}Mtr')

    def move_gonio(self, x, y, z):
        yield from bsps.mv([self.x, x, self.y, y, self.z, z])
    
    def get_position(self):
        return self.x.get(), self.y.get(), self.z.get()

class YMotor(Device):
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr', labels=['fmx'])

    def move(self, y):
        yield from bsps.mv([self.y, y])

RE = RunEngine()
print("Initialized RE")
beamline = os.environ["BEAMLINE_ID"]
configdir = os.environ['CONFIGDIR']
RE.md = PersistentDict('%s%s_bluesky_config' % (configdir, beamline))
from databroker import Broker
db = Broker.named(beamline)
print("Initialized databroker")
RE.subscribe(db.insert)
print("Initialized databroker")

from bluesky.log import config_bluesky_logging
config_bluesky_logging()
print("bluesky logging")

if beamline == "fmx":
    gonio2 = Gonio2("XF:17IDC-ES:FMX{Gon:1-Ax", name="gonio2")
    # light = YMotor('XF:17IDC-ES:FMX{Light:1', name='light')
