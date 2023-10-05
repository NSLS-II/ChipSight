from ophyd import EpicsMotor
from ophyd import Component as Cpt
from ophyd import Device
from ophyd.signal import EpicsSignalRO, EpicsSignal
from ophyd.status import SubscriptionStatus
import bluesky.plan_stubs as bps
import numpy as np
import time
import re
import epics
import glob
import os

from pathlib import Path

from mxtools.vector_program import VectorProgram
from mxtools.zebra import Zebra
from mxtools.flyer import MXFlyer
from mxtools.eiger import EigerSingleTriggerV26, set_eiger_defaults
from mxtools.handlers import EigerHandlerMX
from server.start_bs import RE, db
import datetime
from server.devices import cam_7, cam_8, shutter_bcu, trans_bcu, trans_ri

db.reg.register_handler(EigerHandlerMX.spec, EigerHandlerMX)

vector = VectorProgram('XF:17IDC-ES:FMX{Gon:1-Vec}', name='vector')
zebra = Zebra('XF:17IDC-ES:FMX{Zeb:3}:', name='zebra')
eiger_single = EigerSingleTriggerV26("XF:17IDC-ES:FMX{Det:Eig16M}",
                                     name="eiger_single")
# TODO: uncomment for V33
# eiger_single.cam.ensure_nonblocking()
set_eiger_defaults(eiger_single)
mx_flyer = MXFlyer(vector=vector, zebra=zebra, detector=eiger_single)


save_dir = '/epics/iocs/notebook/notebooks/chip_fiducials'

def blStrGet():
    return 'FMX'

class DCM(Device):
    b = Cpt(EpicsMotor, '-Ax:B}Mtr', labels=['fmx'])
    g = Cpt(EpicsMotor, '-Ax:G}Mtr', labels=['fmx'])
    p = Cpt(EpicsMotor, '-Ax:P}Mtr', labels=['fmx'])
    r = Cpt(EpicsMotor, '-Ax:R}Mtr', labels=['fmx'])
    e = Cpt(EpicsMotor, '-Ax:E}Mtr', labels=['fmx'])
#    w = Cpt(EpicsMotor, '-Ax:W}Mtr', labels=['fmx'])

## Horizontal Double Crystal Monochromator (FMX)
hdcm = DCM('XF:17IDA-OP:FMX{Mono:DCM', name='hdcm')



def govMsgGet(configStr = 'Robot'):
    """
    Returns Governor message

    configStr: Governor configuration, 'Robot' or 'Human', default: 'Robot'
    
    Examples:
    govMsgGet()
    govMsgGet(configStr = 'Human')
    """
    blStr = blStrGet()
    if blStr == -1: return -1
    
    sysStr = 'XF:17IDC-ES:' + blStr
    devStr = '{Gov:' + configStr + '}'
    stsStr = 'Sts:Msg-Sts'
    pvStr = sysStr + devStr + stsStr
    govMsg = epics.caget(pvStr)
    
    return govMsg

def govStatusGet(stateStr, configStr = 'Robot'):
    """
    Returns the current active status for a Governor state
    
    configStr: Governor configuration, 'Robot', 'Human', 'Chip_Scanner' or 'Hepath'. default: 'Robot'
    stateStr: Governor short version state. Example: 'SA' for sample alignment
              one of ['M','SE','SA','DA','XF','BL','BS','AB','CB','DI','CE','CA','CD']

    Examples
    govStatusGet('SA')
    govStatusGet('SA', configStr = 'Human')
    """
    blStr = blStrGet()
    if blStr == -1: return -1
    
    if stateStr not in ['M','SE','SA','DA','XF','BL','BS','AB','CB','DI','CE','CA','CD']:
        print('stateStr must be one of: M,SE,SA,DA,XF,BL,BS,AB,CB,DI,CE,CA,CD]')
        return -1
    
    sysStr = 'XF:17IDC-ES:' + blStr
    devStr = '{Gov:' + configStr + '-St:' + stateStr + '}'
    stsStr = 'Sts:Active-Sts'
    pvStr = sysStr + devStr + stsStr
    govStatus = epics.caget(pvStr)
    
    return govStatus

def govStateSet(stateStr, configStr = 'Robot'):
    """
    Sets Governor state

    configStr: Governor configuration, 'Robot', 'Human', 'Chip_Scanner' or 'Hepath'. default: 'Robot'
    stateStr: Governor short version state. Example: 'SA' for sample alignment
              one of ['M','SE','SA','DA','XF','BL','BS','AB','CB','DI','CE','CA','CD']

    Examples:
    govStateSet('SA')
    govStateSet('AB', configStr = 'Human')
    """
    blStr = blStrGet()
    if blStr == -1: return -1

    if stateStr not in ['M','SE','SA','DA','XF','BL','BS','AB','CB','DI','CE','CA','CD']:
        print('stateStr must be one of: M,SE,SA,DA,XF,BL,BS,AB,CB,DI,CE,CA,CD]')
        return -1
    
    sysStr = 'XF:17IDC-ES:' + blStr
    devStr = '{Gov:' + configStr + '}'
    cmdStr = 'Cmd:Go-Cmd'
    pvStr = sysStr + devStr + cmdStr
    epics.caput(pvStr, stateStr)
    
    while not govStatusGet(stateStr, configStr = configStr):
        print(govMsgGet(configStr = configStr))
        time.sleep(2)
    print(govMsgGet(configStr = configStr))
    
    return

