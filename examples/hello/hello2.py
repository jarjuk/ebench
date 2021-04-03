#!/usr/bin/env python3
import ebench
from ebench import MenuCtrl



from ebench import usage, usageCommand

import os
from absl import app, flags, logging
from absl.flags import FLAGS

def hello( whom:str, who:str ):
    """Hello -command just demonstrates simple menu action.

    It receives to parameters 'whom' and 'who' and prints
    greeting. Defaulta value of 'who' parameter is logged user,
    and its value is remembered between hello commands

    Returns greeted 'whom' if greeter/who is not the same as
    greeted/whom.

    Notice, how

    """
    print( "Hello {} from {}".format(whom, who))
    return whom if who != whom else None

helloPar = {
   "whom": "Whom to greet?",
   "who":  "Who is the greeter? Ret accepts default value: ",
}


defaults = {
"hello" : {
             "who": os.getlogin()
          }
}



helpPar = {
      "command": "Command to give help on (None: help on main menu)"
}



usageText = """

This demo presents:

- command 'hello'  acceting two parameters, one of the parameters (whom) is
  prompted for every command call, the other paremeter (who) defaults to 
  to login-name, and its value is rememebered from previous call

- menu separator

- help to list command

- help on command parameters

- hidden command: _version


"""




mainMenu = {
    "hello"             : ( "Say hello", helloPar, hello),
    MenuCtrl.MENU_QUIT       : ( "Exit", None, None),
}



mainMenu = {
    "Commands:"              : ( None, None, None),
    "hello"                  : ( "Say hello", helloPar, hello),
    "Help:"                  : ( None, None, None),
    MenuCtrl.MENU_HELP       : ( "List commands", None,
                               lambda **argV: usage(cmd=os.path.basename(__file__), mainMenu=mainMenu, synopsis="Demo hello v2", usageText=usageText )),
    MenuCtrl.MENU_CMD_PARAM  : ( "List command parameters", helpPar,
                               lambda **argV: usageCommand(mainMenu=mainMenu, **argV)),
    "_version"               : ("Version number", None, lambda **argv: print( ebench.version())),
    "Exit:"                  : ( None, None, None),
    MenuCtrl.MENU_QUIT       : ("Exit", None, None),

}



def _main( _argv ):
    # global gSkooppi
    logging.set_verbosity(FLAGS.debug)

    cmdController = MenuCtrl()

    cmdController.mainMenu( _argv, mainMenu=mainMenu, mainPrompt="[hello, q=quit]", defaults=defaults)





def main():
    try:
        app.run(_main)
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
