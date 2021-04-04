#!/usr/bin/env python3

from typing import Dict, List

from pprint import pformat
from datetime import datetime
import inspect
import textwrap

import os
import sys
from absl import flags, logging
import re

import pyvisa


flags.DEFINE_integer('debug', -1, '-3=fatal, -1=warning, 0=info, 1=debug')
flags.DEFINE_string('ip', "skooppi", "IP address of pyvisa instrument")
flags.DEFINE_string('addr', None, "pyvisa instrument address")
flags.DEFINE_string('captureDir', "pics", "Screen capture directory")
flags.DEFINE_string('recordingDir', "tmp", "Directory where command line recordings are saved into")
flags.DEFINE_string('csvDir', "tmp", "Directory where command CSV files are saved into")




class MenuValueError(ValueError):
    """Exception catched in inveractive mode: Instead of aborting
    execution, user is notified of the error and operation continues
    with promting for next action. (In non-interactive mode execution
    is aborted)

    """
    pass
class MenuNoRecording(Exception):
    pass

TOOLNAME="ebench"
class Instrument:

    def __init__( self, debug = False ):
        self.debug = debug

    def close(self):
        pass

        
    def screenShot( self, captureDir, fileName=None, ext="png", prefix="EB-"  ):
        if fileName is None or not fileName:
            now = datetime.now()
            fileName = "{}{}.{}".format( prefix, now.strftime("%Y%m%d-%H%M%S"), ext )
        filePath = os.path.join( captureDir, fileName )
        logging.info( "screenShot: filePath={}".format(filePath) )
        self.screenShotImplementation(filePath=filePath)
        return filePath

    def screenShotImplementation( self, filePath):
        """screenShotImplementation method MUST be be implemented for a concrete instrument
        """
        raise NotImplementedError("screenShotImplementation not implmemented for class {}".format( self.__class__.__name__))
        

    def valUnit( self, valUnitStr, validValues:List[str]=None ):
        """Extract value and unit from 'valUnitStr' using VAL_UNIT_REGEXP
        
        VAL_UNIT_REGEXP=r"(?P<value>-?[0-9\.]+)(?P<unit>[a-zA-Z%]+)"

        :valUnitStr: string from which to extrac valid value

        :validValues: list of valid unit string

        :return: (val,unit)
        """

        # Extract value/unit
        VAL_UNIT_REGEXP=r"(?P<value>[0-9-\.]+)(?P<unit>[a-zA-Z%]+)"
        match = re.search( VAL_UNIT_REGEXP, valUnitStr )
        if match is None:
            msg = "Could not extract unit value from '{}'".format( valUnitStr )
            logging.error(msg)
            raise MenuValueError(msg)
        (val,unit) = ( match.group('value'), match.group('unit') )

        # Validate - if validation requested
        if validValues is not None and unit not in  validValues:
            msg = "{} > expecting one of {} - got '{}'".format( valUnitStr, validValues, unit  )
            logging.error( msg )
            raise MenuValueError(msg)
             
        return (val,unit)