def configure_zebra_for_chip_scanner():
    zebra.pc.encoder.put(0)
    zebra.pc.arm.trig_source.put(0)
    zebra.pc.gate.sel.put(0)
    zebra.pc.pulse.sel.put(1)
    zebra.pc.pulse.start.put(1)
    zebra.pc.pulse.width.put(4)
    zebra.pc.pulse.step.put(10)
    zebra.pc.pulse.max.put(1)
    epics.caput("XF:17IDC-ES:FMX{Zeb:3}:M1:MRES", 0.01)
    time.sleep(0.5)
    epics.caput("XF:17IDC-ES:FMX{Zeb:3}:M1:SETPOS.PROC", 1)
    
    
class ppmac_input(Device):
    prog = Cpt(EpicsSignal, 'Program')
    dwell = Cpt(EpicsSignal, 'Dwell')
    move_time = Cpt(EpicsSignal, 'Move')
    go = Cpt(EpicsSignal, 'Go')
    input_string = Cpt(EpicsSignal, 'Input')
    
    def send_program(self, program_number, dwell_time, move_time, input_array):
        self.dwell.put(dwell_time)
        self.move_time.put(move_time)
        self.prog.put(program_number)
        i_string = ""
        for row in input_array:
            i_string = i_string + f'x{row[0]}y{row[1]}_'
        self.input_string.put(i_string[:-1])
        setattr(self, f'ready{program_number}', True)
    
    def run_program(self, program_number):
        if hasattr(self, f'ready{program_number}'):
            self.go.put(1)
        else:
            print(f'Must create program {program_number} first!')
    
ppmac_channel = ppmac_input('XF:17ID-CT:FMX{MC17:Sender}', name='ppmac_channel')


class MotorWithEncoder(EpicsMotor):
    encoder_readback = Cpt(EpicsSignalRO, ".RRBV", kind="hinted", auto_monitor=True)

def get_energy():
    """
    Returns the current photon energy in eV derived from the DCM Bragg angle
    """ 
    
    if blStrGet() == 'FMX':
        energy = hdcm.e.user_readback.get()
        return energy
    return -1

class BeamlineCalibrations(Device):
    LoMagCal = Cpt(EpicsSignal, 'LoMagCal}')
    HiMagCal = Cpt(EpicsSignal, 'HiMagCal}')

BL_calibration = BeamlineCalibrations('XF:17ID-ES:FMX{Misc-',
                                      name='BL_calibration',
                                      read_attrs=['LoMagCal', 'HiMagCal'])


