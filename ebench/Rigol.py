#!/usr/bin/env python3

import os
from absl import app, flags, logging
from absl.flags import FLAGS

import pyvisa
from time import sleep

import ebench

# Installing this module as command
from .CMDS import CMD_RIGOL
CMD=CMD_RIGOL

from .ebench import Instrument, Cmd, subMenuHelp, mainMenuHelpCommon, usage, menuStartRecording, menuStopRecording, menuScreenShot, version


flags.DEFINE_string('ip', "skooppi", "IP address of pyvisa instrument")
flags.DEFINE_string('addr', None, "pyvisa instrument address")
flags.DEFINE_string('captureDir', "pics", "Capture directory")
flags.DEFINE_string('recordingDir', "tmp", "Directory where recordings are saved into")


class Osciloscope(Instrument):
    """Pyvisa instrument managing pyvisa resource and communicating using
    write and query operations
    """

    def __init__( self, addr, debug = False ):
        super().__init__( debug=debug)
        self.addr = addr
        try:
            self.instrument = Instrument.singleton_rm().open_resource(self.addr)
            
        except pyvisa.errors.VisaIOError as err:
            self.instrument = None
            logging.error(err)
            
    def close(self):
        try:
            logging.info(  "Closing instrument {}".format(self.instrument))
            if self.instrument is not None:
                self.instrument.close()
        except:
            logging.error(  "Closing instrument {} - failed".format(self.instrument))                 
        self.instrument = None        

    @property
    def addr(self) -> str :
        if not hasattr(self, "_addr"):
             return None
        return self._addr

    @addr.setter
    def addr( self, addr:str):
        self._addr = addr

    # Low level communication
    def write(self, cmd ):
        logging.info( "write: {}".format(cmd))
        self.instrument.write(cmd)

    def query(self, cmd, strip=False ):
        logging.info( "query: {}".format(cmd))
        ret = self.instrument.query(cmd)
        if strip: ret = ret.rstrip()
        return( ret )

class Rigol(Osciloscope):
    """
    Rigol instrument
    """

    # Construct && close
    def __init__( self, ip:None, addr=None, debug = False ):
        if addr is None:
            addr = "TCPIP0::{}::INSTR".format(ip)
        super().__init__( addr=addr, debug=debug)
        self.ip = ip
        try:
           idn = self.instrument.query('*IDN?')
           logging.warning("Successfully connected  '{}' with '{}'".format(addr, idn))
        except:
           pass

    def ilScreenShot( self, filePath):
        cmd = "lxi  screenshot  {} --address {} >/dev/null".format( filePath, self.ip )
        logging.info( "ilScreenShot: cmd:{}".format(cmd))
        os.system(cmd)


        

