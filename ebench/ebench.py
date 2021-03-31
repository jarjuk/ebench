#!/usr/bin/env python3

from typing import Dict, List

from pprint import pformat
from datetime import datetime

import os
from absl import flags, logging
import re

import pyvisa


flags.DEFINE_integer('debug', -1, '-3=fatal, -1=warning, 0=info, 1=debug')

class MenuValueError(ValueError):
    pass
class MenuNoRecording(Exception):
    pass


class Ebench:

    _rm = pyvisa.ResourceManager()
    @staticmethod
    def list_resources():
        logging.info( "List resources called")
        return Ebench._rm.list_resources()

    @staticmethod
    def singleton_rm():
        return Ebench._rm
    

    def __init__( self, debug = False ):
        self.debug = debug
        if self.debug:
            pyvisa.log_to_screen()

    def close(self):
        Ebench.closetti()

    def closetti():
        try:
            logging.info(  "Closing Resource manager {}".format(Ebench._rm))
            Ebench._rm.close()
            Ebench._rm = None
        except:
            logging.warn(  "Closing Resource manager {} - failed".format(Ebench._rm))
            pass
    
    def screenShot( self, captureDir, fileName=None, ext="png", prefix="EB-"  ):
        if fileName is None or not fileName:
            now = datetime.now()
            fileName = "{}{}.{}".format( prefix, now.strftime("%Y%m%d-%H%M%S"), ext )
        filePath = os.path.join( captureDir, fileName )
        logging.info( "screenShot: filePath={}".format(filePath) )
        self.ilScreenShot(filePath=filePath)
        return filePath
        

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


class Cmd:

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
        self.recording = []
        # Recording actions not recorded
        raise MenuNoRecording

    def appendRecording( self, menuCommand:str, commandParameters:Dict[str,str]={}):
        """Append serialization of  'menuCommand' and 'commandParameters' to
        'recording' -array
        """
        self.recording = self.recording + [menuCommand] + [ "{}={}".format(k,v) for k,v in commandParameters.items() ]
        logging.debug( "appendRecording: {}".format(self.recording))
    
        
    def stopRecording(self, pgm, fileName =None, fileDir=None ):
        """Save recording to 'fileName' in 'fileDir' and start a new
        recording. If 'fileName' not given (or if it empty) just print
        recording.

        :fileName: where to save (None or empty just print to screen)

        :fileDir: directory of fileName

        """
        logging.info( "stopRecording: {} to be into '{}'".format(self.recording,fileName))
        commandsAndParameters = " ".join( self.recording)
        pgm_commandsAndParameters = "{} {}".format(pgm, commandsAndParameters)
        if fileName is None or not fileName or fileName == ".":
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


    def promptValue( prompt:str, key:str=None, cmds:List[str]=None, validValues:List[str]=None ):
        ans = None
        if cmds is None:
            # ans <- interactive
            ans = input( "{} > ".format(prompt) )
        else:
            if len(cmds ) > 0:
                # ans <- batch
                if key is None:
                    # not expecting key-value pair - take first
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



        # ans found - lets check validity
        if validValues is not None:
            if ans not in  validValues:
                print( "{} > expecting one of {} - got '{}'".format( prompt, validValues, ans  ))
                return None
        return ans 

    def mainMenu( self, _argv, mainMenu:Dict[str,List], mainPrompt= "Command [q=quit,?=help]" ):
        """For interactive usage, prompt user for menu command and command
        paramaters, for command line usage parse commands and
        parameters from command line. Invoke action for command.

        :_argv: command line paramaters

        :mainMenu: dict mapping menuCommand:str -> menuSelection =
        List[menuPrompt,parameterPrompt,menuAction], where
        - menuPrompt: string presented to user to query for
          commandParameter value
        - parameterPrompt: dict mapping commandParameter name to
          commandParameter prompt
        - menuAction: function to call with 'commandParameters' (as
          **argv values prompted with parameterPrompt)
        
        Special mainMenu commands:
        - q : quits loop
        - Q : quits loop

        """

        def isInteractive():
            """Interactive receives only pgroramm name in _argv
            """
            return len(_argv) == 1
        
        cmds = None
        if not isInteractive():
            cmds = _argv[1:]

        logging.info( "Interactive: {} Starting cmds={}".format(isInteractive(), cmds))

        
        goon = True
        while goon:
            if cmds is not None and len(cmds) == 0:
                # all commands consumed - quit batch
                break
            menuCommand = Cmd.promptValue( mainPrompt, cmds=cmds, validValues=mainMenu.keys() )
                
            logging.debug( "Command '{}'".format(menuCommand))
            if menuCommand is None:
                continue
            elif menuCommand == 'q' or menuCommand == 'Q':
                goon = False
            else:
                # Extract mainMenu elements
                menuSelection = mainMenu[menuCommand]
                
                # menuPrompt = menuSelection[0]
                parameterPrompt = menuSelection[1]
                menuAction =  menuSelection[2]
                commandParameters = {}

                if parameterPrompt is not None:
                    # Promp user/read CLI keyvalue parameters
                    commandParameters = {
                            k: Cmd.promptValue(v,key=k,cmds=cmds) for k,v in parameterPrompt.items()
                        }
                        
                if menuAction is not None:
                    # Call menu action (w. parameters)
                    try:
                        returnVal = menuAction( **commandParameters )
                        self.appendRecording( menuCommand, commandParameters )
                        if returnVal is not None and isInteractive():
                            print( pformat(returnVal) )
                    except MenuValueError as err:
                        if isInteractive():
                            # Error in command parameter value - start over instead of exiting
                            print( "Error: {}".format(str(err)))
                            continue
                        else:
                            raise
                    except MenuNoRecording:
                        # Help, start/stop recording commands
                        pass

# ------------------------------------------------------------------
# Common menu actions 

def version():
    versionPath = os.path.join( os.path.dirname( __file__), "..", "VERSION")
    with open( versionPath, "r") as fh:
        version = fh.read().rstrip()
    return version

def list_resources():
    print( Ebench.list_resources() )

def mainMenuHelpCommon( cmd, mainMenu, synopsis ):
    print( "{} - {}: {}".format(cmd, version(), synopsis) )
    print( "" )
    print( "Usage: {} [options] [commands and parameters] ".format( cmd ))
    print( "" )
    print( "Commands:")
    for k,v in mainMenu.items():
        if v[0]:
            # Normal menu
            print( "%15s  : %s" % (k,v[0]) )
        else:
            # Separator
            print( "---------- %10s ----------" % (k.center(10)) )


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


def usage( mainMenu, mainMenuHelp, subMenuHelp, command=None  ):
    """Output 'mainMenuHelp' if 'command' is None else 'subMenuHelp' for
    'command'

    :mainMenu: application main commands

    :mainMenuHelp: lambda to start if 'command' is None, output mainMenu

    :subMenuHelp: lambda to start if 'command' is not None, output
    one liner from mainMenu for command synopsis, and then command
    parameters from mainMenu

    """
    if command is None or not command:
        mainMenuHelp(mainMenu=mainMenu)
    else:
        commandParameters = {} if mainMenu[command][1] is None else mainMenu[command][1]
        subMenuHelp( command, menuText=mainMenu[command][0], commandParameters=commandParameters )

    # Help actions not recorded
    raise MenuNoRecording()




