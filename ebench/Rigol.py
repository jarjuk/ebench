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
    # Template methods (used in base classes)

        
    def screenShotImplementation( self, filePath):
        """Screenshot implementation

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
         cmd = ":MEASure:STAT:ITEM? {},{},CHAN{}".format(statistic, item, ch)
         return( float(self.query(cmd)))

    def rigolChannelMeasure( self, item, ch):
         cmd = ":MEASure:ITEM? {},CHAN{}".format(item, ch)
         logging.info( "rigolChannelMeasure: cmd={}".format(cmd))
         return( float(self.query(cmd)))

    def rigolMeasurement(self, ch, item, statistic=None):
        """Single channel item (statics) measurement . 

        :ch: channel to measure

        :statistic: If 'statistic' given make statistic item
                    measurement (:MEASure:STATistic:ITEM) else make
                    item measurement (:MEASure:ITEM <item>). 

                    Valid values MAXimum|MINimum|CURRent|AVERages|
DEViation}


        :item: VMAX, VMIN, VPP, VTOP, VBASe, VAMP, VAVG, VRMS,
        OVERshoot, MARea, MPARea, PREShoot, PERiod, FREQuency, RTIMe, FTIMe,
        PWIDth, NWIDth, PDUTy, NDUTy, TVMAX, TVMIN, PSLEWrate, NSLEWrate,
        VUPper, VMID, VLOWer, VARIance, PVRMS, PPULses, NPULses, PEDGes, and
        NEDGes

        """
        
        
        if statistic is None:
            val = self.rigolChannelMeasure( item=item, ch=ch)
        else:
            val = self.rigolChannelStatMeasure( item=item, ch=ch, statistic=statistic )

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

    def rigolStatClear(self, index=None ):
        if index == None:
            self.write(":MEAS:CLE ALL")
        else:
             self.write(":MEAS:CLE ITEM{}".format(index))

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
            except KeyError:
                pass
            return rigolUnit
        cmd = ":CHAN{}:UNIT {}".format( ch,si2RigolUnit(siUnit))
        self.write(cmd)

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

    
        

