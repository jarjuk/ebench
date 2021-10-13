#!/usr/bin/env python3


from .Unit import UnitSignalGenerator
from .ebench import MenuCtrl
from .ebench import usage, usageCommand, menuStartRecording, menuStopRecording, menuScreenShot
from .ebench import list_resources, MenuValueError

# Installing this module as command
from .CMDS import CMD_UNIT
CMD=CMD_UNIT

from absl import logging


SYNOPSIS="Tool to control UNIT-T UTG962/932 Waveform generator"



class UTG962(UnitSignalGenerator):

    def __init__( self, ip=None, addr=None, debug = False ):
        logging.info( "UTG962: ip={},  addr={}".format(ip, addr))
        super().__init__(ip=ip, addr=addr, debug=debug)
    

    # API ---> 
    def reset(self):
        """Reset UTG962/932 device. This commans also closes both signal
        generation channels.

        UTG962/932 device channel status cannot accessed
        programmatically.  Therefore this tool tries to model state of
        the device as digital twin using following commands:
        - reset: closes channel 1&&2 and and set digital twin state of
          both channels offset
        - on(ch): opens channel ch and set digital twin state ON
        - off(ch) : closes channel ch and updates digital twin state
          OFF

        The task of running 'reset' command is left for used, and it
        is advisable to start session with reset command, particularyq, if 
        command on/off do not change system state correctly.

        """
        # Known state
        # self.ch = [ False, False ]
        self.resetTwinState()
        self.pyvisaReset()
        self.llOpen()

    def validateCh(self,channel):
        channel = int(channel) if channel else 0
        if channel < 1 or channel > 2: raise MenuValueError("Invalid channel {} - expect 1 or 2".format(channel))
        return channel

    def on(self,channel, keyWave=True):
        """Opens 'channel' on UTG962/932 device.
        
        :keyWave: When called generate or from arb function we are
        already configuing wave and should no call it twice.

        """
        channel = self.validateCh(channel)
        logging.debug( "on: self.ch={}".format(self.ch))
        self.ilChooseChannel( channel )
        if keyWave: self.llWave()
        if not self.ch[channel-1]:
            self.llCh(channel)
            # self.ch[channel-1] = True
            self.setTwistate(channel,True)
        self.delay()
        self.llOpen()

    def tst( self, channel ):
        self.delay(10)
        self.ilChooseChannel(channel)
        self.llWave()
        wave = "arb"
        self.ilWave1(wave)
        self.llOpen()
        # self.ilArbModeReset(channel)
        # self.ilFileLocation("Internal")
        # waveFile = "AttALT"
        # self.ilArbInternal( waveFile )
        self.llOpen()
        
    def off(self,channel):
        """Closes 'channel' on UTG962/932 device.
        Open lock on device
        """
        channel = self.validateCh(channel)
        logging.debug( "off: self.ch={}".format(self.ch))
        self.ilChooseChannel( channel )
        if self.ch[channel-1]:
            self.llCh(channel)
            # self.ch[channel-1] = False
            self.setTwistate(channel,False)
        self.llOpen()
        self.delay()


    def generate( self, channel=1, wave="sine", freq=None, amp=None,  offset=None, phase=None, duty=None, raised=None, fall=None, symmetry=None ):
        """sine, square, pulse, ramp generation
        """
        # Deactivate
        # self.off(channel)
        # Start config
        logging.info( "generate: channel={}, wave={}, freq={}".format(channel, wave, freq))
        self.ilChooseChannel( channel )
        # At this point correct channel selected
        self.llWave()
        self.ilWave1(wave)
        # Frequencey (sine, square, pulse,arb)
        if freq is not None and not not freq:
            # Without down would toggle Periosd
            self.llDown()
            self.ilWave1Props( "Freq")
            self.ilFreq( *self.instrumentValUnit( freq ) )
        # Amplification (sine, square, pulse, arb)
        if amp is not None and not not amp:
            logging.info( "amp value:'{}'".format(amp))
            self.ilWave1Props( "Amp")
            self.ilAmp( *self.instrumentValUnit( amp ) )
        # Offset (sine, square, pulse)
        if offset is not None and not not offset:
            self.ilWave1Props( "Offset")
            self.ilOffset( *self.instrumentValUnit(offset))
        # Phase (sine, square, pulse)
        if phase is not None and not not phase:
            self.ilWave1Props( "Phase")
            self.ilPhase( *self.instrumentValUnit( phase ))
        # Duty (square, pulse)
        if duty is not None and not not duty:
            self.ilWave1Props( "Duty")
            self.ilDuty( *self.instrumentValUnit( duty ))
        # Ramp (only)
        if symmetry is not None and not not symmetry:
            self.ilSymmetryProps( "Symmetry")
            self.ilDuty( *self.instrumentValUnit(symmetry))
        # Raise (pulse)
        if raised is not None and not not raised:
            self.ilWave1Props( "Page Down")
            self.llDown()
            self.ilWave2Props( "Raise")
            # Expecting immediatelly raised value
            self.ilRaiseFall( *self.instrumentValUnit( raised ))
            self.ilWave2Props( "Page Up")
        # Fall (pulse)
        if fall is not None and not not fall:
            self.ilWave1Props( "Page Down")
            # Switch to fall section
            self.ilWave2Props( "Fall")
            self.ilRaiseFall( *self.instrumentValUnit( fall ))
            self.ilWave2Props( "Page Up")
        # # Activate
        # ebUnit sine (=any waveform generate) should not toggle output
        # self.delay(2)
        # self.on(channel, keyWave=False)

    def sine( self, **argv ):
        """Generate sine wave on 'channel' """
        self.generate( wave="sine", **argv)
    def square( self, **argv ):
        """Generate square wave on 'channel' """
        self.generate( wave="square", **argv)
    def pulse( self, **argv ):
        """Generate pulse wave on 'channel' 
        """
        self.generate( wave="pulse", **argv)
    def ramp( self, **argv ):
        """Generate ramp wave on 'channel' 
        """
        self.generate( wave="ramp", **argv)
        
    def arb( self, channel=1, wave="arb", waveFile="AbsSine",
             freq=None, amp=None, offset=None, phase=None ):
        """Generate abitrary wave on 'channel'
        
        :wave:     Fixed value arbGenerate
        
        :freq:     Signal frequency, units [uHz|mHz|Hz|kHz|MHz].
                   Examples 1.6kHz, 0.1mHz

        :amp:      Signal amplitude, units [mVpp|Vpp|mVrms|Vrms]
                   Examples 500mV, 0.5V

        :offset:   Signal offset, units [mV|V]
                   Example -100mV

        :phase:    Signal phase, units [deg]
                   Example 90deg

        :waveFile: one of AbsSine, AmpALT, AttALT, Cardiac, CosH, EEG,
                   EOG, GaussianMonopulse,GaussPulse, LogNormal,
                   Lorenz, Pulseilogram, Radar, Sinc, SineVer,
                   StairUD, StepResp,Trapezia, TV, Voice, Log_up,
                   Log_down, Tri_up, Tri_down

                   or path bsv file to upload

        """
        # Deactivate
        # self.off(channel)
        # # Start config
        logging.info( "wave={}, freq={}, waveFile={}".format(wave, freq, waveFile))
        self.ilChooseChannel( channel )
        # At this point correct channel selected
        self.llWave()
        self.ilWave1(wave)

        # WaveFile -> Internal --> WaveFile --> OK
        self.ilArbModeReset(channel)
        # self.delay(2)
        # Assume in Wave.Arb.WaveFile (w. reset)
        if self.ilIsInternalArbName(waveFile):
            # internal 'waveFile' - activate it 
            self.ilFileLocation("Internal")
            self.ilArbInternal( waveFile )
        else:
            self.ilArbModeReset(channel)
            # upload exteral first slot [1] 
            self.ilWriteFile( waveFile, channel=channel )
            self.ilFileLocation("External")
        self.delay(2)
        self.llF(5)  # ok
        self.delay(2)

        # self.ilWriteFile( filePath = filePath )
        
        # Frequencey (sine, square, pulse,arb)
        if freq is not None and not not freq:
            self.ilWaveArbProps( "Freq")
            self.ilFreq( *self.instrumentValUnit( freq ) )
        # Amplification (sine, square, pulse, arb)
        if amp is not None and not not amp:
            logging.info( "amp value:'{}'".format(amp))
            self.ilWaveArbProps( "Amp")
            self.ilAmp( *self.instrumentValUnit( amp ) )
        # Offset (sine, square, pulse)
        if offset is not None and not not offset:
            self.ilWaveArbProps( "Offset")
            self.ilOffset( *self.instrumentValUnit(offset))
        # Phase (sine, square, pulse)
        if phase is not None and not not phase:
            self.ilWaveArbProps( "Phase")
            self.ilPhase( *self.instrumentValUnit( phase ))
        # Activate
        self.delay(2)
        # self.llOpen()
        # arb needs this - not sure why :(
        # self.llWave()
        # self.ilWave1(wave)
        # self.delay(2)
        # No need to choose because have already done 'ilChooseChannel'
        self.on(channel, keyWave=False )


    def close(self):
        # self.llOpen()
        # Wait for a while before closing connection
        # self.delay(10)        
        super().close()
   