class ChipScanner(Device):
    x = Cpt(MotorWithEncoder, 'XF:17IDC-ES:FMX{Chip:1-Ax:CX}Mtr')
    y = Cpt(MotorWithEncoder, 'XF:17IDC-ES:FMX{Chip:1-Ax:CY}Mtr')
    z = Cpt(MotorWithEncoder, 'XF:17IDC-ES:FMX{Gon:2-Ax:Z}Mtr')

    def __init__(self, F0_x, F0_y, F1_x, F1_y, F2_x, F2_y,
                 BLnum_x, BLnum_y, BLgap_x, BLgap_y, 
                 APnum_x, APnum_y, APgap_x, APgap_y,
                 lo_camera, hi_camera, **kwargs):
        super().__init__(**kwargs)
        self.F0: "np.ndarray | None" = None 
        self.F1: "np.ndarray | None" = None
        self.F2: "np.ndarray | None" = None 
        self.F0_x = F0_x
        self.F0_y = F0_y
        self.F1_x = F1_x
        self.F1_y = F1_y
        self.F2_x = F2_x
        self.F2_y = F2_y
        
        self.BLnum_x = BLnum_x
        self.BLnum_y = BLnum_y
        self.BLgap_x = BLgap_x
        self.BLgap_y = BLgap_y
        
        self.APnum_x = APnum_x
        self.APnum_y = APnum_y
        self.APgap_x = APgap_x
        self.APgap_y = APgap_y
        
        self.lo_camera = lo_camera
        self.hi_camera = hi_camera
        
        self.lo_camera_ratios = (BL_calibration.LoMagCal.get(), BL_calibration.LoMagCal.get())
        self.hi_camera_ratios = (BL_calibration.HiMagCal.get(), BL_calibration.HiMagCal.get())
        
        self.filepath = None
                
    def manual_set_fiducial(self, location):
        x_loc = self.x.get().user_readback
        y_loc = self.y.get().user_readback
        z_loc = self.z.get().user_readback
        
        x_loc_enc = self.x.get().encoder_readback
        y_loc_enc = self.y.get().encoder_readback
        z_loc_enc = self.z.get().encoder_readback
        
        setattr(self, location+"_x_motor", x_loc)
        setattr(self, location+"_y_motor", y_loc)
        setattr(self, location+"_z_motor", z_loc)
        
        setattr(self, location+"_x_motor_enc", x_loc_enc)
        setattr(self, location+"_y_motor_enc", y_loc_enc)
        setattr(self, location+"_z_motor_enc", z_loc_enc)
        
        setattr(self, location, np.array([x_loc, y_loc, z_loc]))
        setattr(self, location + "_enc", np.array([x_loc_enc, y_loc_enc, z_loc_enc]))

    def drive_to_position(self, x, y, z=None):
        if not z:
            yield from bps.mv(self.x, x, self.y, y)
        else:
            yield from bps.mv(self.x, x, self.y, y, self.z, z) 
    
    def nudge_by(self, x, y):
        yield from self.drive_to_position(self.x.get().user_readback+x, self.y.get().user_readback+y)
    
    def drive_to_fiducial(self, location_name):
        approx_locations = {'F0': (-self.F1_x/2, -self.F2_y/2), 
                     'F1': (self.F1_x/2, -self.F2_y/2),
                     'F2': (-self.F1_x/2, self.F2_y/2)}
        location: "np.ndarray | None" = getattr(self, location_name)
        if location is None:
            yield from self.drive_to_position(approx_locations[location_name][0], approx_locations[location_name][1])
        else:
            yield from self.drive_to_position(location[0], location[1])
    
    def find_fiducials(self):
        """Routine to find the fiducials of the chip, based on an 
        image from a camera. Relies on the assumptions that the (0,0)
        position is located such that at that location the center of
        the chip is near the center of the camera FOV and that the
        chip is close to level, such that moving half of the given 
        fiducial-to-fiducial distance in each direction leaves the 
        fiducial in the camera image."""
        
        if not (self.check_camera_settings(self.lo_camera) and self.check_camera_settings(self.hi_camera)):
            print("Cancelling fiducial finding")
            return(False)
        
        successes = {'F0': False, 'F1': False, 'F2': False}
        locations = {'F0': (-self.F1_x/2, -self.F2_y/2), 
                     'F1': (self.F1_x/2, -self.F2_y/2),
                     'F2': (-self.F1_x/2, self.F2_y/2)}
        
        for i in range(3):
            location = f'F{i}'
            yield from bps.mv(self.x, locations[location][0], self.y, locations[location][1])
            success = yield from self.find_center(location, center_high = True)
            if success:
                posns = np.array([getattr(self, f'{location}_x_motor'), getattr(self, f'{location}_y_motor'), getattr(self, f'{location}_z_motor')])
                setattr(self, location, posns)
                posns = np.array([getattr(self, f'{location}_x_motor_enc'), getattr(self, f'{location}_y_motor_enc'), getattr(self, f'{location}_z_motor_enc')])
                setattr(self, f'{location}_enc', posns)
                successes[location] = True

        if (successes['F0'] + successes['F1'] + successes['F2'] == 2):
            fail_loc = list(successes.keys())[list(successes.values()).index(False)]
            yield from bps.mv(self.x, locations[fail_loc][0], self.y, locations[fail_loc][1])
            success = yield from self.find_center(fail_loc, center_high = True)
            if success:
                posns = np.array([getattr(self, f'{fail_loc}_x_motor'), getattr(self, f'{fail_loc}_y_motor'), getattr(self, f'{fail_loc}_z_motor')])
                setattr(self, fail_loc, posns)
                posns = np.array([getattr(self, f'{fail_loc}_x_motor_enc'), getattr(self, f'{fail_loc}_y_motor_enc'), getattr(self, f'{fail_loc}_z_motor_enc')])
                setattr(self, f'{fail_loc}_enc', posns)
                successes[fail_loc] = True
            else:
                print(f"Fiducial at {fail_loc} failed to be found twice, set using manual_set_fiducial routine.")
              
        if all(value == True for value in successes.values()):
            data_folder = Path(f"{save_dir}")
            file_to_save = data_folder / f"fiducials_{int(time.time())}.txt"
            self.save_fiducials(file_to_save)
            lx, ly, theta = self.calculate_fit()
            if not (25300 < lx < 25500):
                print(f"Horizontal distance between vectors {lx} appears to be off (expected ~25400), please check.")
            if not (25300 < ly < 25500):
                print(f"Vertical distance between vectors {ly} appears to be off (expected ~25400), please check.")
        else:
            print("At least two fiducial detections failed, check output for details.")
    
    def calculate_fit(self):
        if self.F0 and self.F1 and self.F2:
            ab = self.F1 - self.F0
            ac = self.F2 - self.F0
            print(f"Distance between fiducial F0 and F1: {np.linalg.norm(ab):6.0f}um")
            print(f"Distance between fiducial F0 and F2: {np.linalg.norm(ac):6.0f}um")
            cos_theta = np.dot(ab, ac)/np.linalg.norm(ab)/np.linalg.norm(ac)
            theta = np.arccos(np.clip(cos_theta, -1, 1))
            print(f"Angle between vectors: {theta:6.4f}radians ({theta*180/np.pi:6.3f}deg)")
            return(np.linalg.norm(ab), np.linalg.norm(ac), np.arccos(np.clip(cos_theta, -1, 1)))
    
    def get_fiducials(self):
        return self.F0, self.F1, self.F2, self.F0_enc, self.F1_enc, self.F2_enc
    
    def save_fiducials(self, filepath):
        with open(filepath, 'ab') as f:
            for arr in self.get_fiducials():
                if arr:
                    np.save(f, arr) 
                
    def load_fiducials(self, filepath):
        to_load = ['F0', 'F1', 'F2', 'F0_enc', 'F1_enc', 'F2_enc']
        with open(filepath, 'rb') as f:
            for prop in to_load:
                setattr(self, prop, np.load(f))
                
    def load_last_fiducials(self):
        list_of_files = glob.glob(f'{save_dir}/*')
        latest_file = max(list_of_files, key=os.path.getctime)
        self.load_fiducials(latest_file)
    
    def set_fiducials(self, F0, F1, F2, F0e, F1e, F2e):
        self.F0 = F0
        self.F1 = F1
        self.F2 = F2
        self.F0_enc = F0e
        self.F1_enc = F1e
        self.F2_enc = F2e
        
    def find_center(self, location, center_high = False):
        yield from self.find_camera_center(location, 'lo_camera')
        yield from self.find_camera_center(location, 'hi_camera', center = center_high)
        success, size = yield from autofocus(self.hi_camera, 'stats4_sigma_x', self.z, -100,100,15)
        yield from self.find_camera_center(location, 'hi_camera', center = center_high)
        if success and (size>20):
            setattr(self, location+"_z_motor", self.z.get().user_readback)
            setattr(self, location+"_z_motor_enc", self.z.get().encoder_readback)
        elif not size>20:
            print(f"Detected hole at {location} location appears too small (sigma_x<20), please confirm using manual_set_fiducial routine.")
        else:
            print(f"Failed to find fiducial at {location} location, please find using manual_set_fiducial routine.")
        return (success and (size>20))
    
    def find_camera_center(self, location, camera_st, center = True):
        camera = getattr(self, camera_st)

        x_size = camera.image.dimensions.get()[1]
        y_size = camera.image.dimensions.get()[2]

        if camera == cam_7:
            zoom_roi = camera.roi3
            roi4_focus_size = 100  # Size to cover large fiducial, not the small neighbors
            MagCal = BL_calibration.LoMagCal.get()
        elif camera == cam_8:
            zoom_roi = camera.roi1
            roi4_focus_size = 200  # Size to cover large fiducial, not the small neighbors
            MagCal = BL_calibration.HiMagCal.get()
            
        roi_size = roi4_focus_size
        yield from bps.abs_set(camera.roi4.min_xyz.min_x, 0, wait=True)
        yield from bps.abs_set(camera.roi4.min_xyz.min_y, 0, wait=True)
        yield from bps.abs_set(camera.roi4.size.x, 1692, wait=True)
        yield from bps.abs_set(camera.roi4.size.y, y_size, wait=True)
        yield from bps.sleep(0.2)
        
        max_x = camera.stats4.max_xy.x.get()
        max_y = camera.stats4.max_xy.y.get()
        
        max_val = camera.stats4.max_value.get()
        
        x_ratio, y_ratio = getattr(self, camera_st+'_ratios')
        
        print(max_x, max_y, max_val)
        
        zoom_roi_center_x = zoom_roi.min_xyz.min_x.get() + np.ceil(zoom_roi.size.x.get()/2)
        zoom_roi_center_y = zoom_roi.min_xyz.min_y.get() + np.ceil(zoom_roi.size.y.get()/2)
        
        yield from bps.abs_set(camera.roi4.min_xyz.min_x, max_x-roi_size/2, wait=True)
        yield from bps.abs_set(camera.roi4.min_xyz.min_y, max_y-roi_size/2, wait=True)
        yield from bps.abs_set(camera.roi4.size.x, roi_size, wait=True)
        yield from bps.abs_set(camera.roi4.size.y, roi_size, wait=True)
        yield from bps.sleep(0.2)
        
        center_x = camera.stats4.centroid.x.get()
        center_y = camera.stats4.centroid.y.get()
        
        dx_mot = MagCal * (max_x - roi_size/2 + center_x - zoom_roi_center_x)
        dy_mot = -MagCal * (max_y - roi_size/2 + center_y - zoom_roi_center_y)
        
        yield from bps.mvr(self.x, dx_mot, self.y, dy_mot)
        
        yield from bps.abs_set(camera.roi4.min_xyz.min_x, zoom_roi_center_x-roi_size/2, wait=True)
        yield from bps.abs_set(camera.roi4.min_xyz.min_y, zoom_roi_center_y-roi_size/2, wait=True)
        
        yield from bps.sleep(0.2)
        
        setattr(self, location+"_x_motor", self.x.get().user_readback)
        setattr(self, location+"_y_motor", self.y.get().user_readback)
        
        setattr(self, location+"_x_motor_enc", self.x.get().encoder_readback)
        setattr(self, location+"_y_motor_enc", self.y.get().encoder_readback)
        
        yield from bps.sleep(0.2)
        
    def center_on_point(self):
        yield from bps.sleep(0.2)
        camera = self.hi_camera
        x_size = camera.image.dimensions.get()[1]
        y_size = camera.image.dimensions.get()[2]
        zoom_roi = camera.roi1
        roi4_focus_size = 200  # Size to cover large fiducial, not the small neighbors
        MagCal = BL_calibration.HiMagCal.get()
        roi_size = roi4_focus_size
        zoom_roi_center_x = zoom_roi.min_xyz.min_x.get() + np.ceil(zoom_roi.size.x.get()/2)
        zoom_roi_center_y = zoom_roi.min_xyz.min_y.get() + np.ceil(zoom_roi.size.y.get()/2)
        yield from bps.abs_set(camera.roi4.min_xyz.min_x, zoom_roi_center_x-roi_size/2, wait=True)
        yield from bps.abs_set(camera.roi4.min_xyz.min_y, zoom_roi_center_y-roi_size/2, wait=True)
        yield from bps.sleep(0.2)
        center_x = camera.stats4.centroid.x.get()
        center_y = camera.stats4.centroid.y.get()
        
        dx_mot =  MagCal * (center_x - roi_size/2)
        dy_mot =  -MagCal * (center_y - roi_size/2)
        yield from bps.mvr(self.x, dx_mot, self.y, dy_mot)
        yield from bps.sleep(0.4)
        
        
    def name_to_fiducial_distances(self, location_name):
        """Given a location name of the form @#&& where @ is a capital
        letter from A-H, # is a number from 1-8 and &s are lower case 
        letters from a-t, returns the x and y coordinates of the 
        desired house on the chip, relative to the fiducials F0=(0,0).
        
        Only valid for the Oxford Chip."""
        
        Ny = ord(location_name[0])-65
        Nx = int(location_name[1])-1
        Hy = ord(location_name[2])-97
        Hx = ord(location_name[3])-97
        
        x_loc = (self.F0_x + 
                 Nx*(self.BLgap_x + (self.APnum_x-1)*self.APgap_x) + 
                 Hx*self.APgap_x)
        
        y_loc = (self.F0_y + 
                 Ny*(self.BLgap_y + (self.APnum_y-1)*self.APgap_y) + 
                 Hy*self.APgap_y)
            
        return x_loc, y_loc
    
    def fiducial_distances_to_location(self, x_loc, y_loc):
        """Given distances to the fiducial from the starting point F0=(0,0), 
        returns the x, y and z coordinates of the desired house on the chip.
        
        Only valid for the Oxford Chip."""
        
        relative_x_loc = x_loc/self.F1_x
        relative_y_loc = y_loc/self.F2_y
        
        relative_loc = np.array([relative_x_loc, relative_y_loc])
        
        M = np.array([self.F1-self.F0, self.F2-self.F0]).transpose()
        motor_coords = np.matmul(M, relative_loc) + self.F0
        return(motor_coords)
    
    def fiducial_distances_to_enc_location(self, x_loc, y_loc):
        """Given distances to the fiducial from the starting point F0=(0,0), 
        returns the x, y and z encoder coordinates of the desired house on 
        the chip.
        
        Only valid for the Oxford Chip."""
        
        relative_x_loc = x_loc/self.F1_x
        relative_y_loc = y_loc/self.F2_y
        
        relative_loc = np.array([relative_x_loc, relative_y_loc])
        
        M = np.array([self.F1_enc-self.F0_enc, self.F2_enc-self.F0_enc]).transpose()
        motor_coords = np.matmul(M, relative_loc) + self.F0_enc
        return(motor_coords)
    
    def drive_to_location(self, location_name):
        chip_x, chip_y = self.name_to_fiducial_distances(location_name)
        motor_loc = self.fiducial_distances_to_location(chip_x, chip_y)
        yield from bps.mv(self.x, motor_loc[0], self.y, motor_loc[1], self.z, motor_loc[2])
    
    def configure_detector(self, location, triggers):
        #path = '/nsls2/data/fmx/proposals/commissioning/pass-312064/312064-20230706-fuchs/mx312064-1'
        if not self.filepath:
            print(f'Must set filepath attribute for this chip scanner object before taking data, to determine location where the file will be saved.')
            raise Exception('Filepath not found')
        eiger_single.cam.fw_num_images_per_file.put(triggers)
        eiger_single.cam.file_path.put(self.filepath)
        if not eiger_single.cam.file_path_exists.get():
            print(f'Filepath {self.filepath} does not appear to be a valid directory recognized by the Eiger detector.')
            raise Exception('Filepath not found')
        eiger_single.cam.num_images.put(triggers)
        eiger_single.cam.num_triggers.put(triggers)
        eiger_single.cam.trigger_mode.put(3)
        eiger_single.cam.acquire.put(1)
        my_time = int(time.time())
        eiger_single.cam.fw_name_pattern.put(f'CHIP{location}{my_time}')
        dist = getDetectorDist(configStr = 'Chip_Scanner')
        eiger_single.cam.omega_start.put(0)
        eiger_single.cam.omega_incr.put(0)
        eiger_single.cam.det_distance.put(dist/1000)
    
    def ppmac_linear_scan(self, location_start, location_start_enc, step_vector, step_vector_enc, wait_time, num_steps, start_offset = .01, location_offset_x = 0.0, location_offset_y = 0.0):
        direction = np.sign(step_vector[0])
        zebra.pc.direction.put((1-direction)/2)
        zebra.pc.gate.width.put(abs(step_vector[0]/50.))
        zebra.pc.gate.step.put(abs(step_vector[0]))
        zebra.pc.gate.num_gates.put(num_steps)
        zebra.pc.gate.start.put(location_start[0] - step_vector[0]*start_offset)
        l1 = location_start - step_vector
        
        lse = location_start_enc - step_vector_enc*location_offset_x + np.array([0,1,0])*location_offset_y*10000
        input_array = [[lse[0] + i*step_vector_enc[0], lse[1] + i*step_vector_enc[1]] for i in range(num_steps+1)]
        # input_array = [[location_start_enc[0] + i*step_vector_enc[0], location_start_enc[1] + i*step_vector_enc[1]] for i in range(num_steps+1)]        
        ppmac_channel.send_program(23, wait_time, 20, input_array)

        yield from bps.mv(self.x, l1[0], self.y, l1[1], self.z, l1[2])
        def check_armed(*, old_value, value, **kwargs):
            return(old_value == 0 and value == 1)
        status = SubscriptionStatus(zebra.pc.arm.output, check_armed)
        zebra.pc.arm_signal.put(1)
        try:
            status.wait(10)
        except TimeoutError as e:
            print("Failed to arm zebra within 10s, aborting.")
            return()
        
        def check_done(*, old_value, value, **kwargs):
            return(old_value == 1 and value == 0)
        shutter_bcu.open.put(1)
        yield from bps.sleep(0.08)
        ppmac_channel.run_program(23)
        status = SubscriptionStatus(zebra.pc.arm.output, check_done)
        return status

    def ppmac_single_line_scan(self, line, wait_time, zebra_offset = 0.01, location_offset_x = 0.0, location_offset_y = 0.0, refocus = False):
        pattern = re.compile("^([A-H][1-8][a-t])$")
        if not pattern.match(line):
            print(f"Line scan requires input of form ex. A1a, got {line}.")
            return(False)
        self.configure_detector(line, 20)
        if zebra.pc.gate.sel.get():
            print("Zebra appears to be configured for gonio1, run configure_zebra_for_chip_scanner() and retry.")
            return(False)
        a0 = self.name_to_fiducial_distances('A1aa')
        ax = self.name_to_fiducial_distances('A1ab')
        ay = self.name_to_fiducial_distances('A1ba')
        x_step = self.fiducial_distances_to_location(*ax) - self.fiducial_distances_to_location(*a0)
        y_step = self.fiducial_distances_to_location(*ay) - self.fiducial_distances_to_location(*a0)
        x_step_enc = self.fiducial_distances_to_enc_location(*ax) - self.fiducial_distances_to_enc_location(*a0)
        y_step_enc = self.fiducial_distances_to_enc_location(*ay) - self.fiducial_distances_to_enc_location(*a0)
        yield from self.drive_to_location(f'{line}a')
        yield from self.center_on_point()
        if refocus:
            yield from autofocus(self.hi_camera, 'stats4_sigma_x', self.z, -10,10,15)
        loc = np.array([self.x.get().user_readback, self.y.get().user_readback, self.z.get().user_readback])
        enc_loc = np.array([self.x.get().encoder_readback, self.y.get().encoder_readback, self.z.get().encoder_readback])
        govStateSet('CD', configStr = 'Chip_Scanner')
        status = yield from self.ppmac_linear_scan(loc, enc_loc, x_step, x_step_enc, wait_time, 20, start_offset = zebra_offset + location_offset_x, location_offset_x = location_offset_x, location_offset_y = location_offset_y)
        between_time = wait_time * 20 + 400
        status.wait(between_time/1000. + 20)
        shutter_bcu.close.put(1)
        eiger_single.cam.acquire.put(0)
        govStateSet('CA', configStr = 'Chip_Scanner')
        transmission = trans_bcu.transmission.get()*trans_ri.transmission.get()
        print(f"Transmission = {transmission}")
        print(f"Time = {datetime.datetime.now()}")
        print(f"Type = Line Scan")
        print(f"Location = {line}")
        print(f"Energy = {get_energy()}")
        print(f"Detector distance = {getDetectorDist(configStr = 'Chip_Scanner')}")
        print(f"Data location = {eiger_single.cam.file_path.get()}{eiger_single.cam.fw_name_pattern.get()}")
        
    def ppmac_neighbourhood_scan(self, neighbourhood, wait_time, zebra_offset = 0.01, location_offset_x = 0.0, location_offset_y = 0.0, refocus = False):
        pattern = re.compile("^([A-H][1-8])$")
        if not pattern.match(neighbourhood):
            print(f"Neighbourhood scan requires input of form ex. A1, got {neighbourhood}.")
            return(False)
        if zebra.pc.gate.sel.get():
            print("Zebra appears to be configured for gonio1, run configure_zebra_for_chip_scanner() and retry.")
            return(False)
        self.configure_detector(neighbourhood, 400)
        a0 = self.name_to_fiducial_distances('A1aa')
        ax = self.name_to_fiducial_distances('A1ab')
        ay = self.name_to_fiducial_distances('A1ba')
        x_step = self.fiducial_distances_to_location(*ax) - self.fiducial_distances_to_location(*a0)
        y_step = self.fiducial_distances_to_location(*ay) - self.fiducial_distances_to_location(*a0)
        x_step_enc = self.fiducial_distances_to_enc_location(*ax) - self.fiducial_distances_to_enc_location(*a0)
        y_step_enc = self.fiducial_distances_to_enc_location(*ay) - self.fiducial_distances_to_enc_location(*a0)
        yield from self.drive_to_location(f'{neighbourhood}aa')
        yield from self.center_on_point()
        if refocus:
            yield from autofocus(self.hi_camera, 'stats4_sigma_x', self.z, -10,10,15)
        loc = np.array([self.x.get().user_readback, self.y.get().user_readback, self.z.get().user_readback])
        enc_loc = np.array([self.x.get().encoder_readback, self.y.get().encoder_readback, self.z.get().encoder_readback])
        between_time = wait_time * 20 + 400
        govStateSet('CD', configStr = 'Chip_Scanner')
        for i in range(10):
            # Snake scan, initial going right
            start_loc = loc + 2*i*y_step
            start_enc_loc = enc_loc + 2*i*y_step_enc
            status = yield from self.ppmac_linear_scan(start_loc, start_enc_loc, x_step, x_step_enc, wait_time, 20, start_offset = zebra_offset + location_offset_x, location_offset_x = location_offset_x, location_offset_y = location_offset_y) # 20 to push the chip off the sample at the end
            status.wait(between_time/1000. + 20)
            shutter_bcu.close.put(1)
            
            # Going back left
            start_loc = start_loc + y_step + 19*x_step
            start_enc_loc = start_enc_loc + y_step_enc + 19*x_step_enc
            status = yield from self.ppmac_linear_scan(start_loc, start_enc_loc, -x_step, -x_step_enc, wait_time, 20, start_offset = zebra_offset + location_offset_x, location_offset_x = location_offset_x, location_offset_y = location_offset_y)
            status.wait(between_time/1000. + 20)
            shutter_bcu.close.put(1)

        eiger_single.cam.acquire.put(0)
        govStateSet('CA', configStr = 'Chip_Scanner')
        transmission = trans_bcu.transmission.get()*trans_ri.transmission.get()
        print(f"Transmission = {transmission}")
        print(f"Time = {datetime.datetime.now()}")
        print(f"Type = Neighbourhood Scan")
        print(f"Location = {neighbourhood}")
        print(f"Energy = {get_energy()}")
        print(f"Detector distance = {getDetectorDist(configStr = 'Chip_Scanner')}")
        print(f"Data location = {eiger_single.cam.file_path.get()}{eiger_single.cam.fw_name_pattern.get()}")    

    def linear_scan_with_triggering(self, location_start, location_end, wait_time):
        Ny = ord(location_start[0])-65
        Nx = int(location_start[1])-1
        if Ny != ord(location_end[0])-65 or Nx != int(location_end[1])-1:
            print("linear_scan is not yet configured to work with houses in different neighbourhoods")
            return()
        Hsy = ord(location_start[2])-97
        Hsx = ord(location_start[3])-97
        Hey = ord(location_end[2])-97
        Hex = ord(location_end[3])-97
        if Hsy != Hey:
            print("linear_scan_with_triggering can currently only scan over one row")
            return()
        num_steps = abs(Hex - Hsx)
        direction = np.sign(Hex - Hsx)
        chip_s_x, chip_s_y = self.name_to_fiducial_distances(location_start)
        chip_e_x, chip_e_y = self.name_to_fiducial_distances(location_end)
        motor_s = self.fiducial_distances_to_location(chip_s_x, chip_s_y)
        motor_e = self.fiducial_distances_to_location(chip_e_x, chip_e_y)
        motor_d = (motor_e - motor_s)/num_steps
        zebra.pc.disarm.put(1)
        zebra.pc.direction.put((1-direction)/2)
        zebra.pc.gate.width.put(motor_d[0]/2)
        zebra.pc.gate.step.put(motor_d[0])
        zebra.pc.gate.num_gates.put(num_steps + 1)
        yield from bps.mv(self.x, motor_s[0], self.y, motor_s[1], self.z, motor_s[2])
        yield from self.center_on_point()
        zebra.pc.gate.start.put(self.x.user_readback.get()-1)
        yield from bps.mvr(self.x, -direction*5) # Move away so that the first trigger hits on the first point
        def check_armed(*, old_value, value, **kwargs):
            return(old_value == 0 and value == 1)
        status = SubscriptionStatus(zebra.pc.arm.output, check_armed)
        zebra.pc.arm_signal.put(1)
        try:
            status.wait(10)
        except TimeoutError as e:
            print("Failed to arm zebra within 10s, aborting.")
            return()
        yield from bps.mvr(self.x, direction*5)
        for _ in range(num_steps):
            yield from bps.sleep(wait_time)
            yield from bps.mvr(self.x, motor_d[0], self.y, motor_d[1], self.z, motor_d[2])
        
    def configure_zebra(self):
        zebra.pc.encoder.put(0)
        zebra.pc.arm.trig_source.put(0)
        zebra.pc.gate.sel.put(0)
        zebra.pc.pulse.sel.put(1)
        zebra.pc.pulse.start.put(1)
        zebra.pc.pulse.width.put(4)
        zebra.pc.pulse.step.put(10)
        zebra.pc.pulse.max.put(1)
    
    def linear_scan(self, location_start, location_end, wait_time):
        Ny = ord(location_start[0])-65
        Nx = int(location_start[1])-1
        if Ny != ord(location_end[0])-65 or Nx != int(location_end[1])-1:
            print("linear_scan is not yet configured to work with houses in different neighbourhoods")
            return()
        Hsy = ord(location_start[2])-97
        Hsx = ord(location_start[3])-97
        Hey = ord(location_end[2])-97
        Hex = ord(location_end[3])-97
        if Hsy != Hey and Hsx != Hex:
            print("linear_scan can currently only scan over one row or column")
            return()
        if Hsy == Hey:
            num_steps = Hex - Hsx
        else:
            num_steps = Hey - Hsy
        chip_s_x, chip_s_y = self.name_to_fiducial_distances(location_start)
        chip_e_x, chip_e_y = self.name_to_fiducial_distances(location_end)
        motor_s = self.fiducial_distances_to_location(chip_s_x, chip_s_y)
        motor_e = self.fiducial_distances_to_location(chip_e_x, chip_e_y)
        motor_d = (motor_e - motor_s)/num_steps
        yield from bps.mv(self.x, motor_s[0], self.y, motor_s[1], self.z, motor_s[2])
        yield from self.center_on_point()
        for _ in range(num_steps):
            yield from bps.mvr(self.x, motor_d[0], self.y, motor_d[1], self.z, motor_d[2])
            yield from bps.sleep(wait_time)
            
    def check_camera_settings(self, camera):
        if camera.cam.acquire_time.get() > 0.1:
            print(f'{camera} acquireTime > 0.1, which could affect processing. Please reduce this to continue.')
            return(False)
        if camera.cam.image_mode.get() != 2:
            print(f'{camera} not in continuous acquisition mode, please set this and retry.')
            return(False)
        if camera.cam.detector_state.get() != 1:
            print(f'{camera} not acquiring, please start and retry.')
            return(False)
        return(True)
        

