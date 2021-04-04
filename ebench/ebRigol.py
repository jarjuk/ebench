from .Rigol import RigolScope
from .ebench import MenuCtrl, usage, usageCommand, menuStartRecording, menuStopRecording, menuScreenShot, version

# Installing this module as command
from .CMDS import CMD_RIGOL
CMD=CMD_RIGOL

from absl import app, logging
from absl.flags import FLAGS
from time import sleep



class MSO1104(RigolScope):
    """Rigol MS1104 osciloscope commands (grouping elementary actions to
    groups controlled using ebench commands)
    """

    # Construct && close
    def __init__( self, addr=None, ip=None, debug = False ):
        super().__init__( addr=addr, ip=ip, debug=debug)
    
    # ------------------------------------------------------------------        
    # API --->

    
    def general( self, statsOnOff=None, adiOnOff=None, amSource=None):
        """Scope general settings: 
        - measurement statistics (:MEAS:STAT) on/off
        - channel all measurements (:MEAS:AMS) on/off
        - channel all display (MEAS:ADIS) on/off

        :statsOnOff: valid values ON/1/OFF/0

        :adiOnOff: list of channel 1-4 and MATH separeted with comma

        :amSource: valid values ON/1/OFF/0

        """
        if statsOnOff in ["ON", "1","OFF", "0" ]:
            # self.write( ":MEAS:STAT:DISP {}".format(statsOnOff))
            self.rigolStatDisplayOnOff(statsOnOff)
        if amSource is not None and not not amSource:
            for source in amSource.split(","):
                # if source in [1,2,3,4,"1","2","3","4"]:
                #     source = "CHAN{}".format(source)
                # self.write( ":MEAS:AMS {}".format(source))
                self.rigolChannelAmsOnOff(source)
        if adiOnOff in ["ON", "1","OFF", "0" ]:
            self.rigolChannelAdiOnOff(adiOnOff )
        self.delay()
    
    def reset(self):
        self.pyvisaReset()

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


    def measurement( self, measurements:str, csvFile:str=None, sep=",", sep2=":"):
        """Make AVERAGE 'measurements' (:MEASure:ITEM? {},CHAN{}') from scope and
        save result to 'csvFile'

        :measurements: Comma separated list of ch:item pairs.  For
        example, '1:Vavg,2:FREQ' measures Vrms on channel 1 and
        frequency on channel 2.
        
        :csvFile:  name of CSV file where to append the results

        """
        logging.info( "measurement: measurements={}, csvFile={}".format(measurements, csvFile))
        measuremenList = [ chItem.split(sep2) for chItem  in measurements.split(sep) ]
        statistic = "AVER"
        logging.debug( "measurement: measuremenList{}".format(measuremenList))
        
        measurementRow =  {
            "{}:{}".format(ch,item.upper()): self.rigolMeasurement( ch, item=item.upper(), statistic=statistic )
            for (ch,item) in measuremenList 
            
        }
        if csvFile is not None and not not csvFile:
            self.instrumentAppendCvsFile( csvFile, measurementRow )
        return measurementRow

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

    def setupTrigger( self, source, slope, level ):
        """Setup trigger level. This includes defining:

        - setup edge trigger  source
        - setup trigger slope
        - setup edge trigger  level

        :source: D0, D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11,
        D12, D13, D14, D15, CHAN1, CHAN2, CHAN3, CHAN4, or AC        

        :slope: POS, NEG, or RFAL

        :level: The unit is the same as the current amplitude unit of
        the signal source selected. 

        
        """
        logging.info( "setupTrigger: source:{}, slope: {}, level:{}".format(
            source, slope, level))
        if source is not None and not not source:
            self.rigolTriggerEdgeSource( source=MSO1104.channelToRigolSource(source))
        if slope is not None and not not slope:
            self.rigolTriggerEdgeSlope(slope)
        if level is not None and not not level:
            self.rigolTriggerEdgeLevel(level)
        
    def triggerStatus( self ):
        """Return trigger status (:TRIG:STAT) 
        """
        status = self.rigolTriggerStatusQuery()
        logging.info( "triggerStatus: status:{}".format(status))
        return status
        
    def digitalPodOff( self, pod ):
        self.rigolDigitalPodOnOff( pod=pod, onOff="OFF" )
        self.delay()
        
    def channelOn(self, channel ):
        logging.info( "on ch: {}".format(channel))
        self.rigolChannelOnOff( ch=channel, onOff = True )
        self.delay()        
        
        
    def channelOff(self, channel ):
        logging.info( "off ch: {}".format(channel))
        self.rigolChannelOnOff( ch=channel, onOff = False )
        self.delay()

    # ------------------------------------------------------------------
    # Utitlities

    def delay(self, delay=1):
        """API actions wait allow scope to settle before next action

        :delay: number of base units to wait before next action

        """
        delayUnit=0.2
        sleep(delay*delayUnit)

    def channelToRigolSource( channel:str ) -> str:
        """We are using numbers 1,2,3,4 to refer scope channels, 
        all other names are expected to be Rigol names

        :channel: Number 1,2,3,4, D0, ... D15, AC
        
        :return: CHAN1,...D0, ...

        """
        if channel in ["1", "2", "3", "4", 1, 2, 3, 4]:
            return "CHAN{}".format(channel)
        return channel