class PyInstrument(Instrument):
    """Instrument which can be accessed using pyvisa
    """
    
    # ------------------------------------------------------------------
    # Singleton

    # ResourceManager signleton
    _rm = None

    def singleton_rm():
        if PyInstrument._rm is None:
            PyInstrument._rm = pyvisa.ResourceManager()
        return PyInstrument._rm

    def closetti():
        try:
            logging.info(  "Closing Resource manager {}".format(PyInstrument._rm))
            PyInstrument._rm.close()
            PyInstrument._rm = None
        except:
            logging.warn(  "Closing Resource manager {} - failed".format(PyInstrument._rm))


    # ------------------------------------------------------------------
    # construct && close
    
    def __init__( self, addr, debug = False ):
        super().__init__( debug=debug)
        logging.info( "Open PyInstrument instrument in addr {}".format(addr))
        self.addr = addr
        try:
            self.instrument = PyInstrument.singleton_rm().open_resource(self.addr)
        except pyvisa.errors.VisaIOError as err:
                 self.instrument = None
                 logging.error(err)
        except ValueError as err:
                 self.instrument = None
                 logging.error(err)
        
        if debug:
            pyvisa.log_to_screen()

    def close(self):
        super().close()
        PyInstrument.closetti()

    # ------------------------------------------------------------------
    # properties
    @property
    def addr(self) -> str :
        if not hasattr(self, "_addr"):
             return None
        return self._addr

    @addr.setter
    def addr( self, addr:str):
        self._addr = addr

    # ------------------------------------------------------------------
    # Low level communication
    def write(self, cmd ):
        logging.info( "write: {}".format(cmd))
        if self.instrument is not None:
            self.instrument.write(cmd)
        else:
            logging.error( "write '{}' failed - self.instrument is None".format(cmd))

    def read_raw(self):
        if self.instrument is not None:
            raw = self.instrument.read_raw()
            logging.info( "read_raw return getsizeof(raw) {} bytes".format(sys.getsizeof(raw)))
            return raw
        else:
            logging.error( "read_raw failed - self.instrument is None")
            return None

    def query(self, cmd, strip=False ):
        logging.info( "query: {}".format(cmd))
        if self.instrument is not None:
            ret = self.instrument.query(cmd)
            logging.debug( "query: {} --> {}".format(cmd,ret))
            if strip: ret = ret.rstrip()
            return  ret
        else:
            logging.error( "query '{}' failed - self.instrument is None".format(cmd))
            return None

    # ------------------------------------------------------------------
    # Common commands to all visa instrumetn
    
    def pyvisaGetName(self):
       return( self.query( "*IDN?"))

    def pyvisaReset(self):
        self.write( "*RST" )

class Osciloscope(PyInstrument):
    """Pyvisa instrument managing pyvisa resource and communicating using
    write and query operations
    """

    def __init__( self, addr, debug = False ):
        super().__init__( addr=addr, debug=debug)
        
    def close(self):
        super().close()

class SignalGenerator(PyInstrument):
    def __init__( self, addr, debug = False ):
        super().__init__( addr=addr, debug=debug)

    def close(self):
        super().close()
        
