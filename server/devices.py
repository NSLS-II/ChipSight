from ophyd import PVPositioner, PVPositionerPC, Device, Component as Cpt, EpicsMotor, EpicsSignal, EpicsSignalRO
from ophyd import (SingleTrigger, ProsilicaDetector,
                   ImagePlugin, TIFFPlugin, StatsPlugin, ROIPlugin, DetectorBase, HDF5Plugin,
                   TransformPlugin, ProcessPlugin, AreaDetector)

from ophyd import Component as Cpt


class Transmission(Device):
    energy = Cpt(EpicsSignal, 'Energy-SP') # PV only used for debugging. Attenuator uses Bragg axis energy
    transmission = Cpt(EpicsSignal, 'Trans-SP')
    set_trans = Cpt(EpicsSignal, 'Cmd:Set-Cmd.PROC')

## Dummy Attenuator - for read/write_lut() and XF:17ID-ES:FMX{Misc-LUT:atten}X-Wfm/Y-Wfm
class AttenuatorLUT(Device):
    done = Cpt(EpicsSignalRO, '}attenDone')

class AttenuatorBCU(Device):
    a1 = Cpt(EpicsMotor, '-Ax:1}Mtr', labels=['fmx'])
    a2 = Cpt(EpicsMotor, '-Ax:2}Mtr', labels=['fmx'])
    a3 = Cpt(EpicsMotor, '-Ax:3}Mtr', labels=['fmx'])
    a4 = Cpt(EpicsMotor, '-Ax:4}Mtr', labels=['fmx'])
    done = Cpt(EpicsSignalRO, '}attenDone')



class YMotor(Device):
	y = Cpt(EpicsMotor, '-Ax:Y}Mtr', labels=['fmx'])

class XYMotor(Device):
	x = Cpt(EpicsMotor, '-Ax:X}Mtr', labels=['fmx'])
	y = Cpt(EpicsMotor, '-Ax:Y}Mtr', labels=['fmx'])

class XYZMotor(XYMotor):
	z = Cpt(EpicsMotor, '-Ax:Z}Mtr', labels=['fmx'])

class XZXYMotor(Device):
	x = Cpt(EpicsMotor, '-Ax:X}Mtr', labels=['fmx'])
	z = Cpt(EpicsMotor, '-Ax:Z}Mtr', labels=['fmx'])

class XYZfMotor(Device):
	x = Cpt(EpicsMotor, '-Ax:Xf}Mtr')
	y = Cpt(EpicsMotor, '-Ax:Yf}Mtr')
	z = Cpt(EpicsMotor, '-Ax:Zf}Mtr')

class Slits(Device):
	b = Cpt(EpicsMotor, '-Ax:B}Mtr', labels=['fmx'])
	i = Cpt(EpicsMotor, '-Ax:I}Mtr', labels=['fmx'])
	o = Cpt(EpicsMotor, '-Ax:O}Mtr', labels=['fmx'])
	t = Cpt(EpicsMotor, '-Ax:T}Mtr', labels=['fmx'])
	x_ctr = Cpt(EpicsMotor, '-Ax:XCtr}Mtr', labels=['fmx'])
	x_gap = Cpt(EpicsMotor, '-Ax:XGap}Mtr', labels=['fmx'])
	y_ctr = Cpt(EpicsMotor, '-Ax:YCtr}Mtr', labels=['fmx'])
	y_gap = Cpt(EpicsMotor, '-Ax:YGap}Mtr', labels=['fmx'])

class VirtualCenter(PVPositioner):
	setpoint = Cpt(EpicsSignal, 'center')
	readback = Cpt(EpicsSignalRO, 't2.D')
	done = Cpt(EpicsSignalRO, 'DMOV')
	done_value = 1

class VirtualGap(PVPositioner):
	setpoint = Cpt(EpicsSignal, 'size')
	readback = Cpt(EpicsSignalRO, 't2.C')
	done = Cpt(EpicsSignalRO, 'DMOV')
	done_value = 1

class HorizontalDCM(Device):
	b = Cpt(EpicsMotor, '-Ax:B}Mtr', labels=['fmx'])
	g = Cpt(EpicsMotor, '-Ax:G}Mtr', labels=['fmx'])
	p = Cpt(EpicsMotor, '-Ax:P}Mtr', labels=['fmx'])
	r = Cpt(EpicsMotor, '-Ax:R}Mtr', labels=['fmx'])
	e = Cpt(EpicsMotor, '-Ax:E}Mtr', labels=['fmx'])
#	w = Cpt(EpicsMotor, '-Ax:W}Mtr', labels=['fmx'])

class VerticalDCM(Device):
    b = Cpt(EpicsMotor, '-Ax:B}Mtr')
    g = Cpt(EpicsMotor, '-Ax:G}Mtr')
    p = Cpt(EpicsMotor, '-Ax:P}Mtr')
    r = Cpt(EpicsMotor, '-Ax:R}Mtr')
    e = Cpt(EpicsMotor, '-Ax:E}Mtr')
    w = Cpt(EpicsMotor, '-Ax:W}Mtr')

