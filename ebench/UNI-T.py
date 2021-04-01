#!/usr/bin/env python3

import os
import sys
from absl import app, flags, logging
from absl.flags import FLAGS

import pyvisa
from time import sleep

from ebench import version, Instrument, Cmd, subMenuHelp, mainMenuHelpCommon, usage, menuStartRecording, menuStopRecording, menuScreenShot, list_resources, MenuValueError

ADDR= "USB0::0x6656::0x0834::1485061822::INSTR"
flags.DEFINE_string('ip', None, "IP address of pyvisa instrument")
flags.DEFINE_string('addr', ADDR, "UTG900 pyvisa resource address")
flags.DEFINE_string('captureDir', "pics", "Capture directory")
flags.DEFINE_string('recordingDir', "tmp", "Directory where recordings are saved into")


CMD="UTG900.py"

class SignalGenerator(Instrument):
    def __init__( self, addr, debug = False ):
             super().__init__( debug=debug)
             self.addr = addr
             try:
                      self.instrument = Instrument.singleton_rm().open_resource(self.addr)

             except pyvisa.errors.VisaIOError as err:
                      self.instrument = None
                      logging.error(err)

             except ValueError as err:
                      self.instrument = None
                      logging.error(err)

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

    def read_raw(self):
        raw = self.instrument.read_raw()
        logging.info( "read_raw return getsizeof(raw) {} bytes".format(sys.getsizeof(raw)))
        return raw

    def query(self, cmd, strip=False ):
        logging.info( "query: {}".format(cmd))
        ret = self.instrument.query(cmd)
        if strip: ret = ret.rstrip()
        return( ret )


