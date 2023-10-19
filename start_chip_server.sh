#!/bin/bash
export BEAMLINE_ID=fmx
export CONFIGDIR=/nsls2/software/mx/daq/bnlpx_config
uvicorn server.main:app --host=0.0.0.0 --port=8000 --reload