# ------------------------------------------------------------------
# Menu: command and parameters

# helpProps = {
#     "command" : "show help for command",
# }

onOffProps  = {
    'channel'    :   "Channel 1,2 to operate upon",    
}

# screenCapturePar  = {
#     'fileName'   :   "Screen capture file name (optional)",    
# }

# stopRecordingPar = {
#     "fileName" : "Filename to store recording, '.' show current playback list",
# }

sinePar = onOffProps | {
    'freq'  :   "Frequency [uHz|mHz|Hz|kHz|MHz]",
    'amp'   :    "Amplitude [mVpp|Vpp|mVrms|Vrms]",
    'offset': "Offset [mV|V]",
    'phase' :  "Phase [deg]",
}
        
arbProps = sinePar | {
    'waveFile'  :   "Name of waveform file",
}
        
squarePar = sinePar | {
    'duty'  :   "Duty [%]",
}
        
pulsePar = squarePar | {
    'raised':   "Raise [ns,us,ms,s,ks]",
    'fall'  :     "Fall [ns,us,ms,s,ks]",
}

rampPar = sinePar | {
    'symmetry'  :   "Symmetry [%]",
}

defaults = {
}



# ------------------------------------------------------------------
#  menu documentation (=help system)

usageText = f"""
More help:
  {CMD} --help                          : to list options
  {CMD} ? command=<command>             : to get help on command <command> parameters

Examples:
  {CMD} ? command=sine                  : help on sine command parameters
  {CMD} list_resources                  : Identify --addr option parameter
  {CMD} --addr 'USB0::1::2::3::0::INSTR': Run interactively on device found in --addr 'USB0::1::2::3::0::INSTR'
  {CMD} --captureDir=pics screen        : Take screenshot to pics directory (form device in default --addr)
  {CMD} reset                           : Send reset to UTH900 waveform generator
  {CMD} sine channel=2 freq=2kHz        : Generate 2 kHz sine signal on channel 2
  {CMD} sine channel=1 square channel=2 : chaining sine generation on channel 1, and square generation on channel 2

Hint:
  Run reset to synchronize {CMD} -tool with device state. Ref= ?? command=reset
  One-liner in linux: {CMD} --addr $({CMD} list_resources)

"""

