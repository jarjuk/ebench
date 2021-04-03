#!/usr/bin/env python3
import ebench
from ebench import MenuCtrl



import os
from absl import app, flags, logging
from absl.flags import FLAGS

def hello( whom:str ):
    print( "Hello {}".format(whom))

helloPar = {
   "whom": "Whom to greet?"
}


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

    cmdController.mainMenu( _argv, mainMenu=mainMenu, mainPrompt="[hello, q=quit]")






def main():
    try:
        app.run(_main)
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