class OxfordChip(ChipScanner):
    def __init__(self, **kwargs):
        super().__init__(400, 400, 25400, 0, 0, 25400,
                         8, 8, 800, 800,
                         20, 20, 125, 125,
                         cam_7, cam_8, **kwargs)

chip_scanner = OxfordChip(name='chip_scanner')


def autofocus(camera, stats, motor, start, end, steps, move2Focus=True, max_repeats = 2):
    """
    Chip scanner autofocus
    
    Scan axis, e.g. chipsc.z vs ROI stats sigma_x, and drive to position that minimizes sigma_x
    
    The scan is relative to the current position
    
    Examples:
    RE(autofocus(cam_8, 'stats4_sigma_x', chipsc.z, -40,40,15))
    RE(autofocus(cam_7, 'stats4_sigma_x', chipsc.z, -60,60,15, move2Focus=False))
    """
    # Best-Effort Callback table will interfere with LiveTable
    # Check if set, if yes store current setting, disable for scan, reset at end
    try:
        bec
    except NameError:
        bec_exists = False
    else:
        bec_exists = True
        bec_table_enabled = bec._table_enabled
        bec.disable_table()
    
    fig, ax1 = plt.subplots()
    ax1.grid(True)

    stats_name = "_".join((camera.name,stats))
    @bpp.subs_decorator(LivePlot(stats_name, motor.name, ax=ax1))
    @bpp.subs_decorator(LiveTable([motor.name, stats_name], default_prec=5))
    def inner(camera, motor, start, end, steps):
        uid = yield from bp.relative_scan([camera], motor, start, end, steps)
        return uid
    
    # Find minimum
    uid = yield from inner(camera, motor, start, end, steps)
    data = np.array(db[uid].table()[[stats_name, motor.name]])
    min_idx = np.argmin(data[:, 0])
    min_x = data[min_idx, 1]
    min_y = data[min_idx, 0]


    ax1.plot([min_x], [min_y], 'or')

    if move2Focus:
        yield from bps.mv(motor, min_x)

    if min_y < 1:
        print("Failed to find signal in ROI, aborting")
        return False, 0
    
    if 0 < min_idx < steps-1:
        success = True
    else:
        success = False
        if max_repeats > 0 and move2Focus:
            step_size = abs(end-start)/steps
            if min_idx == 0:
                new_start, new_end = -abs(end-start), step_size
            else:
                new_start, new_end = -step_size, abs(end-start)
            success = yield from autofocus(camera, stats, motor, new_start, new_end, steps, move2Focus=move2Focus, max_repeats = max_repeats - 1)
    
    # Reset Best-Effort Callback table settings to previous settings
    if bec_exists and bec_table_enabled:
        bec.enable_table()
    return success, min_y

