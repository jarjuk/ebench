#!/usr/bin/env python3

from typing import Dict, List

from pprint import pformat
from datetime import datetime
import inspect
import textwrap

import os
from absl import flags, logging
import re

import pyvisa


flags.DEFINE_integer('debug', -1, '-3=fatal, -1=warning, 0=info, 1=debug')

class MenuValueError(ValueError):
    pass
class MenuNoRecording(Exception):
    pass

TOOLNAME="ebench"
class Instrument:

    _rm = pyvisa.ResourceManager()
    @staticmethod
    def list_resources():
        logging.info( "List resources called")
        return Instrument._rm.list_resources()

    @staticmethod
    def singleton_rm():
        return Instrument._rm
    

    def __init__( self, debug = False ):
        self.debug = debug
        if self.debug:
            pyvisa.log_to_screen()

    def close(self):
        Instrument.closetti()

    def closetti():
        try:
            logging.info(  "Closing Resource manager {}".format(Instrument._rm))
            Instrument._rm.close()
            Instrument._rm = None
        except:
            logging.warn(  "Closing Resource manager {} - failed".format(Instrument._rm))
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

    # Well knonw menu items
    MENU_QUIT="q"             # quits loop
    MENU_REC_SAVE="."         # save recording
    MENU_REC_START="!"        # start/rerset recording
    MENU_HELP="?"             # list commands
    MENU_CMD_PARAM="??"       # list command paramters
    MENU_VERSION="version"    # output version number
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
        if fileName is None or not fileName or fileName == Cmd.MENU_REC_SAVE:
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
        

        """

        # Interactive receives only pgroramm name in _argv
        interactive = len(_argv) == 1
        pgm=_argv[0]

        
        def execMenuCommand(mainMenu,menuCommand):
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
                    if returnVal is not None and interactive:
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
            return True

        
        cmds = None
        if not interactive:
            # batch executes all CLI parameters
            cmds = _argv[1:]

        logging.info( "Interactive: {} Starting cmds={}".format(interactive, cmds))
        
        goon = True
        while goon:
            if cmds is not None and not interactive():
                # all commands consumed - quit batch
                break
            menuCommand = Cmd.promptValue( mainPrompt, cmds=cmds, validValues=mainMenu.keys() )
                
            logging.debug( "Command '{}'".format(menuCommand))
            if menuCommand is None:
                continue
            elif menuCommand == Cmd.MENU_QUIT:
                goon = False
            else:
                goon = execMenuCommand( mainMenu, menuCommand)

        # Confirmm whether save recording
        if self.anyRecordings() and interactive and Cmd.MENU_REC_SAVE in mainMenu:
            print( "Save recordings?")
            execMenuCommand( mainMenu, Cmd.MENU_REC_SAVE)

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
        return instrument.screenShot( **argv)
    return f

def menuStartRecording(cmdController:Cmd):
    """Lambda function to use in mainMenu construct

    Usage example: Cmd.MENU_REC_START  : ( "Start recording", None, menuStartRecording ),

    Document string in f is presented in help commands

    """
    def f(**argv):
        """Clear the command list, which {TOOLNAME} -tool collects during
        interactive session

        The command list can be later saved into a file

        """
        return cmdController.startRecording(**argv)
    return f


def menuStopRecording( cmdController:Cmd, pgm, fileDir ):
    """Lambda function to use in mainMenu construct

    Usage example: 
      Cmd.MENU_REC_SAVE   : 
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
    print( Instrument.list_resources() )

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


def usage( mainMenu, mainMenuHelp, subMenuHelp, command=None  ):
    """Output 'mainMenuHelp' if 'command' is None else 'subMenuHelp' for
    'command'

    :mainMenu: application main commands

    :mainMenuHelp: lambda to start if 'command' is None, output mainMenu

    :subMenuHelp: lambda to start if 'command' is not None, output
    one liner from mainMenu for command synopsis, and then command
    parameters from mainMenu

    :doc: Output menuAction docString True/False(=default), unless
    'command' is one of MENU_QUIT, MENU_HELP, MENU_CMD_DOC, MENU_CMD_PARAM

    """
    if command is None or not command:
        mainMenuHelp(mainMenu=mainMenu)
    else:
        commandParameters = {} if mainMenu[command][1] is None else mainMenu[command][1]
        menuActionToDoc = None
        if command not in [ Cmd.MENU_QUIT, Cmd.MENU_HELP, Cmd.MENU_CMD_PARAM]:
            menuActionToDoc = mainMenu[command][2]
        subMenuHelp( command, menuText=mainMenu[command][0], commandParameters=commandParameters, menuAction=menuActionToDoc )

    # Help actions not recorded
    raise MenuNoRecording()




