#!/usr/bin/env python3
import ebench
from ebench import MenuCtrl

import hello

import os
from absl import app, flags, logging
from absl.flags import FLAGS


def hello1():
    hello.main()

def hello2():
    hello.main()



mainMenu = {
    "hello1"                 : ( "Start hello1", None, hello1),
    "hello2"                 : ( "Start hello2", None, hello2),
    MenuCtrl.MENU_QUIT      : ( "Exit", None, None),
}

def _main( _argv ):
    logging.set_verbosity(FLAGS.debug)

    cmdController = MenuCtrl()

    cmdController.mainMenu( _argv, mainMenu=mainMenu, mainPrompt="[hello1,hello2, q=quit]")





def main():
    try:
        app.run(_main)
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
