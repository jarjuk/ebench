from ebench import MenuCtrl

from ebench import Instrument

from ebench import usage, usageCommand
from ebench import version
from ebench import menuStartRecording, menuStopRecording


import os

# --------------------------------------
# Example instrument "HelloInstrument"

class HelloInstrument(Instrument):
  """HelloInstrument class defines method 'greet', which made available
  as a menu command.

  """

  def hello( self, whom:str, who:str ) -> str:
      """Format string for greet"""
      return  "HELLO: '{}' FROM: '{}'".format(whom, who)

  def greet( self, whom:str, who:str ):
      print(self.hello( whom=whom, who=who ) )

# --------------------------------------
# Menu interagration

greetPar = {
   "whom": "Whom to greet?",
   "who":  "Who is the greeter? Ret accepts default value: ",
}

usageText = """
Demostrage gentle slope to bride gap between

      interactive-CLI-yaml-API

usage
"""

# --------------------------------------
# Application run && ebMenu integration

def run( _argv, runMenu:bool = True, outputTemplate:str = None, recordingDir=None  ):

     helloController = HelloInstrument()
     menuController = MenuCtrl( args=_argv, prompt="[?=help,q=quit]"
                   , instrument=helloController, outputTemplate=outputTemplate )

     mainMenu = {
         # First section: application commands
         "Commands:"              : MenuCtrl.MENU_SEPATOR_TUPLE,
         "greet"                  : ( "Say hello", greetPar, helloController.greet ),


         # Second section: recording
         "Recording:"             : MenuCtrl.MENU_SEPATOR_TUPLE,
         MenuCtrl.MENU_REC_START  : ( "Start recording", None, menuStartRecording(menuController) ),
         MenuCtrl.MENU_REC_SAVE   : ( "Stop recording", MenuCtrl.MENU_REC_SAVE_PARAM,
                                     menuStopRecording(menuController, recordingDir=recordingDir) ),

         # Third section: help
         "Help:"                  : MenuCtrl.MENU_SEPATOR_TUPLE,
         MenuCtrl.MENU_HELP       : ( "List commands", None,
                                    lambda : usage(cmd=os.path.basename(__file__)
                                                         , mainMenu=mainMenu
                                                         , synopsis="Demo hello v2"
                                                         , usageText=usageText )),
         MenuCtrl.MENU_CMD_PARAM  : ( "List command parameters", MenuCtrl.MENU_HELP_CMD_PARAM,
                                    lambda **argV: usageCommand(mainMenu=mainMenu, **argV)),

         # Fourth section: exiting
         "Exit:"                  : MenuCtrl.MENU_SEPATOR_TUPLE,
         MenuCtrl.MENU_QUIT       : MenuCtrl.MENU_QUIT_TUPLE,

         # Hidden
         MenuCtrl.MENU_VERSION    : MenuCtrl.MENU_VERSION_TUPLE,
     }

     menuController.setMenu(menu=mainMenu)
     if runMenu: menuController.mainMenu()

     return menuController
