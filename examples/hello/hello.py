#!/usr/bin/env python3
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
    MenuCtrl.MENU_QUIT      : MenuCtrl.MENU_QUIT_TUPLE,
}

def _main( _argv ):
    # configure logger
    logging.set_verbosity(FLAGS.debug)

    # Construct 'menuController' 
    menuController = MenuCtrl(args=_argv,prompt="[hello, q=quit]")

    # and configure menu
    menuController.setMenu(mainMenu)

    # start executing
    menuController.mainMenu()


def main():
    try:
        app.run(_main)
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
