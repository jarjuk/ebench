# Tangled from TEMPLATE.org - changes will be overridden


from ebench import PyInstrument
from ebench import MenuCtrl

from ebench import usage, usageCommand, menuStartRecording, menuStopRecording, menuScreenShot, version

import os
from time import sleep
from absl import logging


# ------------------------------------------------------------------
# Usage 
CMD="example"

SYNOPSIS="Example to setup oscilloscope"

USAGE_TEXT=f""" 
A minimal running example ebench tool for setting up oscilloscope
configuration.

Tested on Rigol MSO1104Z. 


"""


# ------------------------------------------------------------------
# Acces instrument API

class InstrumentApiException(Exception):
      pass

class MyConfigurationError(InstrumentApiException):
      pass
class MyRuntimeError(InstrumentApiException):
      pass

class InstrumentApi(PyInstrument):
    """Abstract base class, which inherits from 'PyInstrument' i.e.
    can be controlled using pyvisa.
    """

    # Constructor && setup
    def __init__(self, ip=None):
        logging.info( "InstrumentApi: ip={}".format(ip))
        if ip is None:
            raise MyConfigurationError( "Missing configuration 'ip'")
        self.ip = ip
        # Init pyvisa on address
        addr = "TCPIP0::{}::INSTR".format(ip)
        super().__init__(addr=addr)

    # Destructor && close stuff
    def close(self):
        logging.info( "InstrumentApi: closing all my resources, pass to super")
        super().close()

    # Template implementation
    def screenShotImplementation( self, filePath):
        """Screenshot implementation using lxi command line

        :filePath: path where to save screen shot

        :return: filePath in success, None in error

        """
        cmd = "lxi  screenshot  {} --address {} >/dev/null".format( filePath, self.ip )
        logging.info( "screenShotImplementation: cmd:{}".format(cmd))
        status = os.system(cmd)
        logging.debug( "screenShotImplementation: status={} after {}".format(status,cmd))
        if status != 0:
            msg = "status={} for cmd={}".format(status, cmd)
            logging.error(msg)
            return None
        return filePath



    # Elementary services 
    def baseDelay(self, delay=1):
        """Allow instrument to settle before next action.

        :delay: number of base units to wait before next action

        """
        delayUnit=0.2
        sleep(delay*delayUnit)

    # API services
    def baseReset(self):
        self.pyvisaReset()

    def baseChannelOnOff( self, channel, onOff:None):
        cmd = ":CHAN{}:DISP {}".format(channel,"ON" if onOff else "OFF" )
        return  self.write(cmd)


    def baseChannelScale( self, channel, scale ):
        """Set or query the vertical scale of the specified channel. The
        default unit is V.
        """
        cmd = ":CHAN{}:SCAL {}".format( channel, scale)
        self.write( cmd )

    def baseChannelOffset( self, channel, offset ):
        """Set or query the vertical offset of the specified channel. The
        default unit is V.

        Related to the current vertical scale and probe ratio When the
        probe ratio is 1X, vertical scale≥500mV/div: -100V to +100V
        vertical scale<500mV/div: -2V to +2V When the probe ratio is
        10X, vertical scale≥5V/div: -1000V to +1000V vertical
        scale<5V/div: -20V to +20V
        """
        cmd = ":CHAN{}:OFFSET {}".format( channel, offset)
        self.write( cmd )


    def baseChannelDisplayUnit( self, channel, siUnit ):
        """Set or query the amplitude display unit of the specified channel"""
        def si2ScopeUnit( siUnit):
            unitMapper = {
                "A": "AMP",
                "V": "VOLT",
                "W": "WATT",
            }
            baseUnit = "UNKN"
            try:
                baseUnit = unitMapper[siUnit]
            except KeyError:
                pass
            return baseUnit
        cmd = ":CHAN{}:UNIT {}".format( channel,si2ScopeUnit(siUnit))
        self.write(cmd)

    def baseChannelMeasurementStat( self, channel, item ):
        """
        :channel: channel number 1,2,3,4
        """
        cmd = ":MEAS:STAT:ITEM {},CHAN{}".format( item, channel)
        self.write( cmd )

