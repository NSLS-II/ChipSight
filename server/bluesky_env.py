import asyncio
import os
from concurrent.futures import Future, ThreadPoolExecutor
from multiprocessing import Pipe, Process
from pathlib import Path

from bluesky.run_engine import RunEngine, get_bluesky_event_loop
from bluesky.utils import PersistentDict
from databroker import Broker

from server.chip_scanner_plans import BL_calibration, chip_scanner


class RunEngineWorker(Process):
    def __init__(self, conn, config, proposal_config):
        super().__init__()
        print(f"Initializing RE worker {conn}")
        self.conn = conn
        self.config = config
        self.proposal_config = proposal_config

    def initialize_run_engine(self):
        self.RE = RunEngine()
        print("Initialized RE")
        beamline = os.environ["BEAMLINE_ID"]
        configdir = os.environ["CONFIGDIR"]
        self.RE.md = PersistentDict("%s%s_bluesky_config" % (configdir, beamline))

        db = Broker.named(beamline)
        print("Initialized databroker")
        self.RE.subscribe(db.insert)
        print("Initialized databroker")

        from bluesky.log import config_bluesky_logging

        config_bluesky_logging()
        print("bluesky logging")
        chip_scanner.filepath = self.proposal_config["path"]
        p = Path(self.config["fiducial_file"])
        if p.exists():
            chip_scanner.load_fiducials(str(p))

    def run(self):
        self.initialize_run_engine()

        while True:
            message = self.conn.recv()
            if message == "STOP":
                break
            # elif isinstance(message, dict) and message["action"] == "execute_plan":
            else:
                plan = chip_scanner.ppmac_neighbourhood_scan("A1", 20)
                try:
                    print("running plan")
                    self.conn.send(
                        {"status": f"running plan for {message['duration']}"}
                    )
                    self.RE(plan)
                    self.conn.send({"status": "completed"})
                    print("Completed plan")
                except Exception as e:
                    print(f"Failed plan {e}")
                    self.conn.send({"status": "failed", "error": str(e)})


def run_worker(worker):
    asyncio.set_event_loop(get_bluesky_event_loop())
    worker.run()


def run_worker_in_own_thread(worker):
    executor = ThreadPoolExecutor(1, "run-engine-worker")
    return executor.submit(run_worker, worker)


class RunEngineWorkerThread:
    def __init__(self, config, proposal_config):
        self.config = config
        self.proposal_config = proposal_config
        self.initialize_run_engine()

    def initialize_run_engine(self):
        self.RE = RunEngine()
        print("Initialized RE")
        beamline = os.environ["BEAMLINE_ID"]
        configdir = os.environ["CONFIGDIR"]
        self.RE.md = PersistentDict("%s%s_bluesky_config" % (configdir, beamline))

        db = Broker.named(beamline)
        print("Initialized databroker")
        self.RE.subscribe(db.insert)
        print("Initialized databroker")

        from bluesky.log import config_bluesky_logging

        config_bluesky_logging()
        print("bluesky logging")
        chip_scanner.filepath = self.proposal_config["path"]
        p = Path(self.config["fiducial_file"])
        if p.exists():
            chip_scanner.load_fiducials(str(p))

    def run(self):
        self.RE.state_hook = self._update_state

    def _update_state(self, new_state, old_state):
        self._state = new_state

    def start(self):
        run_worker_in_own_thread(self)
