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
    "hello"                 : ( "Say hello", helloPar, hello),
    MenuCtrl.MENU_QUIT      : ( "Exit", None, None),
}

def run( _argv):
    cmdController = MenuCtrl()

    cmdController.mainMenu( _argv, mainMenu=mainMenu, mainPrompt="[hello, q=quit]")

def _main( _argv ):
    # global gSkooppi
    logging.set_verbosity(FLAGS.debug)
    run( _argv)






def main():
    try:
        app.run(_main)
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