class Cover(Device):
    close = Cpt(EpicsSignal, 'Cmd:Cls-Cmd')
    open = Cpt(EpicsSignal, 'Cmd:Opn-Cmd')
    status = Cpt(EpicsSignalRO, 'Pos-Sts') # status: 0 (Not Open), 1 (Open)

class Shutter(Device):
    close = Cpt(EpicsSignal, 'Cmd:Cls-Cmd.PROC')
    open = Cpt(EpicsSignal, 'Cmd:Opn-Cmd.PROC')
    status = Cpt(EpicsSignalRO, 'Pos-Sts') # status: 0 (Open), 1 (Closed), 2 (Undefined)
    
class ShutterTranslation(Device):
	x = Cpt(EpicsMotor, '-Ax:X}Mtr')

class GoniometerStack(Device):
	gx = Cpt(EpicsMotor, '-Ax:GX}Mtr', labels=['fmx'])
	gy = Cpt(EpicsMotor, '-Ax:GY}Mtr', labels=['fmx'])
	gz = Cpt(EpicsMotor, '-Ax:GZ}Mtr', labels=['fmx'])
	o  = Cpt(EpicsMotor, '-Ax:O}Mtr', labels=['fmx'])
	py = Cpt(EpicsMotor, '-Ax:PY}Mtr', labels=['fmx'])
	pz = Cpt(EpicsMotor, '-Ax:PZ}Mtr', labels=['fmx'])

class BeamStop(Device):
	fx = Cpt(EpicsMotor, '-Ax:FX}Mtr', labels=['fmx'])
	fy = Cpt(EpicsMotor, '-Ax:FY}Mtr', labels=['fmx'])
    
class Annealer(Device):
    air = Cpt(EpicsSignal, '1}AnnealerAir-Sel')
    inStatus = Cpt(EpicsSignalRO, '2}AnnealerIn-Sts') # status: 0 (Not In), 1 (In)
    outStatus = Cpt(EpicsSignalRO, '2}AnnealerOut-Sts') # status: 0 (Not In), 1 (In)

class StandardProsilica(SingleTrigger, ProsilicaDetector):
    image = Cpt(ImagePlugin, 'image1:')
    roi1 = Cpt(ROIPlugin, 'ROI1:')
    roi2 = Cpt(ROIPlugin, 'ROI2:')
    roi3 = Cpt(ROIPlugin, 'ROI3:')
    roi4 = Cpt(ROIPlugin, 'ROI4:')
    trans1 = Cpt(TransformPlugin, 'Trans1:')
    proc1 = Cpt(ProcessPlugin, 'Proc1:')
    stats1 = Cpt(StatsPlugin, 'Stats1:')
    stats2 = Cpt(StatsPlugin, 'Stats2:')
    stats3 = Cpt(StatsPlugin, 'Stats3:')
    stats4 = Cpt(StatsPlugin, 'Stats4:')
    stats5 = Cpt(StatsPlugin, 'Stats5:')
    tiff = Cpt(TIFFPlugin, 'TIFF1:')
    

#######################################################
### FMX
#######################################################


## BCU Transmission
trans_bcu = Transmission('XF:17IDC-OP:FMX{Attn:BCU}', name='trans_bcu',
                         read_attrs=['transmission'])
## RI Transmission
trans_ri = Transmission('XF:17IDC-OP:FMX{Attn:RI}', name='trans_ri',
                        read_attrs=['transmission'])

## Dummy Attenuator - for read/write_lut() and XF:17ID-ES:FMX{Misc-LUT:atten}X-Wfm/Y-Wfm
atten = AttenuatorLUT('XF:17IDC-OP:FMX{Attn:BCU', name='atten',
                          read_attrs=['done'])

## BCU Attenuator
atten_bcu = AttenuatorBCU('XF:17IDC-OP:FMX{Attn:BCU', name='atten_bcu',
                          read_attrs=['done', 'a1', 'a2', 'a3', 'a4'],
                          labels=['fmx'])


## Horizontal Double Crystal Monochromator (FMX)
hdcm = HorizontalDCM('XF:17IDA-OP:FMX{Mono:DCM', name='hdcm')

# Vertical Double Crystal Monochromator (AMX)
vdcm = VerticalDCM('XF:17IDA-OP:AMX{Mono:DCM', name='vdcm')

# KB mirror pitch tweak voltages
vkb_piezo_tweak = EpicsSignal('XF:17IDC-BI:FMX{Best:2}:PreDAC0:OutCh1')
hkb_piezo_tweak = EpicsSignal('XF:17IDC-BI:FMX{Best:2}:PreDAC0:OutCh2')