class MenuCtrl:

    # Well knonw menu items
    MENU_QUIT="q"             # quits loop
    MENU_REC_SAVE="."         # save recording
    MENU_REC_START="!"        # start/rerset recording
    MENU_HELP="?"             # list commands
    MENU_CMD_PARAM="??"       # list command paramters
    MENU_VERSION="_version"   # output version number (hidden command)
    MENU_SCREEN="screen"      # output screenshot
    
    def __init__( self):
        self.recording = []

    @property
    def recording(self) -> List[str] :
        if not hasattr(self, "_recording"):
             return None
        return self._recording

    @recording.setter
    def recording( self, recording:List[str]):
        self._recording = recording

    # Actions
    def startRecording(self):
        """@see module startRecording"""
        self.recording = []
        # Recording actions not recorded
        raise MenuNoRecording

    def appendRecording( self, menuCommand:str, commandParameters:Dict[str,str]={}):
        """Append serialization of  'menuCommand' and 'commandParameters' to
        'recording' -array
        """
        self.recording = self.recording + [menuCommand] + [ "{}={}".format(k,v) for k,v in commandParameters.items() ]
        logging.debug( "appendRecording: {}".format(self.recording))

    def anyRecordings( self ) -> bool:
        """Recording status. True is something in recording bufffer"""
        return len(self.recording) > 0
        
    def stopRecording(self, pgm, fileName =None, fileDir=None ):
        """@see module function 'stopRecording'
        """
        logging.info( "stopRecording: {} to be into '{}'".format(self.recording,fileName))
        commandsAndParameters = " ".join( self.recording)
        pgm_commandsAndParameters = "{} {}".format(pgm, commandsAndParameters)
        if fileName is None or not fileName or fileName == MenuCtrl.MENU_REC_SAVE:
            print(pgm_commandsAndParameters)
        else:
            if not os.path.exists( fileDir):
                raise MenuValueError( "Non existing recording directory: {}".format(fileDir))
            filePath= os.path.join( fileDir, fileName)
            if os.path.isdir( filePath ):
                raise MenuValueError( "Recording path is directory: {}".format(filePath))
            with open( filePath, "a") as fh:
                fh.write("{}\n".format(pgm_commandsAndParameters))
            self.startRecording()
        # Recording actions not recorded
        raise MenuNoRecording


    def promptValue( prompt:str, key:str=None, cmds:List[str]=None,
                     validValues:List[str]=None, defaultParameters:dict={} ):
        """Two uses 1) prompt user for menuCommand, 2) prompt user for
        commandParameters

        :key: Lookding for key-value pair for commandParameters 

        :defaultParameters: >dict->value, use 'key' to check if
        promted value has default value, if it has update prompted
        result to 'defaultParameters'. As the result: is default value
        is set, it used if user does not change it, default value is
        rememebered between calls

        """
        ans = None
        logging.debug( "promptValue: key={}, cmds={},".format(key,cmds))
        if cmds is None:
            # Interactive mode

            # default value modifies prompt
            if key in defaultParameters:
                # default value defined
                prompt = "{} ({})".format(prompt, defaultParameters[key])
            ans = input( "{} > ".format(prompt))

            # after user answer check if default accepted/default should be changed
            if key in defaultParameters:
                if ans is None or not ans:
                    # Default value accepted
                   ans = defaultParameters[key]
                else:
                    # Default value to rememeber changed
                    defaultParameters[key] = ans

        else:
            # ans <- batch
            if len(cmds) > 0:
                # ans <- batch
                if key is None:
                    ans = cmds.pop(0)
                else:
                    # expecting key=value
                    peek1st = cmds[0]
                    match = re.search( r"(?P<key>.+)=(?P<value>.*)", peek1st )
                    if match is not None:
                        # key-value pair found
                        if match.group('key') == key:
                            # key matches
                            cmds.pop(0)
                            ans = match.group('value')
                        else:
                            # key does not match
                            ans = None
                    else:
                        # no key-value pair (when expecting one)
                        ans = None

                        
            if ans is None and key in defaultParameters:
                # Batch default
                # value not in found 
                logging.debug( "Bathc ans for key {} defaultValue {}".format(key, defaultParameters[key]))
                ans = defaultParameters[key]

            if key in defaultParameters:
                logging.debug( "Change key: {} defaultValue {}->{}".format(key, defaultParameters[key], ans))
                # update default value for key
                defaultParameters[key] = ans
                




        # ans found - lets check validity
        if validValues is not None:
            if ans not in  validValues:
                msg = "{} > expecting one of {} - got '{}'".format( prompt, validValues, ans  )
                logging.error(msg)
                print(msg)
                return None
        logging.info( "promptValue: --> {}".format(ans))
        return ans 

    def mainMenu( self, _argv, mainMenu:Dict[str,List], mainPrompt= "Command [q=quit,?=help]", defaults:Dict[str,Dict]= None ):
        """
        For interactive usage, prompt user for menu command and command
        parameters, for command line usage parse commands and
        parameters from '_argv'. Invoke action for command.

        :_argv: command line paramaters (in batch mode)

        :mainMenu: dict mapping menuCommand:str -> menuSelection =
        List[menuPrompt,parameterPrompt,menuAction], where
        - menuPrompt: string presented to user to query for
          'commandParameter' value
        - parameterPrompt: dict mapping 'commandParameter' name to
          commandParameter prompt
        - menuAction: function to call with 'commandParameters' (as
          **argv values prompted with parameterPrompt)

        :defaults: is dictionary mapping 'menuCommand' to
        'defaultParameters'.  If 'defaultParameters' for a
        'menuCommand' is found, it is used to lookup 'defaultValue'
        prompeted from user. Also, If 'defaultParameters' for a
        'menuCommand' is found, 'defaultParameters' update with the
        value user enters for the promt.

        """

        # Interactive receives only pgroramm name in _argv
        interactive = len(_argv) == 1
        pgm=_argv[0]
        logging.info( "Starting pgm={}, interactive={}".format(pgm, interactive))

        
        def execMenuCommand(mainMenu,menuCommand,defaults):
            # Extract mainMenu elements
            menuSelection = mainMenu[menuCommand]

            # 'defaultParameters' contains default values remm
            defaultParameters = {}
            if defaults is not None and menuCommand in defaults:
                defaultParameters  = defaults[menuCommand]


            # menuPrompt = menuSelection[0]
            parameterPrompt = menuSelection[1]
            menuAction =  menuSelection[2]
            commandParameters = {}

            if parameterPrompt is not None:
                # Promp user/read CLI keyvalue parameters
                commandParameters = {
                        k: MenuCtrl.promptValue(v,key=k,cmds=cmds,defaultParameters=defaultParameters) for k,v in parameterPrompt.items()
                }

            if menuAction is not None:
                try:
                    # Call menu action (w. parameters)
                    returnVal = menuAction( **commandParameters )
                    self.appendRecording( menuCommand, commandParameters )
                    if returnVal is not None: # and interactive:
                        print( pformat(returnVal) )
                except MenuValueError as err:
                    if interactive:
                        # Interactive error - print erros msg && continue
                        print( "Error: {}".format(str(err)))
                    else:
                        raise
                except MenuNoRecording:
                    # Help, start/stop recording commands
                    pass
                except Exception as err:
                    # In Interactive mode all errors are printed, user quits 
                    if interactive:
                        # Interactive error - print erros msg && continue
                        print( "Error: {}".format(str(err)))
                    else:
                        raise
                    
            return True

        
        cmds = None
        if not interactive:
            # batch executes all CLI parameters
            cmds = _argv[1:]

        logging.info( "interactive: {} Starting cmds={}".format(interactive, cmds))
        
        goon = True
        while goon:
            if not interactive and len(cmds) == 0:
                # all commands consumed - quit batch
                break
            menuCommand = MenuCtrl.promptValue(mainPrompt,
                                               cmds=cmds, validValues=mainMenu.keys() )
                
            logging.debug( "Command '{}'".format(menuCommand))
            if menuCommand is None:
                continue
            elif menuCommand == MenuCtrl.MENU_QUIT:
                goon = False
            else:
                goon = execMenuCommand( mainMenu, menuCommand,defaults)

        # Confirmm whether save recording
        if self.anyRecordings() and interactive and MenuCtrl.MENU_REC_SAVE in mainMenu:
            print( "Save recordings?")
            execMenuCommand( mainMenu, MenuCtrl.MENU_REC_SAVE,defaults)

