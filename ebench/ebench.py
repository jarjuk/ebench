#!/usr/bin/env python3

from typing import Dict, List, Callable, Tuple, Union

from pprint import pformat
from datetime import datetime
import inspect
import textwrap

import ast
import os
import sys
import json
from absl import flags, logging
from absl.flags import FLAGS
import re
import importlib

import csv
import pyvisa

OUTPUT_TEMPLATE_DEFAULT="API"

flags.DEFINE_integer('debug', -1, '-3=fatal, -1=warning, 0=info, 1=debug')
flags.DEFINE_string('captureDir', "pics", "Screen capture directory")
flags.DEFINE_string('recordingDir', "tmp", "Directory where command line recordings are saved into")
flags.DEFINE_string('csvDir', "tmp", "Directory where command CSV files are saved into")
flags.DEFINE_enum( "outputTemplate", None, [OUTPUT_TEMPLATE_DEFAULT], "{}: convert cmds to API calls, default(None): execute cmds)".format(OUTPUT_TEMPLATE_DEFAULT))

# ------------------------------------------------------------------
# output Template

class OutputTemplate: 
    """
    Template to format menuCommand and commandParameters instead of executing
    them using menuAction lambda
    """

    def __init__(self):
        pass


    def formatTemplate( self, name:str, menuCommand:str, commandParameters:dict)->str:
        raise NotImplementedError( "formatTemplate: implementation missing on {}".format(self.__class__.__name__))
    
    def outputTemplate( self, templateStr ):
        print( templateStr )

    def applyTemplate( self, name, menuCommand:str, commandParameters:dict):
        """Template service called from menu controller

        :name:  name of program/sub menuCommand

        """
        self.outputTemplate(self.formatTemplate(name, menuCommand=menuCommand,commandParameters=commandParameters))

class OutputTemplateApi(OutputTemplate):
    def formatTemplate( self, name:str, menuCommand:str, commandParameters:dict)->str:
        """:return: instance.method( **argv ), where name->instance,
        menuCommand->method, commandParameters->**argv
        """
        def name2Instance( name:str )->str:
            return os.path.splitext(os.path.basename(name))[0]
        def formatValue( v ):
            return '"{}"'.format(v)
        dictAsKeyValues = ", ".join(  [ "{}={}".format(k,formatValue(v)) for k,v in commandParameters.items() ])
        return f"{name2Instance(name)}.{menuCommand}({dictAsKeyValues })"


# ------------------------------------------------------------------
# infrastructure services

def version():
    """Version number of ebench tool"""
    versionPath = os.path.join( os.path.dirname( __file__), "..", "VERSION")
    with open( versionPath, "r") as fh:
        version = fh.read().rstrip()
    return version

def printExampleYaml():
    with open(os.path.join( os.path.dirname(__file__), "ebMenu.yaml"), "r") as f:
        print( f.read())

def list_resources():
    """List resources pyvisa finds"""
    logging.info( "List resources called")
    return PyInstrument.singleton_rm().list_resources()

# ------------------------------------------------------------------
# Abstract instrment class
        
class Instrument:

    def __init__( self, debug = False ):
        self.debug = debug

    def close(self):
        logging.info( "Instrument: close called")

    # timestamp when measurement taken
    MEASUREMENT_TS="timestamp"

    # special intrument feed 'USER' (e.g. promp askUser)
    USER_FEED="USER"

    def callByName( self, _name, *args, **kwargs ):
        """
        Call method 'name' and pass arguments
        
        :name: method to call

        :return: value returned by 'name' -method
        """
        logging.debug( "callByName: _name={}, *args={}, **kwargs={}.".format(_name, args, kwargs))
        return getattr( self, _name )( *args,  **kwargs )
        
    def askUser( self, item, validValues:List[str]= None ):
        """Prompt user a value (e.g for a measurement). If 'validValues' is
        given accept one the given values

        """
        validPrompt = "" if validValues is None else " ({})".format(" ".join(validValues))
        prompt = "Enter value for {}{}".format(item, validPrompt )
        return MenuCtrl.promptValue( prompt = prompt, validValues=validValues, )
        
        
    def screenShot( self, captureDir, fileName=None, ext="png", prefix="EB-"  ):
        """Take screenshot into file '{captureDir}/{fileName}'. 'fileName'
        defaults to '{prefix}{timestamp}.{ext}'

        Taking screenshot image is delegate to asbtract
        'screenShotImplementation' -method, which sub classes should
        override.

        :captureDir: directory where screen shot is mage, defaults to
        'FLAGS.captureDir'

        :ext:  extension of the image file

        """
        if captureDir is None: captureDir = FLAGS.captureDir

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
        

    def instrumentValidate(self, value, validValues, context=None):
        """
        Validate 'value' is in 'validValues'

        :validValues: List or None
        """
        if validValues is not None and value not in validValues:
            msg = "{} > expecting one of {} - got '{}'".format( context, validValues, value  )
            logging.error( msg )
            raise MenuValueError(msg)
    
    def instrumentValUnit( self, valUnitStr, validValues:List[str]=None ):
        """Extract value and unit from 'valUnitStr' 
        
        Extract done using VAL_UNIT_REGEXP
        
        VAL_UNIT_REGEXP=r"(?P<value>-?[0-9\.]+)(?P<unit>[a-zA-Z%]+)"

        :valUnitStr: string from which to extrac valid value eg. 5V -> (5,V)

        :validValues: list of valid unit string

        :return: (val,unit)  E.g. "5V" -> ("5","V")

        """

        # Extract value/unit
        VAL_UNIT_REGEXP=r"(?P<value>[0-9-\.]+)(?P<unit>[a-zA-Z%]+)"
        match = re.search( VAL_UNIT_REGEXP, valUnitStr )
        if match is None:
            msg = "Could not extract unit value from '{}'".format( valUnitStr )
            logging.error(msg)
            raise MenuValueError(msg)
        (val,unit) = ( match.group('value'), match.group('unit') )

        # EbValidate - if validation requested
        self.instrumentValidate( value=unit, validValues=validValues, context=valUnitStr)
        
        return (val,unit)

    def instrumentAppendCvsFile( self, csvFile, measurementRow:dict ):
        """
        Append to FLAGS.csvDir/csvFile

        :csvFile: name of the file (within directory FLAGS.csvDir)

        :measurementRow: dict with keys in the format '<channel>:<measurement>'

        """
        appendCvsFile( csvFile=csvFile, measurementRow=measurementRow)
    

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

