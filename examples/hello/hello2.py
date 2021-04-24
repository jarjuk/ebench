#!/usr/bin/env python3
from ebench import MenuCtrl
from ebench import Instrument

from ebench import usage, usageCommand, version

import os
from absl import app, flags, logging
from absl.flags import FLAGS

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

      It receives to parameters 'whom' and 'who' and prints
      greeting. Defaulta value of 'who' parameter is logged user, and
      its value is remembered between hello commands

      Returns greeted 'whom' if greeter/who is not the same as
      greeted/whom.

      Incrementing greetCount demonstrates that Intrument MAY
      maintain internal state.

      """
      self._greetCount = self._greetCount + 1
      print( "Hello #{} to {} from {}".format(self._greetCount, whom, who))

# --------------------------------------
# Menu interagration

helloPar = {
   "whom": "Whom to greet?",
   "who":  "Who is the greeter? Ret accepts default value: ",
}


defaults = {
"hello" : {
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

"""



# --------------------------------------
# Application main && ebMenu integration


def run( _argv, runMenu:bool = True, greetCount = 0  ):
     hello = HelloInstrument( greetCount = greetCount )

     mainMenu = {
     
         # First section: application commands
         "Commands:"              : ( None, None, None),
         "hello"                  : ( "Say hello", helloPar, hello.sayHello ),
     
         # Second section: getting help
         "Help:"                  : ( None, None, None),
         MenuCtrl.MENU_HELP       : ( "List commands", None,
                                    lambda : usage(cmd=os.path.basename(__file__)
                                                         , mainMenu=mainMenu
                                                         , synopsis="Demo hello v2"
                                                         , usageText=usageText )),
         MenuCtrl.MENU_CMD_PARAM  : ( "List command parameters", MenuCtrl.MENU_HELP_CMD_PARAM,
                                    lambda **argV: usageCommand(mainMenu=mainMenu, **argV)),
         "_version"               : ("Version number", None, lambda **argv: print(version())),
     
         # Third section: exiting
         "Exit:"                  : ( None, None, None),
         MenuCtrl.MENU_QUIT       : ("Exit", None, None),
     
     }
     

     menuController = MenuCtrl(args=_argv,prompt="[hello, q=quit]", instrument=hello )
     menuController.setMenu(menu=mainMenu, defaults=defaults)
     if runMenu: menuController.mainMenu()

     return menuController

def _main( _argv ):
     # global gSkooppi
    logging.set_verbosity(FLAGS.debug)
    menuController = run( _argv )
    menuController.close()


def main():
    try:
        app.run(_main)
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