class MSO1104(Rigol):
    """
    Rigol MS1104 osciloscope
    """

    # Construct && close
    def __init__( self, addr=None, ip=None, debug = False ):
        super().__init__( addr=addr, ip=ip, debug=debug)

        
    # Rigol specicig commands
    def rigolClear( self):
        self.write(":CLEAR")
        
    def rigolReset( self):
        self.write("*RST")

    def rigolChannelStatMeasure( self, item, ch, t):
         cmd = ":MEASure:STAT:ITEM? {},{},CHAN{}".format(t, item, ch)
         return( float(self.query(cmd)))

    def rigolChannelMeasure( self, item, ch):
         cmd = ":MEASure:ITEM? {},CHAN{}".format(item, ch)
         logging.info( "rigolChannelMeasure: cmd={}".format(cmd))
         return( float(self.query(cmd)))

    def rigolMeasurement(self, ch, item, t=None):
       if t is None:
           val = self.rigolChannelMeasure( item=item, ch=ch)
       else:
           val = self.rigolChannelStatMeasure( item=item, ch=ch, t=t )

       if val > 10**12:
            # Ridiculous values discard, e.g.g FREQ
            val = None
       return( val )

    def rigolChannelMeasurementStat( self, item, ch ):
        cmd = ":MEAS:STAT:ITEM {},CHAN{}".format( item, ch)
        self.write( cmd )
        
    def rigolChannelOnOff( self, ch, onOff:None):
        cmd = ":CHAN{}:DISP {}".format(ch,"ON" if onOff else "OFF" )
        return  self.write(cmd)

    def setdChOnOff( self, dCh, onOff:bool= None):
        cmd = ":LA:DIGI{}:DISPLAY {}" .format(dCh,"ON" if onOff else "OFF" )
        return  self.write(cmd)
    
    def rigolChannelProbe( self, ch, probe ):
        (val,unit) = self.valUnit(probe, validValues=["x"])
        cmd = ":CHAN{}:PROB {}".format( ch, probe)
        self.write( cmd )

    def rigolStatDisplayOnOff( self, statsOnOff):
        self.write( ":MEAS:STAT:DISP {}".format(statsOnOff))

    def rigolChannelAmsOnOff( self, source):
        if source in [1,2,3,4,"1","2","3","4"]:
            source = "CHAN{}".format(source)
        self.write( ":MEAS:AMS {}".format(source))

    def rigolChannelAdiOnOff( self, adiOnOff):
        self.write( ":MEAS:ADIS {}".format(adiOnOff))

    def rigolChannelOffset( self, ch, offset ):
        """Set or query the vertical offset of the specified channel. The
        default unit is V.

        Related to the current vertical scale and probe ratio When the
        probe ratio is 1X, vertical scale≥500mV/div: -100V to +100V
        vertical scale<500mV/div: -2V to +2V When the probe ratio is
        10X, vertical scale≥5V/div: -1000V to +1000V vertical
        scale<5V/div: -20V to +20V
        """
        cmd = ":CHAN{}:OFFSET {}".format( ch, offset)
        self.write( cmd )
         
    def rigolChannelScale( self, ch, scale ):
        """Set or query the vertical scale of the specified channel. The
        default unit is V.

        The range of the vertical scale is related to the current
        probe ratio (set by the :CHANnel<n>:PROBe command).

        You can use the :CHANnel<n>:VERNier command to enable or
        disable the fine adjustment of the vertical scale. By default,
        the fine adjustment is off. At this point, you can only set
        the vertical scale in 1-2-5 step, namely 10mV, 20mV, 50mV,
        100mV, ..., 100V (the probe ratio is 10X). When the fine
        adjustment is on, you can further adjust the vertical scale
        within a relatively smaller range to improve the vertical
        resolution. If the amplitude of the input waveform is a little
        bit greater than the full scale under the current scale and
        the amplitude would be a little bit lower if the next scale is
        used, fine adjustment can be used to improve the display
        amplitude of the waveform to view the signal details.

        """
        cmd = ":CHAN{}:SCAL {}".format( ch, scale)
        self.write( cmd )
         
    def rigolChannelDisplayUnit( self, ch, siUnit ):
        """Set or query the amplitude display unit of the specified channel"""
        def si2RigolUnit( siUnit):
            unitMapper = {
                "A": "AMP",
                "V": "VOLT",
                "W": "WATT",
            }
            rigolUnit = "UNKN"
            try:
                rigolUnit = unitMapper[siUnit]
            except KeyError as err:
                pass
            return rigolUnit
        cmd = ":CHAN{}:UNIT {}".format( ch,si2RigolUnit(siUnit))
        self.write(cmd)

    def rigolDigitalLabel( self, ch, label):
        self.write(":LA:DIGITAL{}:LABEL {}".format(ch, label) )
    
    def getName(self):
       return( self.query( "*IDN?"))
         
    def rigolDigitalPodOnOff( self, pod, onOff="ON" ):
        self.write(":LA:DISP POD{},{}".format(pod, onOff))

    def rigolStatClear(self, index=None ):
        if index == None:
            self.write(":MEAS:CLE ALL")
        else:
             self.write(":MEAS:CLE ITEM{}".format(index))

    # API --->
    def general( self, statsOnOff=None, adiOnOff=None, amSource=None):
        """
        Scope general settings: statsittis on/off
        """
        if statsOnOff in ["ON", "1","OFF", "0" ]:
            # self.write( ":MEAS:STAT:DISP {}".format(statsOnOff))
            self.rigolStatDisplayOnOff(statsOnOff)
        if amSource is not None and not not amSource:
            for source in amSource.split(","):
                # if source in [1,2,3,4,"1","2","3","4"]:
                #     source = "CHAN{}".format(source)
                # self.write( ":MEAS:AMS {}".format(source))
                self.rigolChannelAmsOnOff( source)
        if adiOnOff in ["ON", "1","OFF", "0" ]:
            self.rigolChannelAdiOnOff(adiOnOff )
        self.delay()
    
    def delay(self, delay=1):
        sleep(delay)
    
    def reset(self):
        self.rigolReset()

    def clear(self):
        self.rigolClear()
        self.delay()

    def setup(self, channel, probe="10x", scale=None, offset=None, stats=None):
        """Setup osciloscope 'channel' probe attenuation, scale and offset, and
        statistic measurement collection.


        :probe: Attenuation factor of the probe used (default probe=10x). 

        :scale: Set vertical scale and unit of 'channel', if given (=no
        change if not give). Example: scale=1V.

        :offset: Set offset and unit of channel

        :stats: comma separed list of measurement items to start
        collecting in scope bottom row. Empty list does not change
        measurement statistic collection

        Valid measument identifiers: MAX, VMIN, VPP, VTOP, VBASe,
        VAMP, VAVG, VRMS, OVERshoot, MARea, MPARea, PREShoot, PERiod,
        FREQuency, RTIMe, FTIMe, PWIDth, NWIDth, PDUTy, NDUTy, TVMAX,
        TVMIN, PSLEWrate, NSLEWrate, VUPper, VMID, VLOWer, VARIance,
        PVRMS, PPULses, NPULses, PEDGes, and NEDGes

        """
        logging.info( "Setup channel: {}, stats='{}'".format(channel, stats))
        self.rigolChannelOnOff( ch=channel, onOff = True )
        if probe is None or not probe:
            probe = "10x"
        self.rigolChannelProbe( channel, probe )
        if scale is not None and not not scale:
            (val,siUnit) = self.valUnit(scale)
            self.rigolChannelScale(channel,val)
            self.rigolChannelDisplayUnit(channel,siUnit)
        if offset is not None and not not offset:
            (val,siUnit) = self.valUnit(offset)
            self.rigolChannelOffset(channel,val)
            self.rigolChannelDisplayUnit(channel,siUnit)
        if stats is not None and not not stats:
            items = stats.split(",")
            for item in items:
                self.rigolChannelMeasurementStat(item=item.upper(), ch=channel)
        self.delay()

    def measurement( self, ch, measurements:str, sep=","):
        logging.info( "measurement ch: {}, measurements: {}".format(ch, measurements))
        measuremenList = measurements.split(sep)
        measurementResults =  {
            measurement.upper(): self.rigolMeasurement( ch, measurement.upper() ) for measurement in measuremenList 
            
        }
        return measurementResults
        

    def clearStats( self):
        self.rigolStatClear()
        
    def podSetup( self, pod, labels=None, sep="," ):
        """Put 'pod' 1/2 on display and update 8 pod digital channel labels.

        :labels: list of (4 char) eigth strings (1 pod/8 channels)
        separated by 'sep' -character. Empty strin for missing labels.

        :sep: label separator in 'labels'
        """

        # Set POD display on
        self.rigolDigitalPodOnOff( pod=pod, onOff="ON" )

        # Extract digial channel labels (separated by)
        labelArray = labels.split(sep)
        labelCount = len(labelArray)
        emptyLabels = [""] * (8-labelCount) if labelCount < 8  else []
        labelArray =  labelArray + emptyLabels
        pod = int(pod)

        # Create dict mapping label number to label text
        labelNames = {
           (pod-1)*8 + k: labelArray[k]   for k in range(8)    
        }
        logging.debug( "podSetup, labelNames={}".format(labelNames))

        # Write labels to scope
        for ch,label in labelNames.items():
            #self.write(":LA:DIGITAL{}:LABEL {}".format(ch, label) )
            self.rigolDigitalLabel(ch,label)
            self.delay(0.2)
        
    def digitalPodOff( self, pod ):
        self.rigolDigitalPodOnOff( pod=pod, onOff="OFF" )
        self.delay()
        
    def channelOn(self, ch ):
        logging.info( "on ch: {}".format(ch))
        self.rigolChannelOnOff( ch=ch, onOff = True )
        self.delay()        
        
        
    def channelOff(self, ch ):
        logging.info( "off ch: {}".format(ch))
        self.rigolChannelOnOff( ch=ch, onOff = False )
        self.delay()

        
         