class MenuCtrl:

    # Well knonw menu items
    MENU_QUIT="q"             # quits loop
    MENU_REC_SAVE="."         # save recording
    MENU_REC_START="!"        # start/rerset recording
    MENU_SCREEN="screen"      # output screenshot
    MENU_HELP="?"             # list commands
    MENU_CMD_PARAM="??"       # DEPRACTED --> MENU_HELP_CMD
    MENU_HELP_CMD="??"        # help on command
    # Hidden commands
    MENU_VERSION="_version"   # output version number (hidden command)
    MENU_YAML="_yaml"         # output exxample _yaml
    MENU_LIST_RES="_list_resources" 

    

    # Menu tuples
    MENU_QUIT_TUPLE        = ( "Exit", None, None)
    MENU_VERSION_TUPLE     = ( "Output version number", None, version )
    MENU_YAML_TUPLE        = ( "Exaxample yaml", None, printExampleYaml)
    MENU_SEPATOR_TUPLE     = ( None, None, None)
    MENU_LIST_RES_TUPLE    = ( "List pyvisa resources (=pyvisa list_resources() wrapper)'", None, list_resources )


    # Parameters
    MENU_HELP_CMD_PARAM={
      "command": "Command to give help on (None: help on main menu)"
    }

    MENU_REC_SAVE_PARAM = {
         "fileName" : "Filename to save recording (.= show current recording)",
    }

    MENU_SCREENSHOT_PARAM = {
      'fileName'   :   "Screen capture file name (optional)",    
    }


    MENU_INSTRUMENT_ACCESS_PARAMS = {
        "apiCalls" : "JSON string { \"key\": \"instrument.method(commaSepListOfArgs)\"} "
    }

    # Prorites in subMenu dictionaries
    SUB_MENU_TYPE="type"                 # menu types (instrumentAccess, )
    SUB_MENU_PROMPT="prompt"             # Text to sub menu propmpt
    SUB_MENU_TYPE_SUB="subMenu"          # value in SUB_MENU_TYPE domain defining submenu
    SUB_MENU_TYPE_API="apiCall"          # value in SUB_MENU_TYPE domain defining API call
    SUB_MENU_MODULE="module"             # Python module name
    SUB_MENU_NAME="menu"                 # name to present in menu -structure
    SUB_MENU_PARAMS="kwargs"             # params passed to run
    SUB_MENU_API_CALLS="apiCalls"        # configure SUB_MENU_TYPE_API 
    SUB_MENU_MEASUREMENT="csvFile"       # configure SUB_MENU_TYPE_API, save to csvFile
    
    
    def __init__( self, args, prompt, instrument:Instrument = None, outputTemplate=None ):
        """:args: paramerter from command line, pgm name etc


        :prompt: prompt presented to user

        :instrument: instrument managerd by this menu (optional)

        :outputTemplate: None execute args/REPL responses, not None
        output (python API)

        """
        self.subMenuCtrls = {}
        self.instrument = instrument
        self.prompt = prompt
        self.outputTemplate = MenuCtrl.dispatchOutputTemplate(outputTemplate)
        if not self.isChildMenu:
            # top level menu created - recording started
            self.recording = []
        logging.info( "MenuCtrl: init, isChildMenu={}".format(self.isChildMenu))
        if self.isTopMenu:
            self.initArgs( args=args)

    def initArgs( self, args):
        """
        Init args (used only on top topMenu: only which receives args)

        :args: args[0] name of program starting/sub menuCommand

        """
        # Interactive receives only pgroramm name in _argv
        self.interactive = len(args) == 1
        self.pgm=args[0]
        logging.info( "Starting pgm={}, interactive={}".format(self.pgm, self.interactive))

        
        if self.interactive:
            self.cmds = None
        else:
            self.cmds = args[1:]
        
    def close(self):
        """Close menu. Calls self.instrument.close (if instrument is
        not None)
        """
        logging.info( "MenuCtrl: close called")
        # Close also sub menus
        for menu,menuCtrl in self.subMenuCtrls.items():
            logging.debug( "MenuCtrl: close subMenu={}".format(menu))
            if menuCtrl is not None: menuCtrl.close()
        self.subMenuCtrls = {}
        if self.instrument is not None:
            self.instrument.close()

    # ------------------------------
    # Properties

    @property
    def subMenuCtrls(self) -> dict :
        if not hasattr(self, "_subMenuCtrls"):
             return None
        return self._subMenuCtrls

    @subMenuCtrls.setter
    def subMenuCtrls( self, subMenuCtrls:dict):
        self._subMenuCtrls = subMenuCtrls

    def subMenuCtrl(self, name) -> "__class__" :
        return self.subMenuCtrls[name]
    
    def addsubMenuCtrl(self, name, subMenuCtrl:'__class__') :
        self.subMenuCtrls[name] = subMenuCtrl
    
    @property
    def recording(self) -> List[str] :
        if self.parentMenu is not None:
            return self.parentMenu.recording
        return self._recording

    @recording.setter
    def recording( self, recording:List[str]):
        self._recording = recording

    @property
    def parentMenu(self):
        """hierarchical menu structure, ref. recording
        """
        if not hasattr(self, "_parentMenu"):
             return None
        return self._parentMenu

    @parentMenu.setter
    def parentMenu( self, parentMenu):
        self._parentMenu = parentMenu

    @property        
    def isChildMenu( self ):
        return self.parentMenu is not None

    @property        
    def isTopMenu( self ):
        return not self.isChildMenu

    @property
    def instrument(self) -> Instrument:
        if not hasattr(self, "_instrument"):
             return None
        return self._instrument

    @instrument.setter
    def instrument( self, instrument:Instrument):
        self._instrument = instrument

    @property
    def cmds(self) -> str :
        if not hasattr(self, "_cmds"):
             return None
        return self._cmds

    @cmds.setter
    def cmds( self, cmds:str):
        self._cmds = cmds

    @property
    def interactive(self) -> bool :
        """Interactive: some command line parameters given?

        """
        if self.isChildMenu:
            return self.parentMenu.interactive
        if not hasattr(self, "_interactive"):
             return None
        return self._interactive

    @interactive.setter
    def interactive( self, interactive:bool):
        self._interactive = interactive

    @property
    def pgm(self) -> str :
        """First command line paramerter (from top-level menu)
        """
        if self.isChildMenu:
            return self.parentMenu.pgm
        if not hasattr(self, "_pgm"):
             return None
        return self._pgm

    @pgm.setter
    def pgm( self, pgm:str):
        self._pgm = pgm

    @property
    def cmds(self) -> List[str] :
        """Parameters"""
        if self.isChildMenu:
            return self.parentMenu.cmds
        if not hasattr(self, "_cmds"):
            return None
        return self._cmds

    @cmds.setter
    def cmds( self, cmds:List[str]):
        self._cmds = cmds

    @property
    def prompt(self) -> str :
        if not hasattr(self, "_prompt"):
             return None
        return self._prompt

    @prompt.setter
    def prompt( self, prompt:str):
        self._prompt = prompt


    @property
    def menu(self) -> Dict[str,List] :
        if not hasattr(self, "_menu"):
             return None
        return self._menu

    @menu.setter
    def menu( self, menu:Dict[str,List]):
        self._menu = menu


    @property
    def defaults(self) -> Dict[str,dict] :
        """Dictionary mappping menuCommand to
        menuCommandDefault. menuCommandDefault is a dict
        mapping. Parameter name to default value

        """
        if not hasattr(self, "_defaults"):
             return None
        return self._defaults

    @defaults.setter
    def defaults( self, defaults:Dict[str,dict]):
        self._defaults = defaults


    def setMenu( self, menu, defaults={}):
        self.menu = menu
        self.defaults = defaults

    @property
    def outputTemplate(self) -> str :
        """Defaults None: args/REPL responses are executed
        """
        if not hasattr(self, "_outputTemplate"):
            return None
        return self._outputTemplate

    @outputTemplate.setter
    def outputTemplate( self, outputTemplate:str):
        self._outputTemplate = outputTemplate



    
    # ------------------------------
    # Recording actions
    def startRecording(self):
        """@see module startRecording"""
        if self.isChildMenu:
            self.parentMenu.startRecording()
        else:
            self.recording = []
            # Recording actions not recorded
            raise MenuNoRecording

    def appendRecording( self, menuCommand:str, commandParameters:Dict[str,str]={}):
        """Append serialization of  'menuCommand' and 'commandParameters' to
        'recording' -array
        """
        logging.debug( "appendRecording: self.isChildMenu={}, menuCommand={}, commandParameters={}".format(self.isChildMenu, menuCommand,  commandParameters))
        if self.isChildMenu:
            logging.debug( "appendRecording: delegate to parentMenu, menuCommand={}".format(menuCommand))
            self.parentMenu.appendRecording( menuCommand=menuCommand, commandParameters=commandParameters)
        else:
            self.recording = self.recording + [menuCommand] + [ '{}="{}"'.format(k,v) for k,v in commandParameters.items() ]
            logging.debug( "appendRecording: {}".format(self.recording))

    def anyRecordings( self ) -> bool:
        """Recording status. True is something in recording bufffer"""
        if self.isChildMenu:
            return self.parentMenu.anyRecordings()
        else:
            return len(self.recording) > 0

    def pgmAndOptions(self)->str:
        """Return string which starts menuController.  For toplevel
        application is argv[0] + command line parameters, for sub menu
        it is the menu command used to enter sub menu.

        For options add $1, which maps to bash option paramter

        """
        # commandLineOptionsToInclude = ["syspath", "recordingDir"]
        # opts = [ '--{}="{}"'.format( opt, str(FLAGS[opt]))
        #          for opt in commandLineOptionsToInclude if opt in FLAGS ]
        return "{} {}".format(self.pgm, "$1" )
        
    def stopRecording(self, fileName =None, recordingDir=None ):
        """@see module function 'stopRecording'
        """
        if recordingDir is None: recordingDir = FLAGS.recordingDir
        if self.isChildMenu:
            self.parentMenu.stopRecording( pgm=self.pgm, fileName=fileName, recordingDir=recordingDir)
        else:
            logging.info( "stopRecording: {} to be into '{}'".format(self.recording,fileName))
            if not self.anyRecordings():
                print( "NO recordings to save")
                raise MenuNoRecording

            # Create recording line
            commandsAndParameters = " ".join( self.recording)
            pgm_commandsAndParameters = "{} {}".format(self.pgmAndOptions(), commandsAndParameters)

            # Show/save to file
            if fileName is None or not fileName or fileName == MenuCtrl.MENU_REC_SAVE:
                print(pgm_commandsAndParameters)
            else:
                if not os.path.exists( recordingDir):
                    raise MenuValueError( "Non existing recording directory: {}".format(recordingDir))
                filePath= os.path.join( recordingDir, fileName)
                if os.path.isdir( filePath ):
                    raise MenuValueError( "Recording path is directory: {}".format(filePath))
                with open( filePath, "a") as fh:
                    fh.write("{}\n".format(pgm_commandsAndParameters))
                self.startRecording()
            # Recording actions not recorded
            raise MenuNoRecording

    # ------------------------------
    # Construct submenu and use it 

    def registerSubMenus( self, subMenuDefs:List[Dict], defaults:dict={} ) -> Dict:
        """Create dictionary for defining 'subMenuDefs' in MenuCtr menu.
        regiterter . Register each entries 'subMenuDefs' so that they
        can be later called, when user chooses 'menuCommand' and
        return a
        

        :subMenuDefs: list of dicts with keys SUB_MENU_MODULE,
        SUB_MENU_NAME

        :self.subMenuCtrls: update dict mapping 'SUB_MENU_NAME' -> MenuCtrl

        :defaults: dictionary update if any of subMenuDefs use default
        parameters
        
        :return: dict mapping 'SUB_MENU_NAME' -> (menuPrompt,
        menuParameters, menuAction), @see mainMenu

        """

        def menuActionInvokeSubmenu( menuCommand, subMenuCtrl:"__class__" ) -> Callable:
            """Create lambda for 'menuAction'. Basically binds 'run' to co-operate
            with 'parentMenu'

            :menuCommand: Menu command invoking 'menuAction'

            :parentMenu: run co-operatater with 

            :return: menuAction -callable  to put into 'menuDict'

            """
            def subMenuAction():
                # Record before entring menu
                subMenuCtrl.parentMenu.appendRecording( menuCommand = menuCommand)
                subMenuCtrl.mainMenu()
                # Action is not recorded (recording was done before run)
                raise MenuNoRecording
            return subMenuAction


        def typeSubMenu( menuDict, menuDef, defaults):
            """Construct subMenu -type menu entry into 'menuDict' for 'menuDef'

            :return: updated menuDict

            """
            logging.debug( "typeSubMenu: menuDef={}".format(menuDef))
            
            menuCommand = menuDef[MenuCtrl.SUB_MENU_NAME]
            menuPrompt = menuDef[MenuCtrl.SUB_MENU_PROMPT]
            # optional kwargs
            kwArgs = {}
            if MenuCtrl.SUB_MENU_PARAMS in menuDef:
                kwArgs = menuDef[MenuCtrl.SUB_MENU_PARAMS]

            # Resolve module implementing subMenu
            subMenuModule = menuDef[MenuCtrl.SUB_MENU_MODULE]
            run = importlib.import_module( subMenuModule ).run

            # Construct hierarchical 'MenuCtrl' for sub-menu
            subMenuCtrl = run( [menuCommand], runMenu=False, **kwArgs )
            subMenuCtrl.parentMenu = self
            if subMenuCtrl is None:
                raise MenuValueError( "Submenu {} in module {} does not return MenuCtrl object ".format( menuCommand, subMenuModule))

            # Register subMenuCtrl for later use
            self.addsubMenuCtrl( menuCommand, subMenuCtrl )

            # and create menuAction to for the subMenu
            menuAction = menuActionInvokeSubmenu( menuCommand=menuCommand, subMenuCtrl=subMenuCtrl )
            menuParameters  = None
            menuDict[menuCommand] = (menuPrompt, menuParameters, menuAction)

            return menuDict

        def typeApi( menuDict, menuDef, defaults):
            """Construct menu entry for API calls 'menuDef' into 'menuDict'
            
            :menuDef: Prorperties SUB_MENU_NAME, SUB_MENU_API_CALLS,
            SUB_MENU_MEASUREMENT (optional)

            """
            logging.debug( "typeApi: menuDef={}".format(menuDef))
            menuCommand = menuDef[MenuCtrl.SUB_MENU_NAME]
            menuPrompt = menuDef[MenuCtrl.SUB_MENU_PROMPT]
            apiCalls = menuDef[MenuCtrl.SUB_MENU_API_CALLS]
            csvFile =  menuDef[MenuCtrl.SUB_MENU_MEASUREMENT] if MenuCtrl.SUB_MENU_MEASUREMENT in menuDef else None

            # menuAction lambda requiring parameters apiCalls and
            # csvFile (optional)
            menuActionRequiringParams = self.apiCallMenuAction()

            # bind parameters to values resolved here
            menuActionWithoutParams = lambda : menuActionRequiringParams(apiCalls=apiCalls, csvFile=csvFile)
            
            # Finally: create menuEntry
            menuDict[menuCommand] = (menuPrompt,None,menuActionWithoutParams)
            return menuDict

        # This is constructed
        menuDict = {}
        menuTypeDispatcher = {
            MenuCtrl.SUB_MENU_TYPE_API: typeApi,
            MenuCtrl.SUB_MENU_TYPE_SUB: typeSubMenu,
        }

        # Dispatch applicable method for each entry in 'subMenuDefs'
        for menuDef in subMenuDefs:
            # Extract from menuDef
            menuType  = menuDef[MenuCtrl.SUB_MENU_TYPE]
            try:
                menuTypeLambda = menuTypeDispatcher[menuType]
            except KeyError as err:
                msg = "Invalid 'type' {} in {}, valid types: {}. Error: {}".format(
                    menuType, menuDef, menuTypeDispatcher.keys(), str(err) )
                logging.error( msg )
                raise KeyError( msg )
            # Constructing 'menuDict'
            menuDict = menuTypeLambda(menuDict=menuDict, menuDef=menuDef, defaults=defaults)    

            
        return menuDict

    def apiCallMenuAction( self ):
        """Create menuAction -lambda for dispatching 'apiAccesses' on
        instruments wrapped by 'self.subMenuCtrls'. Lambda parameters
        given in 'MENU_INSTRUMENT_ACCESS_PARAMS'

        """
        def parseApiAccess(apiDef:str) -> Tuple[str,str,List[str]]:
            """Extract parts subMenuName.methodName(args) from apiDef:str

            :return: tuple (subMenuName, methodName, methodArgs)
            """
            INSTRUMENT_ACCESS_REGEXP =r"(?P<subMenuName>[^\.]+)\.(?P<methodName>[^\(]+)\((?P<args>.*)\)"
            match = re.search( INSTRUMENT_ACCESS_REGEXP, apiDef )
            if match is None:
                msg = "Could not extract subMenuName, methodName, methodArgs from '{}'".format( apiDef )
                logging.error(msg)
                raise MenuValueError(msg)
            logging.debug( "match['subMenuName']={}".format(match['subMenuName']))
            logging.debug( "match['methodName']={}".format(match['methodName']))
            logging.debug( "match['args']={}.".format(match['args']))
            (subMenuName, methodName) = (match['subMenuName'], match["methodName"] )
            argsStr =  match["args"].strip()
            # methodArgs = [] if len(commaSepList) == 0 else commaSepList.split(",")
            (args,kwargs) = parse_args( argsStr)
            logging.debug( "parse_args.args={}, parse_args..kwargs={}".format(args,kwargs))
            return (subMenuName, methodName, args, kwargs)

        def apiAccess(apiDef):
            """Dispatch API call in 'apiDef' using
            subMenuCtrl.callIntrumentMethodByName

            :return: value returned from the dispatched API

            """
            (subMenuName, methodName, methodArgs, methodKwargs) = parseApiAccess(apiDef)
            logging.debug( "subMenuName={}, methodName={}, methodArgs={}/{},methodKwargs={}".format(
                subMenuName, methodName, len(methodArgs), methodArgs, methodKwargs))
            retVal = self.subMenuCtrl(subMenuName).callIntrumentMethodByName(methodName, *methodArgs, **methodKwargs )
            return retVal

        def menuActionLambda( apiCalls:Union[str,dict]=None, csvFile:str = None ):
            """Parse json string :apiCalls: (unless it is already a dict mapping
            key 'apiDef'), parse API call in 'apiDef' and dispatch API
            call them using 'callIntrumentMethodByName'.


             'apiAccess' json string "{ key: subMenuName.methodName(args) }" OR dict
             { key: subMenuName.methodName(args) }

             - subMenuName (SUB_MENU_NAME) to locate subMenuCtrl

             - methodName is name of API method to invoke in
               'subMenuCtrl'

             - params is colon (:) sepated parameters to API method

            :return: csvPath (if csvFile given), apiResults (if
            csvFile not given)

            """
            logging.info( "menuActionLambda: apiCalls={}".format(apiCalls))
            if isinstance(apiCalls,str):
                apiCalls = json.loads(apiCalls)
            logging.debug( "apiCallMap: {}".format(apiCalls))
            apiResults = { k: apiAccess(apiDef) for k,apiDef in apiCalls.items() }
            logging.info( "apiResults:".format(apiResults))
            if csvFile is not None:
                csvPath = appendCvsFile( csvFile, apiResults )
                return csvPath
            else:
                return apiResults

        return menuActionLambda

    # ------------------------------
    # Dispatch output templateate
    OUTPUT_TEMPLATE_DISPATCHER= {
        OUTPUT_TEMPLATE_DEFAULT: OutputTemplateApi
    }

    def dispatchOutputTemplate( outputTemplate:str )->OutputTemplate:
        """Map 'outputTemplate' to class OutputTemplate 

        :outputTemplate: command line configuration

        :return: None if 'outputTemplate' is None else class
        'OutputTemplate'

        """
        logging.debug( "dispatchOutputTemplate: outputTemplate={}".format(outputTemplate))
        # cli options None --> no outputTemplate processing
        if outputTemplate is None: return None
        if outputTemplate in MenuCtrl.OUTPUT_TEMPLATE_DISPATCHER:
            templateInstance = MenuCtrl.OUTPUT_TEMPLATE_DISPATCHER[outputTemplate]()
            logging.info( "dispatchOutputTemplate: outputTemplate={} -> {}".format(outputTemplate, templateInstance) )
            return templateInstance
        else:
            raise ValueError( "Invalid outputTemplate {}, valid outputTemplates={}".format(
                outputTemplate, " ".join( MenuCtrl.OUTPUT_TEMPLATE_DISPATCHER.keys())))
        

     
    # ------------------------------
    # executing menu
    
    def promptValue( prompt:str, key:str=None, cmds:List[str]=None,
                     validValues:List[str]=None, defaultParameters:dict={}, promptIndentation="" ):
        """Three uses 1) prompt user for menuCommand, 2) prompt user for
        commandParameters, 3) ask user for measurement value

        :key: Lookding for key-value pair for commandParameters 

        :cmds: Command line parameters (in batch mode), which give
        values to promts (instead of asking user)

        :defaultParameters: dict->value, use 'key' to check if promted
        value has default value. If default value defined: update the
        prompted value to 'defaultParameters' --> it is rememeber for
        later invocations.

        :promptIndentation: sub menus prompts are intended

        """
        ans = None
        logging.debug( "promptValue: key={}, cmds={},".format(key,cmds))
        if cmds is None:
            # Interactive mode

            # default value modifies prompt
            if key in defaultParameters:
                # default value defined
                prompt = "{} ({})".format(prompt, defaultParameters[key])
            ans = input( "{}{} > ".format(promptIndentation,prompt))

            # after user answer check if default accepted/default should be changed
            if key in defaultParameters:
                if ans is None or not ans:
                    # Default value accepted
                   ans = defaultParameters[key]
                else:
                    # Default value to rememeber changed
                    defaultParameters[key] = ans
            ans = str(ans).strip()

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

    def mainMenu( self ):
        """For interactive usage, prompt user for menu command and command
        parameters, for command line usage parse commands and
        parameters from '_argv'. Invoke action for command.

        :self.cmds: command line paramaters (in batch mode)

        :self.menu: dict mapping menuCommand:str -> menuSelection =
        List[menuPrompt,parameterPrompt,menuAction], where
        - menuPrompt: string presented to user to query for
          'commandParameter' value
        - parameterPrompt: dict mapping 'commandParameter' name to
          commandParameter prompt
        - menuAction: function to call with 'commandParameters' (as
          **argv values prompted with parameterPrompt)

        :self.defaults: is dictionary mapping 'menuCommand' to
        'defaultParameters'.  If 'defaultParameters' for a
        'menuCommand' is found, it is used to lookup 'defaultValue'
        prompeted from user. Also, If 'defaultParameters' for a
        'menuCommand' is found, 'defaultParameters' is updated with
        the value user enters for the promt.

        """
        
        def execMenuCommand(mainMenu,menuCommand,defaults, promptIndentation,outputTemplate=None):
            # Extract mainMenu elements
            # :outputTemplate: execute 'menuCommand' if None, else format output using template
            menuSelection = mainMenu[menuCommand]

            # 'defaultParameters' may provide initial value 
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
                    k: MenuCtrl.promptValue(
                            v,key=k,
                            cmds=cmds,
                            defaultParameters=defaultParameters,
                            promptIndentation=promptIndentation)
                    for k,v in parameterPrompt.items()
                }

            if menuAction is not None:
                if not outputTemplate is None:
                    # Format output (to API)
                    logging.debug( "applyTemplate menuAction={}, with commandParameters={}".format( menuAction, commandParameters))
                    outputTemplate.applyTemplate( name=self.pgm, menuCommand=menuCommand, commandParameters=commandParameters)
                else:
                    # Normal execution
                    try:
                        # Call menu action (w. parameters)
                        logging.debug( "call menuAction={}, with commandParameters={}".format( menuAction, commandParameters))
                        returnVal = menuAction( **commandParameters )
                        self.appendRecording( menuCommand, commandParameters )
                        if returnVal is not None: # and interactive:
                            if isinstance(returnVal, str):
                                print(returnVal )
                            else:
                                print( pformat(returnVal) )
                    except MenuValueError as err:
                        if self.interactive:
                            # Interactive error - print erros msg && continue
                            print( "Error: {}".format(str(err)))
                        else:
                            raise
                    except MenuNoRecording:
                        # Help, start/stop recording commands
                        pass
                    except: #  Exception as err:
                        err = sys.exc_info()[0]
                        # In Interactive mode all errors are printed, user quits 
                        if self.interactive:
                            # Interactive error - print erros msg &&
                            # continue (debug print stacktrace)
                            print( "Error: {}".format(str(err)))
                            if logging.level_debug():
                                raise err
                        else:
                            raise err
                        
            return True

        promptIndentation = "" if self.isTopMenu else " "
        cmds  = self.cmds
        menu = self.menu
        defaults = self.defaults
        validMenuSelections = [ k for k in  menu.keys() if menu[k][0] is not None ]
        
        logging.info( "interactive: {} Starting cmds={}, isTopMenu={}".format(self.interactive, cmds, self.isTopMenu ))
        goon = True
        while goon:
            if not self.interactive and len(cmds) == 0:
                # all commands consumed - quit batch
                break
            menuCommand = MenuCtrl.promptValue(
                self.prompt
                , cmds=cmds
                , validValues=validMenuSelections
                , promptIndentation=promptIndentation )
                
            logging.debug( "Command '{}'".format(menuCommand))
            if menuCommand is None:
                continue
            elif menuCommand == MenuCtrl.MENU_QUIT:
                goon = False
                if self.isChildMenu:
                    # Main menu quit is not recorded (batch mode ends
                    # automagically when all input consume)
                    self.appendRecording( menuCommand )
            else:
                goon = execMenuCommand( menu, menuCommand,defaults
                                        , promptIndentation=promptIndentation , outputTemplate=self.outputTemplate)

        # Confirm whether save recording when exiting
        if self.anyRecordings() and self.interactive and MenuCtrl.MENU_REC_SAVE in menu and self.isTopMenu:
            print( "Save recordings?")
            execMenuCommand( menu, MenuCtrl.MENU_REC_SAVE,defaults
                             ,promptIndentation=promptIndentation, outputTemplate=self.outputTemplate)

    def callIntrumentMethodByName( self, name, *args, **kwargs):
        """Dispatch 'name' method on 'self.instrument' and pass to it
        arguments

        :return: value returned by 'name' -method

        """
        logging.info( "Dispach {}-method with args={}, kwargs={})".format(name, args, kwargs))
        return self.instrument.callByName( name, *args, **kwargs)


