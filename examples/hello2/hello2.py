from ebench import MenuCtrl

from ebench import Instrument

from ebench import usage, usageCommand, version

import os

# --------------------------------------
# Example instrument "HelloInstrument"

class HelloInstrument(Instrument):

  def __init__(self, greetCount=0):
      self._greetCount = greetCount

  def greetCount(self, fake=0 ):
      """Access object state variable with API twist

      :fake: parameter used to demonstrate passing literal parameter
      value in API call

      :return: current 'greetCount' + 'fake'

      """

      return self._greetCount + int(fake)

  def sayHello( self, whom:str, who:str ):
      """Hello -command just demonstrates simple menu action.

      It receives to parameters 'whom' and 'who' and prints greeting
      and increments 'greetCount' (just to demonstrate that Intrument
      MAY maintain internal state).


      :who: default value is of 'who' parameter is logged in user, its
      value is remembered between greetings

      :whom: object to be greeted

      """
      self._greetCount = self._greetCount + 1
      print( "Hello #{} to {} from {}".format(self._greetCount, whom, who))

# --------------------------------------
# Menu interagration

greetPar = {
   "whom": "Whom to greet?",
   "who":  "Who is the greeter? Ret accepts default value: ",
}


defaults = {
"greet" : {
             "who": os.environ['USER']
          }
}




usageText = """

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



# --------------------------------------
# Application run && ebMenu integration


def run( _argv, runMenu:bool = True, greetCount = 0, outputTemplate:str = None  ):
     """Run hello2 as a standalone interactive or CLI application with the
     proviso to integrate 'hello2' with ~ebench.ebMenu~ tool.

     :_argv: list of command line arguments. In interactive mode, this
     is just the name of script. In CLI mode, name is followed by
     command line arguments

     :runMenu: defaults True = running standalone application. ebMenu
     sets this to 'False'.

     :greetCount: In this contrived example, 'greetCount' is the
     number greetings already made. It is passed to 'HelloInstrument'
     -constructor. For real world use, 'greetCount' represents
     parameters needed in instruments constructor.

     :outputTemplate: controls how '_argv'/REPL input in processed,
     default None: they are executed, any other value is mapped to
     template to produce API reprensentation of menu actions. Here
     just pass it trough.

     """
     helloController = HelloInstrument( greetCount = greetCount )

     mainMenu = {
     
         # First section: application commands
         "Commands:"              : MenuCtrl.MENU_SEPATOR_TUPLE,
         "greet"                  : ( "Say hello", greetPar, helloController.sayHello ),
     
         # Second section: getting help
         "Help:"                  : MenuCtrl.MENU_SEPATOR_TUPLE,
         MenuCtrl.MENU_HELP       : ( "List commands", None,
                                    lambda : usage(cmd=os.path.basename(__file__)
                                                         , mainMenu=mainMenu
                                                         , synopsis="Demo hello v2"
                                                         , usageText=usageText )),
         MenuCtrl.MENU_CMD_PARAM  : ( "List command parameters", MenuCtrl.MENU_HELP_CMD_PARAM,
                                    lambda **argV: usageCommand(mainMenu=mainMenu, **argV)),
     
         # Third section: exiting
         "Exit:"                  : MenuCtrl.MENU_SEPATOR_TUPLE,
         MenuCtrl.MENU_QUIT       : MenuCtrl.MENU_QUIT_TUPLE,
     
         # Hidden
         "_version"               : ("Version number", None, lambda **argv: print(version())),
         # Line above makes following line visible
         # MenuCtrl.MENU_VERSION    : MenuCtrl.MENU_VERSION_TUPLE,
     }
     

     menuController = MenuCtrl( args=_argv
                        , prompt="[hello, q=quit]"
                        , instrument=helloController
                        , outputTemplate=outputTemplate )
     menuController.setMenu(menu=mainMenu, defaults=defaults)
     if runMenu: menuController.mainMenu()

     return menuController