# ------------------------------------------------------------------
# State && access state

# def skooppi():
#     logging.info( "Open skooppi in: {}".format(FLAGS.addr))
#     return MSO1104(addr = FLAGS.addr, ip=FLAGS.ip)

# cmdController = Cmd()

# ------------------------------------------------------------------
# Menu: command parameters

helpPar = {
      "command": "Command to give help on (None: help on main menu)"
}

channelPar = {
    "channel"  : "Channel 1-4 to act upon"
}
setupPar = channelPar | {
    "probe"    : "Probe value (default 10x) [x]",
    "offset"   : "Channel offset, value + unit[V,A,W]",
    "scale"    : "Channel scale, value + unit[V,A,W]",
    "stats"    : "Comma -separated list of stat measuremnts",
}

measurePar = channelPar | {
     "measurements"   : "Comma -separated list of measurements"
}


onOffPar = channelPar

stopRecordingPar = {
    "fileName" : "Filename to store recording, '.' show current playback list",
}

podPar ={
    "pod" : "Pod number (1,2)",
}

screenCapturePar  = {
    'fileName'   :   "Screen capture file name (optional)",    
}

generalPar = {
    "statsOnOff": "Display statistics ON/OFF",
    "amSource"  : "All measurement source, Comma separated list: 1/2/3/4/MATH",
    "adiOnOff"  : "All measurement display ON/OFF",
}


