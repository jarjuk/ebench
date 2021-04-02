
from ebench import SignalGenerator, MenuValueError

import os
from absl import logging

from time import sleep



# Name of command line tool


class UnitSignalGenerator(SignalGenerator):
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
       super().__init__(addr=addr, debug=debug)
       self.ip = ip
       try:
          idn = self.instrument.query('*IDN?')
          logging.warning("Successfully connected  '{}' with '{}'".format(addr, idn))
       except:
          pass
       # Need to know state of device --> reset, Here make the bold assumption
       self.ch = [False,False]
       # self.reset()

    # ------------------------------------------------------------------
    # Template methods (used in base classes)

    def screenShotImplementation( self, filePath):
        """Screenshot implementation

        :return: filePath in success, None in error
        """
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
    # def llReset(self):
    #   self.write( "*RST" )
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