# ------------------------------------------------------------------
# Common menu actions


def menuScreenShot( instrument:Instrument, captureDir, prefix ):
    """Lambda function to use in mainMenu construct

    Usage example: 

    Document string in f is presented in help commands

    """

    def f( **argv ):
        """Take a screen shot from instrument and save it to a file

        Method of taking the screen shot varies deding on the
        instrument

        """
        return instrument.screenShot( captureDir=captureDir, prefix=prefix, **argv)
    return f

def menuStartRecording(cmdController:MenuCtrl):
    """Lambda function to use in mainMenu construct

    Usage example: MenuCtrl.MENU_REC_START  : ( "Start recording", None, menuStartRecording ),

    Document string in f is presented in help commands

    """
    def f(**argv):
        """Clear the command list, which {TOOLNAME} -tool collects during
        interactive session

        The command list can be later saved into a file

        """
        return cmdController.startRecording(**argv)
    return f


def menuStopRecording( cmdController:MenuCtrl, pgm, fileDir ):
    """Lambda function to use in mainMenu construct

    Usage example: 
      MenuCtrl.MENU_REC_SAVE   : 
       ( "Stop recording", stopRecordingPar, 
          menuStopRecording(cmdController, pgm=_argv[0], fileDir=FLAGS.recordingDir ) ),

    Document string in f is presented in help commands

    """
    def f(**argv):
        """Save current command recording history to 'fileName' in 'fileDir'
        and clear command history.

        If no 'fileName' given, just print current command history
        (and do not clear command history)

        """
        return cmdController.stopRecording(pgm=pgm, fileDir=fileDir, **argv )
    return f

