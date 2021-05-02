# Tangled from TEMPLATE.org - changes will be overridden


from ebench import Instrument
from ebench import MenuCtrl

from ebench import usage, usageCommand, menuStartRecording, menuStopRecording, menuScreenShot, version

import os
from time import sleep
from absl import logging


# ------------------------------------------------------------------
# Usage 
CMD="hello2"

SYNOPSIS="Hello -command just demonstrates simple menu action"

USAGE_TEXT = """

This demo presents:

 - maintaining instrument state: counting number of greetings made

 - command 'hello' accepting two parameters, one of the parameters
   (whom) is prompted for every command call, the other paremeter (who)
   defaults to to login-name, and its value is rememebered from
   previous call

 - menu separator

 - help to list command (and to show this text)

 - more detailed help on menu commands

 - hidden command: _version

 - proviso for integrating ~hello2~ with ebMenu

"""

# ------------------------------------------------------------------
# Acces instrument API
class HelloApi(Instrument):

  def __init__(self, greetCount=0):
      self._greetCount = greetCount

  def greetCount(self, fake=0 ):
      """Access object state variable with API twist

      :fake: parameter used to demonstrate passing literal parameter
      value in API call

      :return: current 'greetCount' + 'fake'

      """

      return self._greetCount + int(fake)

  def greetDone(self):
      self._greetCount = self._greetCount + 1



# ------------------------------------------------------------------
# Facade presented to user
class HelloInstrument(HelloApi):

  def __init__(self, greetCount=0):
      super().__init__(greetCount)

  def sayHello( self, whom:str, who:str ):
      """Hello -command just demonstrates simple menu action.

      It receives to parameters 'whom' and 'who' and prints greeting
      and increments 'greetCount' (just to demonstrate that Intrument
      MAY maintain internal state).


      :who: default value is of 'who' parameter is logged in user, its
      value is remembered between greetings

      :whom: object to be greeted

      """
      self.greetDone()
      print( "Hello #{} to {} from {}".format(self._greetCount, whom, who))


# ------------------------------------------------------------------
# Menu

# Menu commands 
CMD_GREET = "greet"


# Parameters to menu command CMD_GREET
greetPar = {
    "whom": "Whom to greet?",
    "who":  "Who is the greeter? Ret accepts default value: ",
}

# Initial values for menu command parameters
defaults = {
    CMD_GREET : {
        "who": os.environ['USER']
    }
}

# ------------------------------------------------------------------
# Bind instrument controller classes to ebench toolset
def run( _argv, greetCount=None
     , runMenu:bool = True
     , outputTemplate=None, captureDir=None, recordingDir=None ):
    """Examaple template 

    :runMenu: default True, standalone application call REPL-loop
    'menuController.mainMenu()', subMenu constructs 'menuController'
    without executing the loop

    :outputTemplate: if None(default): execute cmds/args, else (not
    None): map menu actions to strings using 'outputTemplate'

    :recordingDir: directory where interactive session recordings are
    saved to (defaults to 'FLAGS.recordingDir')

    :captureDir: directory where screenshots are made, defaults to
    'FLAGS.captureDir'

    :return: MenuCtrl (wrapping instrument)

    """

    # 'instrument' controlled by application 
    instrument = HelloInstrument(greetCount=greetCount) 

    # Wrap instrument with 'MenuCtrl'
    menuController = MenuCtrl( args=_argv,instrument=instrument
                             , prompt="[q=quit,?=commands,??=help on command]"
                             , outputTemplate=outputTemplate )

    mainMenu = {
        CMD                      : MenuCtrl.MENU_SEPATOR_TUPLE,
        # Application menu 
        CMD_GREET                : ( "Say hello", greetPar, instrument.sayHello ),

        "Util"                   : MenuCtrl.MENU_SEPATOR_TUPLE,
        MenuCtrl.MENU_REC_START  : ( "Start recording", None, menuStartRecording(menuController) ),
        MenuCtrl.MENU_REC_SAVE   : ( "Stop recording", MenuCtrl.MENU_REC_SAVE_PARAM, menuStopRecording(menuController, recordingDir=recordingDir) ),
        MenuCtrl.MENU_SCREEN     : ( "Take screenshot", MenuCtrl.MENU_SCREENSHOT_PARAM,
                                     menuScreenShot(instrument=instrument,captureDir=captureDir,prefix="Capture-" )),
        MenuCtrl.MENU_HELP       : ( "List commands", None,
                                    lambda **argV: usage(cmd=CMD, mainMenu=mainMenu, synopsis=SYNOPSIS, usageText=USAGE_TEXT)),
        MenuCtrl.MENU_HELP_CMD   : ( "List command parameters", MenuCtrl.MENU_HELP_CMD_PARAM,
                                 lambda **argV: usageCommand(mainMenu=mainMenu, **argV )),

        "Quit"                   : MenuCtrl.MENU_SEPATOR_TUPLE,
        MenuCtrl.MENU_QUIT       : MenuCtrl.MENU_QUIT_TUPLE,

        # Hidden commands
        MenuCtrl.MENU_VERSION    : ( "Output version number", None, version ),
    }

    menuController.setMenu( menu = mainMenu, defaults = defaults)

    # Interactive use starts REPL-loop
    if runMenu: menuController.mainMenu()

    # menuController.close() call after returning from run()
    return menuController
