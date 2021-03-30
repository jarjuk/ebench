#!/usr/bin/env python3

import os
from datetime import datetime
from absl import app, flags, logging
from absl.flags import FLAGS

import pyvisa
import re
from time import sleep

from ebench import version, Ebench, Cmd


ADDR= "USB0::0x6656::0x0834::1485061822::INSTR"
# flags.DEFINE_integer('debug', -1, '-3=fatal, -1=warning, 0=info, 1=debug')
flags.DEFINE_string('addr', ADDR, "UTG900 pyvisa resource address")
flags.DEFINE_string('captureDir', "pics", "Capture directory")

CMD="UTG900.py"


class UTG962(Ebench):
         """
         Unit-T UTG900 signal generator PYVISA control wrapper.
         """

         # Construct && close
         def __init__( self, addr=ADDR,  debug = False ):
            super().__init__( debug=debug)
            # self.sgen = UTG962._rm.open_resource(addr)
            self.sgen = singleton_rm().open_resource(addr)
            if self.debug:
                 pyvisa.log_to_screen()
            try:
                self.idn = self.sgen.query('*IDN?')
                logging.warning("Successfully connected  '{}' with '{}'".format(addr, self.idn))
            except:
                pass
            self.reset()

         def close(self ):
             __super__.close()
             try:
                 logging.info(  "Closing sgen {}".format(self.sgen))
                 self.sgen.close()
             except:
                 logging.warning(  "Closing sgen {} - failed".format(self.sgen))                 
                 pass


         # Low level commuincation 
         def write(self, cmd ):
              self.sgen.write(cmd)
         def read_raw(self):
              return self.sgen.read_raw()
         def query(self, cmd, strip=False ):
              ret = self.sgen.query(cmd)
              if strip: ret = ret.rstrip()
              return( ret )

         # LL (low level language =keypress)
         def llSShot(self):
           self.write( "Display:Data?")
           sleep( 0.4 )
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
           if self.debug: print( "numStr={}".format(numStr))
           for ch in str(numStr):
              if self.debug: print( "ch={}".format(ch))
              self.write( "KEY:{}".format(ch2cmd(ch)))
         def llFKey( self, val, keyMap):
             try:
                self.llF(keyMap[val])
             except KeyError as err:
                logging.error( "Invalid key: '{}', valid keys: {}".format( val, keyMap.keys()))
                logging.error( str(err) )
                raise

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
             sleep( 0.1)
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
                 # "Internal": "1",
                 "External": "2",
             }
             self.llFKey( val=location, keyMap=fileLocation )
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

         def valUnit( self, valUnitsStr ):
                match = re.search( r"(?P<value>[0-9-\.]+)(?P<unit>[a-zA-Z%]+)", valUnitsStr )
                if match is None:
                      msg = "Could not extract unit value from '{}'".format( valUnitsStr )
                      logging.error(msg)
                      raise ValueError(msg)
                return ( match.group('value'), match.group('unit') )

         # API ---> 
         def reset(self):
              # Known state
              self.ch = [ False, False ]
              self.llReset()
              self.llOpen()

         def on(self,ch):
              ch = int(ch)
              if self.ch[ch-1]: return;
              self.ilChooseChannel( ch )
              self.llCh(ch)
              self.ch[ch-1] = True
              self.llOpen()
              sleep( 0.1)

         def off(self,ch):
              ch = int(ch)
              if not self.ch[ch-1]: return;
              self.ilChooseChannel( ch )
              self.llCh(ch)
              self.ch[ch-1] = False
              self.llOpen()
              sleep( 0.1)

 
         def screenShot( self, captureDir, fileName=None, ext="png"  ):
             if fileName is None:
                 now = datetime.now()
                 fileName = "UTG-{}.{}".format( now.strftime("%Y%m%d-%H%M%S"), ext )
             filePath = os.path.join( captureDir, fileName )
             logging.info( "screenShot: filePath={}".format(filePath) )
             self.ilScreenShot( filePath = filePath)
             self.llOpen()
             return filePath

         def generate( self, ch=1, wave="sine", freq=None, amp=None,  offset=None, phase=None, duty=None, raised=None, fall=None ):
             """sine, square, pulse generation
             """
             # Deactivate
             self.off(ch)
             # Start config
             self.ilChooseChannel( ch )
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
             self.on(ch)

         def arbGenerate( self, ch=1, wave="arb", filePath="tmp/apu.csv", freq=None, amp=None,  offset=None, phase=None ):
             """Arb generation
             """
             # Deactivate
             self.off(ch)
             # Start config
             self.ilChooseChannel( ch )
             # At this point correct channel selected
             self.ilWave1( wave )
             # Upload file
             self.llDown()
             self.ilWaveArbProps( "WaveFile")
             self.ilWriteFile( filePath = filePath )
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
             self.on(ch)
             
         def getName(self):
            return( self.query( "*IDN?"))


# ------------------------------------------------------------------
# State && access state
gSgen = None