podOffPar = podPar 

podSetupPar = podPar | {
    "labels" : "Pod 4-character labels separated with comma(,)",
}

def mainMenuHelp(mainMenu):
    mainMenuHelpCommon( cmd=CMD, mainMenu=mainMenu, synopsis="Tool to control UNIT-T UTG900 Waveform generator")


# ------------------------------------------------------------------
# Main

def _main( _argv ):
    # global gSkooppi
    logging.set_verbosity(FLAGS.debug)
    
    gSkooppi=MSO1104(addr=FLAGS.addr, ip=FLAGS.ip)
    cmdController = Cmd()

    mainMenu = {
        "Init"              : (None, None, None),
        "general"           : ( "General setup", generalPar, gSkooppi.general),
        "setup"             : ( "Setup channel", setupPar, gSkooppi.setup ),
        "podSetup"          : ( "Setup digical channels", podSetupPar, gSkooppi.podSetup),
        "podOff"            : ( "Setup digical channels", podOffPar, gSkooppi.digitalPodOff),
        "on"                : ( "Open channel", onOffPar, gSkooppi.channelOn),
        "off"               : ( "Close channel", onOffPar, gSkooppi.channelOff),
        "statClear"         : ( "Clear statistics", None, gSkooppi.clearStats),
        "reset"             : ( "Send reset to Rigol", None, gSkooppi.reset),
        "clear"             : ( "Send clear to Rigol", None, gSkooppi.clear),
        "Measure"           : (None, None, None),
        "measure"           : ("Measure", measurePar, gSkooppi.measurement),
        "Record"            : (None, None, None),
        Cmd.MENU_REC_START  : ( "Start recording", None, menuStartRecording(cmdController) ),
        Cmd.MENU_REC_SAVE   : ( "Stop recording", stopRecordingPar, menuStopRecording(cmdController, pgm=_argv[0], fileDir=FLAGS.recordingDir) ),
        Cmd.MENU_SCREEN     : ( "Take screenshot", screenCapturePar, menuScreenShot(instrument=gSkooppi,captureDir=FLAGS.captureDir,prefix="Rigol-" )),
        "Misc"              : (None, None, None),        
        Cmd.MENU_VERSION    : ( "Output version number", None, version ),
        "Help"              : (None, None, None),                
        Cmd.MENU_QUIT       : ( "Exit", None, None),
        Cmd.MENU_HELP       : ( "List commands", None,
                             lambda **argV: usage(mainMenu=mainMenu, mainMenuHelp=mainMenuHelp, subMenuHelp=subMenuHelp, **argV )),
        Cmd.MENU_CMD_PARAM  : ( "List command parameters", helpPar,
                             lambda **argV: usage(mainMenu=mainMenu, mainMenuHelp=mainMenuHelp, subMenuHelp=subMenuHelp, **argV )),
    }

    
    cmdController.mainMenu( _argv, mainMenu=mainMenu, mainPrompt="[q=quit,?=commands,??=help on command]")
    if gSkooppi is not None:
        gSkooppi.close()
        gSkooppi = None

def main():
    try:
        app.run(_main)
    except SystemExit:
        pass
    
    
if __name__ == '__main__':
    main()
    # try:
    #     app.run(main)
    # except SystemExit:
    #     pass
    
    