# ------------------------------------------------------------------
# Facade presented to user
class InstrumentFacade(InstrumentApi):
    def __init__( self, ip=None):
        super().__init__( ip=ip )

    def reset(self):
        """Reset scope to default state
         reset

        """
        self.baseReset()

    def setup(self, channel, scale=None, offset=None, stats=None ):
        """Setup osciloscope 'channel', measurement scale (scale), screen
        offset (offset), and measurement collection on the screen
        bottm row (stats)

        :scale: Set vertical scale and unit of 'channel', if given (=no
        change if not given). Example: scale=1V.

        :offset: Set offset and unit of channel. No change if not
        given

        :stats: comma separed list of measurement items to start
        collecting in scope bottom row. Empty list does not change
        measurement statistic collection

        Valid measument identifiers: MAX, VMIN, VPP, VTOP, VBASe,
        VAMP, VAVG, VRMS, OVERshoot, MARea, MPARea, PREShoot, PERiod,
        FREQuency, RTIMe, FTIMe, PWIDth, NWIDth, PDUTy, NDUTy, TVMAX,
        TVMIN, PSLEWrate, NSLEWrate, VUPper, VMID, VLOWer, VARIance,
        PVRMS, PPULses, NPULses, PEDGes, and NEDGes

        """
        logging.info( "Setup channel: {}, stats='{}'".format(channel, stats ))
        self.baseChannelOnOff( channel=channel, onOff = True )
        if scale is not None and not not scale:
            (val,siUnit) = self.instrumentValUnit(scale)
            self.baseChannelScale(channel,val)
            self.baseChannelDisplayUnit(channel,siUnit)
        if offset is not None and not not offset:
            (val,siUnit) = self.instrumentValUnit(offset)
            self.baseChannelOffset(channel,val)
            self.baseChannelDisplayUnit(channel,siUnit)
        if stats is not None and not not stats:
            items = stats.split(",")
            for item in items:
                self.baseChannelMeasurementStat(item=item.upper(), channel=channel)
        self.baseDelay()


# ------------------------------------------------------------------
# Menu
CMD_RESET= "reset"
CMD_SETUP= "setup"

channelPar = {
    "channel"  : "Channel 1-4 to act upon"
}

setupPar = channelPar | {
    "scale"    : "Channel scale, value + unit[V,A,W]",
    "offset"   : "Channel offset, value + unit[V,A,W]",
    "stats"    : "Comma -separated list of stat measuremnts",
}

defaults = {
   CMD_SETUP: {
        "offset": "0V"
   }
}

# ------------------------------------------------------------------
# Bind instrument controller classes to ebench toolset
def run( _argv, ip:str=None
     , runMenu:bool = True
     , outputTemplate=None, captureDir=None, recordingDir=None ):
    """Examaple template 

    :runMenu: default True, standalone application call REPL-loop
    'menuController.mainMenu()', subMenu constructs 'menuController'
    without executing the loop

    :outputTemplate: if None(default): execute cmds/args, else (not
    None): map menu actions to strings using 'outputTemplate'

    :recordingDir: directory where interactive session recordings are
    saved to (defaults to 'FLAGS.recordingDir')

    :captureDir: directory where screenshots are made, defaults to
    'FLAGS.captureDir'

    :return: MenuCtrl (wrapping instrument)

    """

    # 'instrument' controlled by application 
    instrument = InstrumentFacade(ip=ip) 

    # Wrap instrument with 'MenuCtrl'
    menuController = MenuCtrl( args=_argv,instrument=instrument
                             , prompt="[q=quit,?=commands,??=help on command]"
                             , outputTemplate=outputTemplate )

    mainMenu = {
        CMD                      : MenuCtrl.MENU_SEPATOR_TUPLE,
        # Application menu 
        CMD_RESET                : ( "Send reset to Scope", None, instrument.reset),
        CMD_SETUP                : ( "Setup channel", setupPar, instrument.setup ),

        "Util"                   : MenuCtrl.MENU_SEPATOR_TUPLE,
        MenuCtrl.MENU_REC_START  : ( "Start recording", None, menuStartRecording(menuController) ),
        MenuCtrl.MENU_REC_SAVE   : ( "Stop recording", MenuCtrl.MENU_REC_SAVE_PARAM, menuStopRecording(menuController, recordingDir=recordingDir) ),
        MenuCtrl.MENU_SCREEN     : ( "Take screenshot", MenuCtrl.MENU_SCREENSHOT_PARAM,
                                     menuScreenShot(instrument=instrument,captureDir=captureDir,prefix="Capture-" )),
        MenuCtrl.MENU_HELP       : ( "List commands", None,
                                    lambda **argV: usage(cmd=CMD, mainMenu=mainMenu, synopsis=SYNOPSIS, usageText=USAGE_TEXT)),
        MenuCtrl.MENU_HELP_CMD   : ( "List command parameters", MenuCtrl.MENU_HELP_CMD_PARAM,
                                 lambda **argV: usageCommand(mainMenu=mainMenu, **argV )),

        "Quit"                   : MenuCtrl.MENU_SEPATOR_TUPLE,
        MenuCtrl.MENU_QUIT       : MenuCtrl.MENU_QUIT_TUPLE,

        # Hidden commands
        MenuCtrl.MENU_VERSION    : ( "Output version number", None, version ),
    }

    menuController.setMenu( menu = mainMenu, defaults = defaults)

    # Interactive use starts REPL-loop
    if runMenu: menuController.mainMenu()

    # menuController.close() call after returning from run()
    return menuController