def getDetectorDist(configStr = 'Robot'):
    """
    Returns Governor message

    configStr: Governor configuration, 'Robot' or 'Human', default: 'Robot'
    
    Examples:
    govMsgGet()
    govMsgGet(configStr = 'Human')
    """
    blStr = blStrGet()
    if blStr == -1: return -1
    
    sysStr = 'XF:17IDC-ES:' + blStr
    devStr = '{Gov:' + configStr
    stsStr = '-Dev:dz}Pos:In-Pos'
    pvStr = sysStr + devStr + stsStr
    govMsg = epics.caget(pvStr)
    
    return govMsg

def multiple_chip_neighbourhoods(neighbourhood_list, wait_time = 20):
    for neighbourhood in neighbourhood_list:
        RE(chip_scanner.ppmac_neighbourhood_scan(neighbourhood, wait_time))
        
def chip_line_of_blocks(line, wait_time = 20):
    neighbourhoods = []
    for i in range(1,9):
        neighbourhoods.append(f'{line}{i}')
    multiple_chip_neighbourhoods(neighbourhoods, wait_time = wait_time)

    
letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
def chip_all_blocks(wait_time = 20):
    neighbourhoods = []
    for i in range(1,9):
        for letter in letters:
            neighbourhoods.append(f'{letter}{i}')
    multiple_chip_neighbourhoods(neighbourhoods, wait_time = wait_time)