# ------------------------------------------------------------------
# Menu: command parameters

CMD_MEASURE= "measure"
CMD_SETUP_TRIGGER= "setupTrigger"
CMD_TRIGGER_STATUS="_triggerStatus"

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

triggerSetupPar = {

    "source"   : "Trigger source 1,2,3,4,D0..D15",
    "slope"    : "Trigger source POS,NEG,RFAL",
    "level"    : "Trigger level (without unit)",
    
}

measurePar =  {
    "measurements"   : "Comma -separated list of measurements",
    "csvFile"        : "Name of CSV-file for appending measurements into",
}
measureDefaults = {
    "measurements": "1:Vavg,2:FREQ",
    "csvFile": "measurement.csv",
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
    "amSource"  : "All measurement source, Comma separated list: 1,2,3,4,MATH",
    "adiOnOff"  : "All measurement display ON/OFF",
}


podOffPar = podPar 

podSetupPar = podPar | {
    "labels" : "Pod 4-character labels separated with comma(,)",
}


defaults = {
    CMD_MEASURE: measureDefaults,
    CMD_SETUP_TRIGGER: { k: None for k in triggerSetupPar.keys()},
}


# ------------------------------------------------------------------
# Main

def _main( _argv ):
    # global gSkooppi
    logging.set_verbosity(FLAGS.debug)
    
    gSkooppi=MSO1104(addr=FLAGS.addr, ip=FLAGS.ip)
    cmdController = MenuCtrl()

    mainMenu = {
        "Init"                   : (None, None, None),
        "general"                : ( "General setup", generalPar, gSkooppi.general),
        "setup"                  : ( "Setup channel", setupPar, gSkooppi.setup ),
        CMD_SETUP_TRIGGER        : ( "Setup trigger", triggerSetupPar, gSkooppi.setupTrigger ),
        "podSetup"               : ( "Setup digical channels", podSetupPar, gSkooppi.podSetup),
        "podOff"                 : ( "Setup digical channels", podOffPar, gSkooppi.digitalPodOff),
        "on"                     : ( "Open channel", onOffPar, gSkooppi.channelOn),
        "off"                    : ( "Close channel", onOffPar, gSkooppi.channelOff),
        "statClear"              : ( "Clear statistics", None, gSkooppi.clearStats),
        "reset"                  : ( "Send reset to Rigol", None, gSkooppi.reset),
        "clear"                  : ( "Send clear to Rigol", None, gSkooppi.clear),
        "Measure"                : (None, None, None),
        CMD_MEASURE              : ("Measure", measurePar, gSkooppi.measurement),
        CMD_TRIGGER_STATUS       : ("Trigger status", None, gSkooppi.triggerStatus),
        "Record"                 : (None, None, None),
        MenuCtrl.MENU_REC_START  : ( "Start recording", None, menuStartRecording(cmdController) ),
        MenuCtrl.MENU_REC_SAVE   : ( "Stop recording", stopRecordingPar, menuStopRecording(cmdController, pgm=_argv[0], fileDir=FLAGS.recordingDir) ),
        MenuCtrl.MENU_SCREEN     : ( "Take screenshot", screenCapturePar,
                                     menuScreenShot(instrument=gSkooppi,captureDir=FLAGS.captureDir,prefix="Rigol-" )),
        "Misc"                   : (None, None, None),        
        MenuCtrl.MENU_VERSION    : ( "Output version number", None, version ),
        "Help"                   : (None, None, None),                
        MenuCtrl.MENU_QUIT       : ( "Exit", None, None),
        MenuCtrl.MENU_HELP       : ( "List commands", None,
                                    lambda **argV: usage(cmd=CMD, mainMenu=mainMenu, synopsis="Tool to control Rigol MSO1104Z osciloscope")),
        MenuCtrl.MENU_CMD_PARAM  : ( "List command parameters", helpPar,
                                 lambda **argV: usageCommand(mainMenu=mainMenu, **argV )),
    }

    
    cmdController.mainMenu( _argv, mainMenu=mainMenu
                            , mainPrompt="[q=quit,?=commands,??=help on command]"
                            , defaults=defaults)
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
    
    
