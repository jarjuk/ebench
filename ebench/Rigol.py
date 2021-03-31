#!/usr/bin/env python3

import os
from absl import app, flags, logging
from absl.flags import FLAGS

import pyvisa
from time import sleep

from ebench import version, Ebench, Cmd, subMenuHelp, mainMenuHelpCommon, usage

CMD="Rigol"
ADDR = "TCPIP0::skooppi::INSTR"
flags.DEFINE_string('addr', ADDR, "UTG900 pyvisa resource address")
flags.DEFINE_string('captureDir', "pics", "Capture directory")
flags.DEFINE_string('recordingDir', "tmp", "Directory where recordings are saved into")

class MSO1104(Ebench):
    """
    Rigol MS1104 osciloscope services
    """


    # Construct && close
    def __init__( self, addr=ADDR,  debug = False ):
        super().__init__( debug=debug)
        self.rm = pyvisa.ResourceManager()
        self.addr = addr
        self.ip = "skooppi"
        self.skooppi = Ebench.singleton_rm().open_resource(addr)
        try:
           self.idn = self.skooppi.query('*IDN?')
           logging.warning("Successfully connected  '{}' with '{}'".format(addr, self.idn))
        except:
           pass

    def close(self):
        super().close()
        try:
            logging.info(  "Closing skooppi {}".format(self.skooppi))
            self.skooppi.close()
        except:
            logging.error(  "Closing skooppi {} - failed".format(self.skooppi))                 
        self.skooppi = None        

    # Low level commuincation 
    def write(self, cmd ):
        logging.info( "write: {}".format(cmd))
        self.skooppi.write(cmd)

    def query(self, cmd, strip=False ):
        logging.info( "query: {}".format(cmd))
        ret = self.skooppi.query(cmd)
        if strip: ret = ret.rstrip()
        return( ret )

    # IL (intermediate language)
    def measureStatItem( self, item, ch, t):
         cmd = ":MEASure:STAT:ITEM? {},{},CHAN{}".format(t, item, ch)
         return( float(self.query(cmd)))

    def measureItem( self, item, ch):
         cmd = ":MEASure:ITEM? {},CHAN{}".format(item, ch)
         logging.info( "measureItem: cmd={}".format(cmd))
         return( float(self.query(cmd)))

    def oneMeasurement(self, ch, item, t=None):
       if t is None:
           val = self.measureItem( item=item, ch=ch)
       else:
           val = self.measureStatItem( item=item, ch=ch, t=t )

       if val > 10**12:
            # Ridiculous values discard, e.g.g FREQ
            val = None

       return( val )

    def ilScreenShot( self, filePath):
        cmd = "lxi  screenshot  {} --address {} >/dev/null".format( filePath, self.ip )
        logging.info( "ilScreenShot: cmd:{}".format(cmd))
        os.system(cmd)


    def setStat( self, item, ch ):
        cmd = ":MEAS:STAT:ITEM {},CHAN{}".format( item, ch)
        self.write( cmd )
        
    # def chUnit( self, ch):
    #     cmd = "CHAN{}:UNIT?".format(ch)
    #     return  self.query(cmd, strip=True)

    def setChOnOff( self, ch, onOff:None):
        cmd = ":CHAN{}:DISP {}".format(ch,"ON" if onOff else "OFF" )
        return  self.write(cmd)

    def setdChOnOff( self, dCh, onOff:bool= None):
        cmd = ":LA:DIGI{}:DISPLAY {}" .format(dCh,"ON" if onOff else "OFF" )
        return  self.write(cmd)
        
    
    def setProbe( self, ch, probe ):
        (val,unit) = self.valUnit(probe, validValues=["x"])
        cmd = ":CHAN{}:PROB {}".format( ch, probe)
        self.write( cmd )

    def setOffset( self, ch, offset ):
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
         
    def setScale( self, ch, scale ):
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
         
    def setDisplayUnit( self, ch, siUnit ):
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

    def getName(self):
       return( self.query( "*IDN?"))

    # def laPod1On( self  ):
    #      self.displayLAPod( pod=1, onOff="ON")
         
    def displayLAPod( self, pod, onOff="ON" ):
        self.write(":LA:DISP POD{},{}".format(pod, onOff))

    # def laPod1Off( self ):
    #      self.displayLAPod( pod=1, onOff="OFF")

    # def laLabels( self, labels:dict=None ):
    #      """Set labels on LogicAnalyzer ch, None clears

    #      :labels: dictionary with ascii keys 0..15
    #      """
    #      if labels is None:
    #          labels = { "{}".format(i): "" for i in range(16) }
    #      # labels = defaultLabels | labels
    #      # print( labels )
    #      for ch,label in labels.items():
    #           self.write(":LA:DIGITAL{}:LABEL {}".format(ch, label) )
    #           self.delay(0.2)

    # def measureFreq(self, ch, t=None):
    #     """
    #     :t: type MAX, MIN, CURRent, AVERages
    #     """
    #     return self.oneMeasurement( item="FREQ", ch=ch, t=t)

    # def measureVpp(self, ch, t=None):
    #     return self.oneMeasurement( item="VPP", ch=ch, t=t)

    # def measureVmin(self, ch, t=None):
    #     return self.oneMeasurement( item="VMIN", ch=ch, t=t)

    # def measureVmax(self, ch, t=None):
    #     return self.oneMeasurement( item="VMAX", ch=ch, t=t)

    # def measurePeriod(self, ch, t=None):
    #     return self.oneMeasurement( item="PER", ch=ch, t=t)

    # def statFreq(self, ch, t=None):
    #     return self.setStat( item="FREQ", ch=ch)

    # def statPeriod(self, ch, t=None):
    #     return self.setStat( item="PER", ch=ch)

    def statClear(self, index=None ):
        if index == None:
            self.write(":MEAS:CLE ALL")
        else:
             self.write(":MEAS:CLE ITEM{}".format(index))

    # API --->
    def delay(self, delay=1):
        sleep(delay)
    
    def reset(self):
         self.write("*RST")
         self.delay()

    def setup(self, ch, probe="10x", scale=None, offset=None):
        logging.info( "Setup ch: {}".format(ch))
        self.setChOnOff( ch=ch, onOff = True )
        if probe is None or not probe:
            probe = "10x"
        self.setProbe( ch, probe )
        if scale is not None and not not scale:
            (val,siUnit) = self.valUnit(scale)
            self.setScale(ch,val)
            self.setDisplayUnit(ch,siUnit)
        if offset is not None and not not offset:
            (val,siUnit) = self.valUnit(offset)
            self.setOffset(ch,val)
            self.setDisplayUnit(ch,siUnit)
        self.delay()

    def measurement( self, ch, measurements:str, sep=","):
        logging.info( "measurement ch: {}, measurements: {}".format(ch, measurements))
        measuremenList = measurements.split(sep)
        measurementResults =  {
            measurement.upper(): self.oneMeasurement( ch, measurement.upper() ) for measurement in measuremenList 
            
        }
        return measurementResults
        

    def podSetup( self, pod, labels=None, sep="," ):
        """Put 'pod' 1/2 on display and update 8 pod digital channel labels.

        :labels: list of (4 char) eigth strings (1 pod/8 channels)
        separated by 'sep' -character. Empty strin for missing labels.

        :sep: label separator in 'labels'

        """

        # Set POD display on
        self.displayLAPod( pod=pod, onOff="ON" )

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
              self.write(":LA:DIGITAL{}:LABEL {}".format(ch, label) )
              self.delay(0.2)
        
        
    def podOff( self, pod ):
        self.displayLAPod( pod=pod, onOff="OFF" )
        self.delay()
        
    def on(self, ch ):
        logging.info( "on ch: {}".format(ch))
        self.setChOnOff( ch=ch, onOff = True )
        self.delay()        
        
        
    def off(self, ch ):
        logging.info( "off ch: {}".format(ch))
        self.setChOnOff( ch=ch, onOff = False )
        self.delay()

        
         