# ------------------------------------------------------------------
# Main

def run( _argv, runMenu:bool =True, addr=None, ip=None,captureDir=None, recordingDir=None, outputTemplate=None ):
    """Construct UTG962 -instrument and wrap it to MenuCtrl object. Call
     MenuCtrl.mainMenu if 'runMenu' True (default).

    :outputTemplate: CLI configuration, None(default): =execute
    cmds/args, not None: map menu actions to strings using
    'outputTemplate',

    :runMenu: call MenuCtrl.mainMenu if True, default True

    :return: MenuCtrl (wrapping MSO1104 instrument )

    """
    logging.info( "starting")

    sgen = UTG962( addr=addr, ip=ip)
    
    menuController = MenuCtrl( args=_argv
                               , instrument=sgen, prompt = "[q=quit,?=commands,??=help on command]"
                               , outputTemplate = outputTemplate  )

    
    mainMenu = {
        "sine"                   : ( "Generate sine -wave on channel 1|2", sinePar, sgen.sine ),
        "square"                 : ( "Generate square -wave on channel 1|2", squarePar, sgen.square  ),
        "pulse"                  : ( "Generate pulse -wave on channel 1|2", pulsePar, sgen.pulse ),
        "ramp"                   : ( "Generate ramp -wave on channel 1|2", rampPar, sgen.ramp ),        
        "arb"                    : ( "Upload wave file and use it to generate wave on channel 1|2", arbProps, sgen.arb),
        "on"                     : ( "Switch on channel 1|2", onOffProps, sgen.on ),
        "_tst"                   : ( "Switch on channel 1|2", onOffProps, sgen.tst ),
        "off"                    : ( "Switch off channel 1|2", onOffProps, sgen.off),
        "reset"                  : ( "Send reset to UTG900 signal generator", None, sgen.reset),
        "Record"                 : MenuCtrl.MENU_SEPATOR_TUPLE,
        MenuCtrl.MENU_REC_START  : ( "Start recording", None, menuStartRecording(menuController) ),
        MenuCtrl.MENU_REC_SAVE   : ( "Stop recording", MenuCtrl.MENU_REC_SAVE_PARAM,
                                     menuStopRecording(menuController, recordingDir=recordingDir) ),
        MenuCtrl.MENU_SCREEN     : ( "Take screenshot", MenuCtrl.MENU_SCREENSHOT_PARAM,
                                     menuScreenShot(instrument=sgen,captureDir=captureDir,prefix="UTG-" )),
        "list_resources"         : ( "List pyvisa resources (=pyvisa list_resources() wrapper)'", None, list_resources ),
        # "Misc"                   : MenuCtrl.MENU_SEPATOR_TUPLE,
        "Help"                   : MenuCtrl.MENU_SEPATOR_TUPLE,
        MenuCtrl.MENU_QUIT       : MenuCtrl.MENU_QUIT_TUPLE,
        MenuCtrl.MENU_HELP       : ( "List commands", None,
                                    lambda **argV: usage(cmd=CMD, mainMenu=mainMenu, synopsis=SYNOPSIS, usageText=usageText )),
        MenuCtrl.MENU_HELP_CMD   : ( "List command parameters", MenuCtrl.MENU_HELP_CMD_PARAM,
                                  lambda **argV: usageCommand(mainMenu=mainMenu, **argV )),

        MenuCtrl.MENU_VERSION    : MenuCtrl.MENU_VERSION_TUPLE,
    }

    menuController.setMenu( menu = mainMenu, defaults = defaults)
    
    if runMenu:  menuController.mainMenu()

    return menuController
        