# ------------------------------------------------------------------
# Devices


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
            if PyInstrument._rm is not None: PyInstrument._rm.close()
            PyInstrument._rm = None
        except:
            logging.warn(  "Closing Resource manager {} - failed".format(PyInstrument._rm))


    # ------------------------------------------------------------------
    # construct && close
    
    def __init__( self, addr, debug = False ):
        super().__init__( debug=debug)
        logging.info( "Setting PyInstrument instrument in addr {}".format(addr))
        self.addr = addr
        # Lazy inialization (only when need) 
        self.instrument = None
        if debug:
            pyvisa.log_to_screen()

    def initInstrument( self ):
        """
        """
        if  self._instrument is not None:
            logging.warning( "PyInstrument instrument {} is already open".format(self.addr))
            return
        logging.info( "OPening PyInstrument instrument in addr {}".format(self.addr))
        try:
            self._instrument = PyInstrument.singleton_rm().open_resource(self.addr)
        except pyvisa.errors.VisaIOError as err:
            self._instrument = None
            logging.error(err)
        except ValueError as err:
            self._instrument = None
            logging.error(err)
        try:
            idn = self.instrument.query('*IDN?')
            logging.warning("Successfully connected  '{}' with '{}'".format(self.addr, idn))
        except:
            pass
            

        
    def close(self):
        if self.instrument is not None:
            logging.info( "Close instrument: {}".format(self.instrument))
            self.instrument.close()
            self.instrument = None
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

    @property
    def instrument(self):
        if self._instrument is None:
            self.initInstrument()
        return self._instrument

    @instrument.setter
    def instrument( self, instrument:str):
        self._instrument = instrument



    # ------------------------------------------------------------------
    # Low level communication
    def write(self, cmd ):
        logging.info( "write: {}".format(cmd))
        if self.instrument is not None:
            self.instrument.write(cmd)
        else:
            logging.error( "write '{}' failed - self.instrument is None".format(cmd))

    def write_raw( self, data):
        logging.info( "write_raw: {} bytes ".format(sys.getsizeof(data)))
        if self.instrument is not None:
            self.instrument.write_raw(data)
        else:
            logging.error( "write_raw '{}' bytes failed - self.instrument is None".format(sys.getsizeof(data)))

            
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
        # lazy init may open instrument at this point - do not remove
        self.instrument
        logging.info( "Reset instrument {}".format(self.instrument))
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
        