def version():
    """Version number of ebench tool"""
    versionPath = os.path.join( os.path.dirname( __file__), "..", "VERSION")
    with open( versionPath, "r") as fh:
        version = fh.read().rstrip()
    return version

def list_resources():
    """List resources pyvisa finds"""
    logging.info( "List resources called")
    return PyInstrument.singleton_rm().list_resources()

def usageListCommands( mainMenu:dict[str,List] ):
    """Prints 'mainMenu' ()

    Menu item 
    - with no prompt are separators
    - with prompt starting with _ are hidden (=not printed)
    
    """
    
    print( "Commands:")
    print( "")
    for k,v in mainMenu.items():
        if v[0]:
            if  k[0] == '_' :
                # Hidden menu item
                pass
            else:
            # Normal menu
                print( "%15s  : %s" % (k,v[0]) )
        else:
            # Separator
            print( "---------- %10s ----------" % (k.center(10)) )


def usageSynopsis( cmd, mainMenu, synopsis ):
    print( "{}: {}".format(cmd, synopsis) )
    print( "" )
    print( "Usage: {} [options] [commands and parameters] ".format(cmd))
    print( "" )

def subMenuHelp( command, menuText, commandParameters, menuAction = None ):
    """Print 'menuText' as synopsis, followed by 'menuAction' docstring
     and 'commandParameters'"""

    # Synopsis
    print( "{} - {}".format( command, menuText))
    print( "" )
    
    # Docstring
    if menuAction is not None:
        if menuAction.__doc__ is None or not menuAction.__doc__:
            missingDoc = textwrap.dedent( f"""
                 !!!!!!!!!!!
                 '{command}' -command does not define doc-string clarifying actions taken. 
   
                 Raise an issue to developer to add the missing  doc-string to {command}'-command
                 !!!!!!!!!!!""")
            
            print(missingDoc)
        else:
            print(inspect.getdoc(menuAction))
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


def usage( cmd, mainMenu, synopsis=None, command=None, usageText=None  ):
    """Outputs synonpsis, list of commands in 'mainMenu', followed by
    'usageText' (if given)

    :cmd: part of synosis

    :synopsis: short one line documentation

    :mainMenu: app commands structure, see function 'mainMenu'

    :usageText: print after synopsis

    """
    usageSynopsis( cmd=cmd, mainMenu=mainMenu, synopsis=synopsis)
    usageListCommands(mainMenu)
    if usageText is not None:
        print( usageText)
    

    # Help actions not recorded
    raise MenuNoRecording()

def usageCommand( command, mainMenu ):
    """
    Document 'command' in 'mainMenu'


    """
    commandParameters = {} if mainMenu[command][1] is None else mainMenu[command][1]
    menuActionToDoc = None
    if command not in [ MenuCtrl.MENU_QUIT, MenuCtrl.MENU_HELP, MenuCtrl.MENU_CMD_PARAM]:
        # non trivial
        menuActionToDoc = mainMenu[command][2]
    subMenuHelp( command, menuText=mainMenu[command][0], commandParameters=commandParameters, menuAction=menuActionToDoc )
    # Help actions not recorded    
    raise MenuNoRecording()