# ------------------------------------------------------------------
# State && access state

def skooppi():
    logging.info( "Open skooppi in: {}".format(FLAGS.addr))
    return MSO1104(addr = FLAGS.addr)

cmdController = Cmd()

# ------------------------------------------------------------------
# Menu: command parameters

helpPar = {
      "command": "Command to give help on (None: help on main menu)"
}

channelPar = {
    "ch"       : "Channel 1-4"
}
setupPar = channelPar | {
    "probe"    : "Probe value (default 10x) [x]",
    "offset"   : "Channel offset, value + unit[V,A,W]",
    "scale"    : "Channel scale, value + unit[V,A,W]",
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


podOffPar = podPar 

podSetupPar = podPar | {
    "labels" : "Pod 4-character labels separated with comma(,)",
}

def mainMenuHelp(mainMenu):
    mainMenuHelpCommon( cmd=CMD, mainMenu=mainMenu, synopsis="Tool to control UNIT-T UTG900 Waveform generator")

# ------------------------------------------------------------------
# Main


def main( _argv ):
    # global gSkooppi
    logging.set_verbosity(FLAGS.debug)
    
    gSkooppi=MSO1104(addr=FLAGS.addr)
    cmdController = Cmd()

    mainMenu = {
        "Init"           : (None, None, None),
        "setup"          : ( "Setup channel", setupPar, gSkooppi.setup ),
        "podSetup"       : ( "Setup digical channels", podSetupPar, gSkooppi.podSetup),
        "podOff"         : ( "Setup digical channels", podOffPar, gSkooppi.podOff),
#       "on"             : ( "Open channel", onOffPar, gSkooppi.on ), 
        "off"            : ( "Close channel", onOffPar, gSkooppi.off),
        "reset"          : ( "Send reset to Rigol", None, gSkooppi.reset),
        "Measure"        : (None, None, None),
        "measure"        : ("Measure", measurePar, gSkooppi.measurement),
        "Record"         : (None, None, None),
        "!"              : ( "Start recording", None, cmdController.startRecording),
        "."              : ( "Stop recording", stopRecordingPar,
                             lambda **argv: cmdController.stopRecording( pgm=_argv[0], fileDir=FLAGS.recordingDir, **argv ) ),
        "screen"         : ( "Take screenshot", screenCapturePar,
                             lambda **argv: gSkooppi.screenShot( captureDir = FLAGS.captureDir, prefix="Rigol-", **argv)),
        "Misc"           : (None, None, None),        
        "list_resources" : ( "List pyvisa resources (=pyvisa list_resources() wrapper)'", None, lambda: print(Ebench.list_resources()) ),
        "version"        : ( "Output version number", None, lambda : print(version())),
        "Help"           : (None, None, None),                
        'q'              : ( "Exit", None, None),
        '?'              : ( "List commands", None,
                             lambda **argV: usage(mainMenu=mainMenu, mainMenuHelp=mainMenuHelp, subMenuHelp=subMenuHelp, **argV )),
        '??'             : ( "List command parameters", helpPar,
                             lambda **argV: usage(mainMenu=mainMenu, mainMenuHelp=mainMenuHelp, subMenuHelp=subMenuHelp, **argV )),
        
    }

    
    cmdController.mainMenu( _argv, mainMenu=mainMenu, mainPrompt="[q=quit,?=commands,??=help on command]")
    if gSkooppi is not None:
        gSkooppi.close()
        gSkooppi = None


if __name__ == '__main__':
    try:
        app.run(main)
    except SystemExit:
        pass
    
    