# ------------------------------------------------------------------
# Common menu actions

def appendCvsFile( csvFile, measurementRow:dict):
    """
    Append to FLAGS.csvDir/csvFile

    :csvFile: name of the file (within directory FLAGS.csvDir)

    :measurementRow: dict with keys in the format '<channel>:<measurement>'

    """
    csvDir = FLAGS.csvDir 
    filePath= os.path.join( csvDir, csvFile)

    # Exepct columns to be the same
    csv_columns = [Instrument.MEASUREMENT_TS ] + list(measurementRow.keys())
    if not os.path.exists( filePath):
        # Create CSV header
        with open( filePath, "w") as csvfile:
            writer = csv.DictWriter( csvfile, fieldnames=csv_columns)
            writer.writeheader()

    with open( filePath, "a") as csvfile:
        # Write datarow
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        measurementRow[Instrument.MEASUREMENT_TS] = datetime.now().strftime("%Y%m%d-%H%M%S")
        writer.writerow(measurementRow)

    return filePath



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


def menuStopRecording( menuController:MenuCtrl, recordingDir ):
    """Lambda function to use in mainMenu construct

    :recordingDir: directory where save, default FLAGS.recordingDir

    Usage example: 
      MenuCtrl.MENU_REC_SAVE   : 
       ( "Stop recording", stopRecordingPar, 
          menuStopRecording(menuController, recordingDir=FLAGS.recordingDir ) ),

    Document string in f is presented in help commands

    """
    def f(**argv):
        """Save current command recording history to 'fileName' in 'recordingDir'
        and clear command history.

        If no 'fileName' given, just print current command history
        (and do not clear command history)

        """
        return menuController.stopRecording(recordingDir=recordingDir, **argv )
    return f

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


# https://stackoverflow.com/questions/49723047/parsing-a-string-as-a-python-argument-list
def parse_args(args):
    args = 'f({})'.format(args)
    tree = ast.parse(args)
    funccall = tree.body[0].value

    args = [ast.literal_eval(arg) for arg in funccall.args]
    kwargs = {arg.arg: ast.literal_eval(arg.value) for arg in funccall.keywords}
    return args, kwargs    