## 17-ID-A FOE shutter
shutter_foe = Shutter('XF:17ID-PPS:FAMX{Sh:FE}', name='shutter_foe',
                 read_attrs=['status'])

## 17-ID-C experimental hutch shutter
shutter_hutch_c = Shutter('XF:17IDA-PPS:FMX{PSh}', name='shutter_hutch_c',
                 read_attrs=['status'])

## FMX BCU shutter
shutter_bcu = Shutter('XF:17IDC-ES:FMX{Gon:1-Sht}', name='shutter_bcu',
                 read_attrs=['status'])

## Beam Conditioning Unit Shutter Translation
sht = ShutterTranslation('XF:17IDC-ES:FMX{Sht:1', name='sht')

## Eiger16M detector cover
cover_detector = Cover('XF:17IDC-ES:FMX{Det:FMX-Cover}', name='cover_detector',
                 read_attrs=['status'])

## Slits Motions
slits1 = Slits('XF:17IDA-OP:FMX{Slt:1', name='slits1', labels=['fmx'])
slits2 = Slits('XF:17IDC-OP:FMX{Slt:2', name='slits2', labels=['fmx'])
slits3 = Slits('XF:17IDC-OP:FMX{Slt:3', name='slits3', labels=['fmx'])
slits4 = Slits('XF:17IDC-OP:FMX{Slt:4', name='slits4', labels=['fmx'])
slits5 = Slits('XF:17IDC-OP:FMX{Slt:5', name='slits5', labels=['fmx'])

## BPM Motions
mbpm1 = XYMotor('XF:17IDA-BI:FMX{BPM:1', name='mbpm1')
mbpm2 = XYMotor('XF:17IDC-BI:FMX{BPM:2', name='mbpm2')
mbpm3 = XYMotor('XF:17IDC-BI:FMX{BPM:3', name='mbpm3')

## Collimator
colli = XZXYMotor('XF:17IDC-ES:FMX{Colli:1', name='colli')

## Microscope
mic = XYMotor('XF:17IDC-ES:FMX{Mic:1', name='mic')
light = YMotor('XF:17IDC-ES:FMX{Light:1', name='light')

## Holey Mirror
hm = XYZMotor('XF:17IDC-ES:FMX{Mir:1', name='hm')

## Goniometer Stack
gonio = GoniometerStack('XF:17IDC-ES:FMX{Gon:1', name='gonio')

## PI Scanner Fine Stages
pif = XYZfMotor('XF:17IDC-ES:FMX{Gon:1', name='pif')

## Beam Stop
bs = BeamStop('XF:17IDC-ES:FMX{BS:1', name='bs')

## FMX annealer aka cryo blocker
annealer = Annealer('XF:17IDC-ES:FMX{Wago:', name='annealer',
                        read_attrs=[],
                        labels=['fmx'])

keithley = EpicsSignalRO('XF:17IDC-BI:FMX{Keith:1}readFloat', name='keithley')

cam_fs1 = StandardProsilica('XF:17IDA-BI:FMX{FS:1-Cam:1}', name='cam_fs1')
#cam_mono = StandardProsilica('XF:17IDA-BI:FMX{Mono:DCM-Cam:1}', name='cam_mono')
cam_fs2 = StandardProsilica('XF:17IDA-BI:FMX{FS:2-Cam:1}', name='cam_fs2')
cam_fs3 = StandardProsilica('XF:17IDA-BI:FMX{FS:3-Cam:1}', name='cam_fs3')
cam_fs4 = StandardProsilica('XF:17IDC-BI:FMX{FS:4-Cam:1}', name='cam_fs4')
cam_fs5 = StandardProsilica('XF:17IDC-BI:FMX{FS:5-Cam:1}', name='cam_fs5')
cam_7 = StandardProsilica('XF:17IDC-ES:FMX{Cam:7}', name='cam_7')
cam_8 = StandardProsilica('XF:17IDC-ES:FMX{Cam:8}', name='cam_8')

#all_standard_pros = [cam_fs1, cam_mono, cam_fs2, cam_fs3, cam_fs4, cam_fs5, cam_7, cam_8]
all_standard_pros = [cam_fs1, cam_fs2, cam_fs3, cam_fs4, cam_fs5, cam_7, cam_8]

for camera in all_standard_pros:
    camera.read_attrs = ['stats1', 'stats2', 'stats3', 'stats4', 'stats5']
    camera.stats1.read_attrs = ['total', 'centroid']
    camera.stats2.read_attrs = ['total', 'centroid']
    camera.stats3.read_attrs = ['total', 'centroid']
    camera.stats4.read_attrs = ['total', 'centroid', 'sigma_x', 'sigma_y']
    camera.stats5.read_attrs = ['total', 'centroid']
    camera.stats4.centroid.read_attrs = ['x', 'y']
    camera.tiff.read_attrs = []

cam_fs2.stats1.total.kind = 'hinted'