class UTG962(SignalGenerator):
    """Unit-T UTG900 signal generator PYVISA control wrapper.

    Maintains digital twin of physical device in self.ch variable.
    - reset: closes channel 1&&2 and digital twin state self.ch
    - on(ch): opens channel and updates digital twin state self.ch
    - on(ch): closes channel and updates digital twin state self.ch


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
       # Need to know state of device --> reset, Here make the bold assumption
       self.ch = [False,False]
       # self.reset()


    def ilScreenShot( self, filePath="tmp/apu.jpg"):
        fileDir = os.path.dirname(filePath )
        filePathDib = os.path.join(fileDir, "__UTG-capture__.bmp" )
        logging.info( "ilScreenShot: fileDir={}, filePathDib={} -> filePath={}".format(fileDir, filePathDib, filePath) )
        # Query binary screenshot
        sShot = self.llSShot()
        with open( filePathDib, "wb") as f:
             f.write( sShot)
        # Need to flip it over && convert to ext
        self.dibToImage( filePathDib, filePath )


    # LL (low level language =keypress)
    def llSShot(self):
      self.write( "Display:Data?")
      self.delay()
      data = self.read_raw()
      # Skip header stuff
      return data[15:]
    def llReset(self):
      self.write( "*RST" )
    def llLock(self):
      self.write( "System:LOCK on")
    def llOpen(self):
      self.write( "System:LOCK off")
    def llCh(self, ch):
      self.write( "KEY:CH{}".format(ch))
    def llData(self,*args, **kwargs):
      return self.query_binary_values( "Display:Data?", *args, **kwargs )
    def llWave(self):
      self.write( "KEY:Wave")
    def llUtility(self):
      self.write( "KEY:Utility")
    def llKey(self, keyStr):
      self.write( "KEY:{}".format(keyStr))
    def llMode(self):
      self.write( "KEY:Mode")
    def llF(self, digit ):
      self.write( "KEY:F{}".format(digit))
    def llUp(self):
      self.llKey("Up")
    def llDown(self):
      self.llKey("Down")
    def llLeft(self):
      self.llKey("Left")
    def llRight(self):
      self.llKey("Right")
    def llNum(self, numStr):
      def ch2cmd( ch ):
          chMap = {
              "0": "NUM0",
              "1": "NUM1",
              "2": "NUM2",
              "3": "NUM3",
              "4": "NUM4",
              "5": "NUM5",
              "6": "NUM6",
              "7": "NUM7",
              "8": "NUM8",
              "9": "NUM9",
              "-": "SYMBOL",
              ".": "DOT",
              ",": "DOT",
          }
          try:
             keyName = chMap[ch]
             return  keyName
          except KeyError:
                logging.fatal( "Could not extract keyName for ch {} numStr {}".format( ch, numStr ))
                raise 
      for ch in str(numStr):
         self.write( "KEY:{}".format(ch2cmd(ch)))
    def llFKey( self, val, keyMap):
        try:
           self.llF(keyMap[val])
        except KeyError as err:
           logging.error( "Invalid key: '{}', valid keys one of {}".format( val, list(keyMap.keys())))
           logging.error( str(err) )
           raise MenuValueError(str(err))

    # IL intermediate (=action in a given mode)
    def ilFreq( self, freq, unit ):
        self.llNum( str(freq))
        self.ilFreqUnit( unit )
    def ilAmp( self, amp, unit ):
        self.llNum( str(amp))
        self.ilAmpUnit( unit )
    def ilOffset( self, offset, unit ):
        self.llNum( str(offset))
        self.ilOffsetUnit( unit )
    def ilPhase( self, freq, unit ):
        self.llNum( str(freq))
        self.ilPhaseUnit( unit )
    def ilDuty( self, duty, unit ):
        self.llNum( str(duty))
        self.ilDutyUnit(unit)
    def ilRaiseFall( self, raiseFall, unit ):
        self.llNum( str(raiseFall))
        self.ilRaiseFallUnit(unit)
    def ilWriteFile( self, filePath):
        """Expect to be in Arb/WaveFile waitin for file loaction &&
        updaload"""
        self.ilFileLocation( "External")
        with open( filePath) as fh:
            lines = fh.readlines()
            for line in lines:
                self.write( line )
    def ilConf( self, wave ):
        waveMap  = {
           "Freq":   "1",
           "Amp":    "2",
           "Offset": "3",
           "Phase":  "4",
        }
        self.llFKey( val=wave, keyMap = waveMap )

    def ilWave1( self, wave ):
        """Selec wave type"""
        waveMap  = {
           "sine": "1",
           "square": "2",
           "pulse":  "3",
           "ramp": "4",
           "arb": "5",
           "MHz": "6",
        }
        self.llFKey( val=wave, keyMap = waveMap )

    def ilWave1Props( self, wave ):
        """Wave properties, page1"""
        waveMap  = {
           "Freq": "1",
           "Amp": "2",
           "Offset":  "3",
           "Phase": "4",
           "Duty": "5",
           "Page Down": "6",
        }
        self.llFKey( val=wave, keyMap = waveMap )

    def ilWaveArbProps( self, wave ):
        """Arb Wave properties"""
        waveMap  = {
           "WaveFile": "1",
           "Freq": "2",
           "Amp": "3",
           "Offset":  "4",
           "Phase": "5",
        }
        self.llFKey( val=wave, keyMap = waveMap )

    def ilWave2Props( self, wave ):
        """Wave properties, page2"""
        waveMap  = {
           "Raise": "1",
           "Fall": "2",
           "Page Up": "6",
        }
        self.llFKey( val=wave, keyMap = waveMap )

    # Units
    def ilChooseChannel( self, ch ):
        """Key sequence to to bring UTG962 to display to a known state. 

        Here, invoke Utility option, use function key F1 or F2 to
        choose channel. Do it twice (and visit Wave menu in between)

        """
        ch = int(ch)
        self.llUtility()
        self.ilUtilityCh( ch )
        self.llWave()
        self.llUtility()
        self.ilUtilityCh( ch )
        self.llWave()
        self.delay()
    def ilFreqUnit( self, unit ):
        freqUnit  = {
           "uHz": "1",
           "mHz": "2",
           "Hz":  "3",
           "kHz": "4",
           "MHz": "5",
        }
        self.llFKey( val=unit, keyMap = freqUnit )
    def ilAmpUnit( self, unit ):
        ampUnit  = {
           "mVpp": "1",
           "Vpp": "2",
           "mVrms":  "3",
           "Vrms": "4",
           "Cancel": "6",
        }
        self.llFKey( val=unit, keyMap = ampUnit )
    def ilRaiseFallUnit( self, unit ):
        raiseFallUnit  = {
           "ns":  "1",
           "us":  "2",
           "ms":  "3",
           "s":   "4",
           "ks":  "5",                 
        }
        self.llFKey( val=unit, keyMap = raiseFallUnit )
    def ilOffsetUnit( self, unit ):
        offsetUnit  = {
           "mV": "1",
           "V": "2",
        }
        self.llFKey( val=unit, keyMap = offsetUnit )
    def ilFileLocation( self, location ):
        fileLocation  = {
            "Internal": "1",
            "External": "2",
        }
        self.llFKey( val=location, keyMap=fileLocation )
    def ilArbInternal( self, waveFile):
        mapWave2DonwKey = {
            "AbsSine":0,
            "AmpALT":1,
            "AttALT":2,
            "Cardiac":3,
            "CosH":4,
            "EEG":5,
            "EOG":6,
            "GaussianMonopulse":7,
            "GaussPulse":8,
            "LogNormal":9,
            "Lorenz":10,
            "Pulseilogram":11,
            "Radar":12,
            "Sinc":13,
            "SineVer":14,
            "StairUD":15,
            "StepResp":16,
            "Trapezia":17,
            "TV":18,
            "Voice":19,
            "Log_up":20,
            "Log_down":21,
            "Tri_up":22,
            "Tri_down": 23,
        }
        try:
            for i in range(mapWave2DonwKey[waveFile]):
                self.llDown()
        except KeyError as err:
            raise MenuValueError( "Invalid waveformat name {}, valid names one of: {}".format(str(err), list(mapWave2DonwKey.keys()) ))
    def ilUtilityCh( self, ch ):
        chSelect  = {
           1: "1",
           2: "2",
        }
        self.llFKey( val=ch, keyMap = chSelect )
    def ilPhaseUnit( self, unit ):
        phaseUnit  = {
           "deg": "1",
        }
        self.llFKey( val=unit, keyMap = phaseUnit )
    def ilDutyUnit( self, unit ):
        dutyUnit  = {
           "%": "1",
        }
        self.llFKey( val=unit, keyMap = dutyUnit )

     # Utils
    def dibToImage( self, dibFilePath, resultPath ):
        cmd = "convert {} -flop {}".format( dibFilePath, resultPath  )
        logging.info( "Running '{}' to create  resultPath: {}".format( cmd, resultPath))
        os.system(cmd)
        return(resultPath)

    def otherCh( self, ch ):
        return 1 if ch == 2 else 2
    
    def delay(self, delay=1):
        delayUnit=0.2
        sleep(delay*delayUnit)


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
        self.llReset()
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

    def getName(self):
       return( self.query( "*IDN?"))

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

def mainMenuHelp(mainMenu):
    mainMenuHelpCommon( cmd=CMD, mainMenu=mainMenu, synopsis="Tool to control UNIT-T UTG900 Waveform generator")
    print( "" )
    print( "More help:")
    print( "  {} --help                          : to list options".format(CMD) )
    print( "  {} ? command=<command>             : to get help on command <command> parameters".format(CMD) )
    print( "")
    print( "Examples:")
    print( "  {} ? command=sine                  : help on sine command parameters".format(CMD))
    print( "  {} list_resources                  : Identify --addr option parameter".format(CMD))
    print( "  {} --addr 'USB0::1::2::3::0::INSTR': Run interactively on device found in --addr 'USB0::1::2::3::0::INSTR'".format(CMD))
    print( "  {} --captureDir=pics screen        : Take screenshot to pics directory (form device in default --addr)".format(CMD))
    print( "  {} reset                           : Send reset to UTH900 waveform generator".format(CMD))    
    print( "  {} sine channel=2 freq=2kHz        : Generate 2 kHz sine signal on channel 2".format(CMD))
    print( "  {} sine channel=1 square channel=2 : chaining sine generation on channel 1, and square generation on channel 2".format(CMD))
    
    print( "")
    print( "Hint:")
    print( "  Run reset to synchronize {} -tool with device state. Ref= ?? command=reset".format(CMD))
    print( "  One-liner in linux: {} --addr $({} list_resources)".format(CMD, CMD))

# ------------------------------------------------------------------
# Main

def main( _argv ):
    logging.set_verbosity(FLAGS.debug)
    logging.info( "starting")

    sgen = UTG962( addr=FLAGS.addr, ip=FLAGS.ip)
    cmdController = Cmd()

    mainMenu = {
        "sine"              : ( "Generate sine -wave on channel 1|2", sinePar, sgen.sine ),
        "square"            : ( "Generate square -wave on channel 1|2", squarePar, sgen.square  ),
        "pulse"             : ( "Generate pulse -wave on channel 1|2", pulsePar, sgen.pulse ),
        "arb"               : ( "Upload wave file and use it to generate wave on channel 1|2", arbProps, sgen.arb),
        "on"                : ( "Switch on channel 1|2", onOffProps, sgen.on ),
        "off"               : ( "Switch off channel 1|2", onOffProps, sgen.off),
        "reset"             : ( "Send reset to UTG900 signal generator", None, sgen.reset),
        "Record"            : (None, None, None),
        Cmd.MENU_REC_START  : ( "Start recording", None, menuStartRecording(cmdController) ),
        Cmd.MENU_REC_SAVE   : ( "Stop recording", stopRecordingPar, menuStopRecording(cmdController, pgm=_argv[0], fileDir=FLAGS.recordingDir) ),
        Cmd.MENU_SCREEN     : ( "Take screenshot", screenCapturePar, menuScreenShot(instrument=sgen,captureDir=FLAGS.captureDir,prefix="UTG-" )),
        "list_resources"    : ( "List pyvisa resources (=pyvisa list_resources() wrapper)'", None, list_resources ),
        "Misc"              : (None, None, None),        
        Cmd.MENU_VERSION    : ( "Output version number", None, version ),
        "Help"              : (None, None, None),                
        Cmd.MENU_QUIT       : ( "Exit", None, None),
        Cmd.MENU_HELP       : ( "List commands", None,
                             lambda **argV: usage(mainMenu=mainMenu, mainMenuHelp=mainMenuHelp, subMenuHelp=subMenuHelp, **argV )),
        Cmd.MENU_CMD_PARAM  : ( "List command parameters", helpPar,
                             lambda **argV: usage(mainMenu=mainMenu, mainMenuHelp=mainMenuHelp, subMenuHelp=subMenuHelp, **argV )),

    }


    cmdController.mainMenu(_argv, mainMenu=mainMenu, mainPrompt="[q=quit,?=commands,??=help on command]")
    if sgen is not None:
        sgen.close()
        sgen = None


if __name__ == '__main__':
    try:
        app.run(main)
    except SystemExit:
        pass
    