def sgen():
    global gSgen
    if gSgen is None:
        logging.info( "Opening gSgen" )
        gSgen = UTG962( addr = FLAGS.addr )
    return gSgen


# ------------------------------------------------------------------
# Menu: command and parameters

helpProps = {
    "command" : "show help for command",
}

onOffProps  = {
    'ch'    :   "Channel 1,2 to switch on/off",    
}

screenCaptureProps  = {
    'fileName'   :   "Screen capture file name (optional)",    
}

sineProps = onOffProps | {
    'freq'  :   "Frequency [uHz|mHz|Hz|kHz|MHz]",
    'amp'   :    "Amplitude [mVpp|Vpp|mVrms|Vrms]",
    'offset': "Offset [mV|V]",
    'phase' :  "Phase [deg]",
}
        
arbProps = sineProps | {
    'filePath'  :   "Path to waveform file",
}
        
squareProps = sineProps | {
    'duty'  :   "Duty [%]",
}
        
pulseProps = squareProps | {
    'raised':   "Raise [ns,us,ms,s,ks]",
    'fall'  :     "Fall [ns,us,ms,s,ks]",
}

subMenu = {
    "sine"            : sineProps,
    "square"          : squareProps,
    "pulse"           : pulseProps,
    "arb"             : arbProps,    
    "on"              : onOffProps,
    "off"             : onOffProps,
    "screen"          :  screenCaptureProps,
    "reset"           :  {},
    "list_resources"  :  {},
    "version"         :  {},
}

helpPar = {
      "command": "Command to give help on (None: help on main menu)"
}

mainMenu = {
    'q'              : ( "Exit", None, None),
    'Q'              : ( "Exit", None, None),
    '?'              : ( "Usage help", helpPar,
                         lambda menuKey, **argV: Cmd.usage( menuKey, mainMenu=mainMenu, mainMenuHelp=mainMenuHelp, subMenuHelp=subMenuHelp, **argV )),
    "sine"           : ( "Generate sine -wave on channel 1|2", sineProps, lambda menuKey, **argv: sgen().generate( wave="sine", **argv) ),
    "square"         : ( "Generate square -wave on channel 1|2", squareProps, lambda menuKey, **argv: sgen().generate( wave="square", **argv) ),
    "pulse"          : ( "Generate pulse -wave on channel 1|2", pulseProps, lambda menuKey, **argv: sgen().generate( wave="pulse", **argv) ),
    "arb"            : ( "Upload wave file and use it to generate wave on channel 1|2", arbProps, lambda menuKey, **argv: sgen().arbGenerate(wave="arb", **argv)),
    "on"             : ( "Switch on channel 1|2", onOffProps, lambda menuKey, **argv: sgen().on(**argv)),
    "off"            : ( "Switch off channel 1|2", onOffProps, lambda menuKey, **argv: sgen().off(**argv)),
    "reset"          : ( "Send reset to UTG900 signal generator", None, lambda menuKey, **argv: sgen().reset(**argv)),
    "screen"         : ( "Take screenshot to 'captureDir'", screenCaptureProps, lambda menuKey, **argv: sgen().screenShot(**argv)),
    "list_resources" : ( "List pyvisa resources (=pyvisa list_resources() wrapper)'", None, lambda menuKey: Ebench.list_resources()),
    "version"        : ( "Output version number", None, lambda x: print(version())),
}



# ------------------------------------------------------------------
#  menu documentation (=help system)

def mainMenuHelp(mainMenu):
    print( "{} - {}: Tool to control UNIT-T UTG900 Waveform generator".format(CMD, version()) )
    print( "" )
    print( "Usage: {} [options] [commands and parameters] ".format( CMD ))
    print( "" )
    print( "Commands:")
    for k,v in mainMenu.items():
        print( "%15s  : %s" % (k,v) )
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
    print( "  {} sine ch=2 freq=2kHz             : Generate 2 kHz sine signal on channel 2".format(CMD))
    print( "  {} sine ch=1 square ch=2           : chaining sine generation on channel 1, and square generation on channel 2".format(CMD))
    
    print( "")
    print( "Hint:")
    print( "  One-liner in linux: {} --addr $({} list_resources)".format(CMD, CMD))
    

def subMenuHelp( command, menuText, commandParameters ):
    print( "{} - {}".format( command, menuText))
    print( "" )
    if len(commandParameters.keys()) > 0:
       for k,v in commandParameters.items():
           print( "%10s  : %s" % (k,v) )
    else:
        print( "*No parameters*")
    print( "" )
    print( "Notice:")
    print( "- parameters MUST be given in the order listed above")
    print( "- parameters are optional and they MAY be left out")


# ------------------------------------------------------------------
# Main

def main( _argv ):
    global gSgen
    logging.set_verbosity(FLAGS.debug)
    Cmd.mainMenu( _argv, mainMenu=mainMenu)
    if gSgen is not None:
        gSgen.close()
        gSgen = None


if __name__ == '__main__':
    try:
        app.run(main)
    except SystemExit:
        pass
    

