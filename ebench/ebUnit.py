#!/usr/bin/env python3


from .Unit import UnitSignalGenerator
from .ebench import version, MenuCtrl, subMenuHelp
from .ebench import usage, usageCommand, menuStartRecording, menuStopRecording, menuScreenShot
from .ebench import list_resources, MenuValueError

# Installing this module as command
from .CMDS import CMD_UNIT
CMD=CMD_UNIT

from absl import app, logging
from absl.flags import FLAGS

ADDR= "USB0::0x6656::0x0834::1485061822::INSTR"

class UTG962(UnitSignalGenerator):

    def __init__( self, ip=None, addr=None, debug = False ):
        logging.info( "UTG962: ip={},  addr={}".format(ip, addr))
        super().__init__( ip=ip, addr=addr, debug=debug)
    

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
        self.ch = [ False, False ]
        self.pyvisaReset()
        self.llOpen()

    def validateCh(self,channel):
        channel = int(channel) if channel else 0
        if channel < 1 or channel > 2: raise MenuValueError("Invalid channel {} - expect 1 or 2".format(channel))
        return channel

    def on(self,channel):
        """Opens 'channel' on UTG962/932 device.
        """
        channel = self.validateCh(channel)
        if self.ch[channel-1]: return;
        self.ilChooseChannel( channel )
        self.llCh(channel)
        self.ch[channel-1] = True
        self.llOpen()
        self.delay()

    def off(self,channel):
        """Closes 'channel' on UTG962/932 device.
        """
        channel = self.validateCh(channel)
        if not self.ch[channel-1]: return;
        self.ilChooseChannel( channel )
        self.llCh(channel)
        self.ch[channel-1] = False
        self.llOpen()
        self.delay()


    def generate( self, channel=1, wave="sine", freq=None, amp=None,  offset=None, phase=None, duty=None, raised=None, fall=None ):
        """sine, square, pulse generation
        """
        # Deactivate
        self.off(channel)
        # Start config
        self.ilChooseChannel( channel )
        # At this point correct channel selected
        self.ilWave1( wave )
        # Frequencey (sine, square, pulse,arb)
        if freq is not None and not not freq:
            # Without down would toggle Periosd
            self.llDown()
            self.ilWave1Props( "Freq")
            self.ilFreq( *self.valUnit( freq ) )
        # Amplification (sine, square, pulse, arb)
        if amp is not None and not not amp:
            logging.info( "amp value:'{}'".format(amp))
            self.ilWave1Props( "Amp")
            self.ilAmp( *self.valUnit( amp ) )
        # Offset (sine, square, pulse)
        if offset is not None and not not offset:
            self.ilWave1Props( "Offset")
            self.ilOffset( *self.valUnit(offset))
        # Phase (sine, square, pulse)
        if phase is not None and not not phase:
            self.ilWave1Props( "Phase")
            self.ilPhase( *self.valUnit( phase ))
        # Duty (square, pulse)
        if duty is not None and not not duty:
            self.ilWave1Props( "Duty")
            self.ilDuty( *self.valUnit( duty ))
        # Raise (pulse)
        if raised is not None and not not raised:
            self.ilWave1Props( "Page Down")
            self.llDown()
            self.ilWave2Props( "Raise")
            # Expecting immediatelly raised value
            self.ilRaiseFall( *self.valUnit( raised ))
            self.ilWave2Props( "Page Up")
        # Fall (pulse)
        if fall is not None and not not fall:
            self.ilWave1Props( "Page Down")
            # Switch to fall section
            self.ilWave2Props( "Fall")
            self.ilRaiseFall( *self.valUnit( fall ))
            self.ilWave2Props( "Page Up")
        # Activate
        self.on(channel)

    def sine( self, **argv ):
        """Generate sine wave on 'channel' """
        self.generate( wave="sine", **argv)
    def square( self, **argv ):
        """Generate square wave on 'channel' """
        self.generate( wave="sine", **argv)
    def pulse( self, **argv ):
        """Generate pulse wave on 'channel' 
        """
        self.generate( wave="sine", **argv)
        
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

        """
        # Deactivate
        self.off(channel)
        # Start config
        self.ilChooseChannel( channel )
        # Choose arb
        self.ilWave1( wave )

        # WaveFile -> Internal --> WaveFile --> OK
        self.llDown()
        self.delay()
        self.ilWaveArbProps("WaveFile")
        self.delay()
        self.ilFileLocation("Internal")
        self.ilArbInternal( waveFile )
        self.delay(2)
        self.llF(5)  # ok

        # self.ilWriteFile( filePath = filePath )
        
        # Frequencey (sine, square, pulse,arb)
        if freq is not None and not not freq:
            self.ilWaveArbProps( "Freq")
            self.ilFreq( *self.valUnit( freq ) )
            self.llDown()
        # Amplification (sine, square, pulse, arb)
        if amp is not None and not not amp:
            logging.info( "amp value:'{}'".format(amp))
            self.ilWaveArbProps( "Amp")
            self.ilAmp( *self.valUnit( amp ) )
        # Offset (sine, square, pulse)
        if offset is not None and not not offset:
            self.ilWaveArbProps( "Offset")
            self.ilOffset( *self.valUnit(offset))
        # Phase (sine, square, pulse)
        if phase is not None and not not phase:
            self.ilWaveArbProps( "Phase")
            self.ilPhase( *self.valUnit( phase ))
        # Activate
        self.on(channel)


    def close(self):
        self.llOpen()
        super().close()
   


# ------------------------------------------------------------------
# Menu: command and parameters

# helpProps = {
#     "command" : "show help for command",
# }

onOffProps  = {
    'channel'    :   "Channel 1,2 to operate upon",    
}

screenCapturePar  = {
    'fileName'   :   "Screen capture file name (optional)",    
}

stopRecordingPar = {
    "fileName" : "Filename to store recording, '.' show current playback list",
}

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

helpPar = {
      "command": "Command to give help on (None: help on main menu)"
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

def run( _argv, parentMenu:MenuCtrl=None ):
    logging.info( "starting")

    sgen = UTG962( addr=FLAGS.addr, ip=FLAGS.ip)
    cmdController = MenuCtrl( args=_argv, instrument=sgen, parentMenu=parentMenu
                              , prompt = "[q=quit,?=commands,??=help on command]")

    mainMenu = {
        "sine"                   : ( "Generate sine -wave on channel 1|2", sinePar, sgen.sine ),
        "square"                 : ( "Generate square -wave on channel 1|2", squarePar, sgen.square  ),
        "pulse"                  : ( "Generate pulse -wave on channel 1|2", pulsePar, sgen.pulse ),
        "arb"                    : ( "Upload wave file and use it to generate wave on channel 1|2", arbProps, sgen.arb),
        "on"                     : ( "Switch on channel 1|2", onOffProps, sgen.on ),
        "off"                    : ( "Switch off channel 1|2", onOffProps, sgen.off),
        "reset"                  : ( "Send reset to UTG900 signal generator", None, sgen.reset),
        "Record"                 : (None, None, None),
        MenuCtrl.MENU_REC_START  : ( "Start recording", None, menuStartRecording(cmdController) ),
        MenuCtrl.MENU_REC_SAVE   : ( "Stop recording", stopRecordingPar,
                                     menuStopRecording(cmdController, pgm=_argv[0], fileDir=FLAGS.recordingDir) ),
        MenuCtrl.MENU_SCREEN     : ( "Take screenshot", screenCapturePar,
                                     menuScreenShot(instrument=sgen,captureDir=FLAGS.captureDir,prefix="UTG-" )),
        "list_resources"         : ( "List pyvisa resources (=pyvisa list_resources() wrapper)'", None, list_resources ),
        "Misc"                   : (None, None, None),        
        MenuCtrl.MENU_VERSION    : ( "Output version number", None, version ),
        "Help"                   : (None, None, None),                
        MenuCtrl.MENU_QUIT       : ( "Exit", None, None),
        MenuCtrl.MENU_HELP       : ( "List commands", None,
                                    lambda **argV: usage(cmd=CMD, mainMenu=mainMenu, usageText=usageText )),
        MenuCtrl.MENU_CMD_PARAM  : ( "List command parameters", helpPar,
                                  lambda **argV: usageCommand(mainMenu=mainMenu, **argV )),

    }


    cmdController.mainMenu( mainMenu=mainMenu )
    if cmdController.isTopMenu:
        # Top level closes instruments && cleanup
        cmdController.close()
        cmdController = None

    return cmdController
        

def _main( _argv ):
    logging.set_verbosity(FLAGS.debug)
    run( _argv )


def main():
    try:
        app.run(_main)
    except SystemExit:
        pass
    
    
if __name__ == '__main__':
    main()
    


