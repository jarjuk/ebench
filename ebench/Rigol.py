from .ebench import Osciloscope

import os
from absl import logging

class RigolScope(Osciloscope):
    """
    Rigol instrument
    """

    # Construct && close
    def __init__( self, ip:None, addr=None, debug = False ):
        if addr is None:
            addr = "TCPIP0::{}::INSTR".format(ip)
        super().__init__( addr=addr, debug=debug)
        self.ip = ip

    # ------------------------------------------------------------------
    # Help texts
    MEASURE_ITEMS="""
    """
        

    # ------------------------------------------------------------------
    # Template methods (used in base classes)

        
    def screenShotImplementation( self, filePath):
        """Screenshot implementation

        :filePath: path where to save screen shot

        :return: filePath in success, None in error
        """
        cmd = "lxi  screenshot  {} --address {} >/dev/null".format( filePath, self.ip )
        logging.info( "ilScreenShot: cmd:{}".format(cmd))
        os.system(cmd)
        return filePath

    # ------------------------------------------------------------------
    # Commands we expect all rigol scopes to implement
    
    def rigolClear( self):
        self.write(":CLEAR")
        
    def rigolChannelStatMeasure( self, item, ch, statistic):
        """Send :MEASure:STAT:ITEM?  <statistic>, <item>,<chan>
        """
        cmd = ":MEASure:STAT:ITEM? {},{},{}".format(statistic, item, RigolScope.chanStr(ch))
        return( float(self.query(cmd)))

    def rigolChannelMeasure( self, item, ch):
        """
        Send ":MEASure:ITEM? {},CHAN{}".format(item, ch)
        
        :ch: Number 1,2,3,4, D0, ... D15, AC

        """
        cmd = ":MEASure:ITEM? {},{}".format(item, RigolScope.chanStr(ch))
        logging.info( "rigolChannelMeasure: cmd={}".format(cmd))
        return( float(self.query(cmd)))

    def rigolMeasurement(self, ch, item, statistic=None):
        """Single channel item (statics) measurement . 

        :ch: channel to measure

        :statistic: If 'statistic' given measure statistic item
                     (:MEASure:STATistic:ITEM) else measure item
                     (:MEASure:ITEM <item>).

                    Valid values MAXimum|MINimum|CURRent|AVERages|DEViation

        :item: VMAX, VMIN, VPP, VTOP, VBASe, VAMP, VAVG, VRMS,
               OVERshoot, MARea, MPARea, PREShoot, PERiod, FREQuency,
               RTIMe, FTIMe, PWIDth, NWIDth, PDUTy, NDUTy, TVMAX,
               TVMIN, PSLEWrate, NSLEWrate, VUPper, VMID, VLOWer,
               VARIance, PVRMS, PPULses, NPULses, PEDGes, and NEDGes

        """
        
        
        if statistic is None:
            val = self.rigolChannelMeasure( item=item, ch=ch)
        else:
            val = self.rigolChannelStatMeasure( item=item, ch=ch, statistic=statistic )

        if val > 10**12:
            # Ridiculous values discard, e.g.g FREQ
            val = None
        return( val )

    def chanStr( ch ):
        if ch in [1,2,3,4,"1","2","3","4"]:
            chStr = "CHAN{}".format(ch)
        else:
            chStr = ch
        return chStr


    def rigolChannelMeasurementStat( self, item, ch ):
        cmd = ":MEAS:STAT:ITEM {},{}".format( item, RigolScope.chanStr(ch))
        self.write( cmd )
        
    def rigolChannelOnOff( self, ch, onOff:None):
        """Switch channel 'ch' 'onOff'

        :channel: 1,2,3,4,MATH
        """
        cmd = ":{}:DISP {}".format(RigolScope.chanStr(ch),"ON" if onOff else "OFF" )
        return  self.write(cmd)
    

    def setdChOnOff( self, dCh, onOff:bool= None):
        cmd = ":LA:DIGI{}:DISPLAY {}" .format(dCh,"ON" if onOff else "OFF" )
        return  self.write(cmd)
    
    def rigolChannelProbe( self, ch, probe ):
        (val,unit) = self.instrumentValUnit(probe, validValues=["x"])
        cmd = ":CHAN{}:PROB {}".format( ch, probe)
        self.write( cmd )

    def rigolChannelBwLimit( self, ch, type ):
        """Set th bandwidth limit parameter of the specified channel.
        
        :CHANnel<n>:BWLimit <type>
        
        :ch: 1,2,3,4
        
        :type: 20M|OFF

        """
        self.instrumentValidate( value=type, validValues = ["OFF", "20M" ], context="Channel {} bandwidth {}".format(ch,type))
        cmd = ":CHAN{}:BWLimit {}".format( ch, type)
        self.write( cmd )

    def rigolStatDisplayOnOff( self, statsOnOff):
        self.write( ":MEAS:STAT:DISP {}".format(statsOnOff))

    def rigolStatClear(self, index=None ):
        if index == None:
            self.write(":MEAS:CLE ALL")
        else:
             self.write(":MEAS:CLE ITEM{}".format(index))

    def rigolChannelAmsOnOff( self, source):
        # TODO use chanStr
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
            except KeyError:
                pass
            return rigolUnit
        cmd = ":CHAN{}:UNIT {}".format( ch,si2RigolUnit(siUnit))
        self.write(cmd)

    # Math stuff

    def rigolMathOperator( self, operator):
        """Set or query the operator of the math operation.

        When the parameter in :MATH:SOURce1 and/or :MATH:SOURce2 is FX, this command is
        used to set the operator of the outer layer operation of compound operation. The range of
        <opt> is {ADD|SUBTract|MULTiply|DIVision|INTG|DIFF|SQRT|LOG|LN|EXP|ABS}

        :operator: ADD, SUBT, MULT, DIV, AND, OR, XOR, NOT, FFT, INTG,
                   DIFF, SQRT, LOG, LN, EXP, ABS, or FILT
        """
        cmd=f":MATH:OPER {operator}"
        self.write(cmd)

    def rigolMathSource( self, source, ch):
        """Set or query the source or source A of algebraic
        operation/functional operation/the outer layer operation of
        compound operation

        For algebraic operations, this command is used to set source A.
        
        For functional operations, only this command is used to set
        the source.

        For compound operations, this command is used to set source A
        of the outer layer operation when the outer layer operation is
        algeriac operation and the range of <src> is
        {CHANnel1|CHANnel2|CHANnel3|CHANnel4}; this command is used to
        set the source of the outer layer operation when the outer
        layer operation is functional operation and <src> can only be
        FX.

        Note: When the outer layer operation of compound operation is
        algebraic operation, at least one of source A and source B of
        the outer layer operation should be set to FX.

        When "FX" is selected, you can send the
        :MATH:OPTion:FX:SOURce1, :MATH:OPTion:FX:SOURce2, and
        :MATH:OPTion:FX:OPERator commands to set the sources and
        operator of the inner layer operation.

        :source: 1,2

        :ch: 1,2,3,4
        """
        cmd = f":MATH:SOUR{source} CHAN{ch}"
        self.write(cmd)

    def rigolMathScale( self, scale ):
        """Set or query the vertical scale of the operation result. The unit
        depends on the operator currently selected and the unit of the
        source.

        The range of the vertical scale is related to the operator
        currently selected and the vertical scale of the source
        channel. For the integration (intg) and differential (diff)
        operations, it is also related to the current horizontal
        timebase.

        """
        cmd = f":MATH:SCAL {scale}"
        self.write(cmd)

    def rigolMathOffset( self, offset ):
        """Set or query the vertical offset of the operation result. The unit
        depends on the operator currently selected and the unit of the source

        MathVerticalScale is the vertical scale of the operation
        result and can be set by the :MATH:SCALe command

        :offset: Related to the vertical scale of the operation result
        Range: (-1000 x MathVerticalScale) to (1000 x MathVerticalScale) Step:
        MathVerticalScale/50

        """
        cmd = f":MATH:OFFS {offset}"
        self.write(cmd)

    # Timebase stuff
    def rigolSetTimebase( self, scale ):
        """Set or query the main timebase scale. The default unit is s/div.

        When the horizontal timebase mode is YT and the horizontal
        timebase is 200ms/div or larger (namely the "Slow Sweep"
        mode), this command is invalid when the oscilloscope is in the
        transition to the "Stop" state.

        :scale: YT mode: 5ns/div to 50s/div in 1-2-5 step, Roll mode:
                200ms/div to 50s/div in 1-2-5 step

        """
        cmd = ":TIMebase:MAIN:SCALe {:.9f}".format(scale)
        self.write(cmd)
        
    def rigolSetTimebaseUnit( self, timebase ):
        """Set main timebase to 'timebase'

        :timebase: string with 'value' and 'unit'. Unit is one of
        ns,us,ms,s. For example 0.1ms

        """
        valToMult = {
            "ns": 10**-9,
            "us": 10**-6,
            "ms": 10**-3,
            "s": 1,
        }
        (val,unit) = self.instrumentValUnit(timebase, validValues=list(valToMult.keys()))
        self.rigolSetTimebase( scale = float(val)*valToMult[unit])
        

    # Trigger stuff

    def rigolTriggerStatusQuery(self):
        """Query :TRIG:STATUS?

        The query returns TD, WAIT, RUN, AUTO, or STOP.
        """
        return self.query( ":TRIG:STAT?", strip=True)

    def rigolTriggerMode(self, mode:str):
        """Set trigger TRIGger:MODE <mode>

        :mode: EDGE, PULS, RUNT, WIND, NEDG, SLOP, VID, PATT, DEL,
        TIM, DUR, SHOL, RS232, IIC, or SPI

        """
        self.write( ":TRIG:MODE {}".format(mode))
    
    def rigolTriggerCoupling( self, coupling:str):
        """Set trigger coupling :TRIGger:COUPling

        :coupling: AC, DC, LFR, or HFR

        """
        self.write( ":TRIG:COUP {}".format( coupling ))
                           
    def rigolTriggerEdgeSource( self, source:str ):
        """Set the trigger source in edge trigger :TRIGger:EDGe:SOURce <source>

        :source: D0, D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11,
        D12, D13, D14, D15, CHAN1, CHAN2, CHAN3, CHAN4, or AC """
        self.write( ":TRIG:EDGE:SOURCE {}".format( source ))

    def rigolTriggerEdgeSlope( self, slope:str ):
        """Set or query the edge type in edge trigger.  
        :TRIGger:EDGe:SLOPe <slope>

        :slope: POS, NEG, or RFAL

        """
        self.write( ":TRIG:EDGE:SLOPE {}".format(slope))

    def rigolTriggerSweep( self, sweep:str ):
        """Set or query the trigger mode.

        AUTO: auto trigger. No matter whether the trigger condition is met, there is always
        waveform display.

        NORMal: normal trigger. Display waveform when the trigger
        condition is met; otherwise, the oscilloscope holds the
        original waveform and waits for the next trigger.

        SINGle: single trigger. The oscilloscope waits for a trigger
        and displays the waveform when the trigger condition is met and then stops

        """
        validSweeps = [ "AUTO", "NORMAL", "SINGLE"]
        cmd = ":TRIG:SWEEP {}".format( self.instrumentValidate(
            sweep.upper(), validSweeps, context=f"Trigger sweep {sweep}") )
        self.write( cmd)
    
        
    def rigolTriggerEdgeLevel( self, level):
        """Set :TRIGger:EDGe:LEVel <level>.
        
        :level: The unit is the same as the current amplitude unit of
        the signal source selected. 

        Example: TRIGger:EDGe:LEVel 0.16
        """
        self.write(":TRIGger:EDGe:LEVel {}".format(level))
                           
    # MSO commands
    
    def rigolDigitalLabel( self, ch, label):
        self.write(":LA:DIGITAL{}:LABEL {}".format(ch, label) )
    
    def rigolDigitalPodOnOff( self, pod, onOff="ON" ):
        self.write(":LA:DISP POD{},{}".format(pod, onOff))

    
        

