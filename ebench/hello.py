#!/usr/bin/env python3

from ebench import MenuCtrl, Instrument
from absl import app, logging
from absl.flags import FLAGS


class HelloIntrument(Instrument):

    def __init__( self):
        self.cnt=0

    def greet( self, whom:str ):
        self.cnt = self.cnt + 1
        print( "Hello {}".format(whom, self.cnt))

    def close( self ):
        super().close()
        self.cnt = 0

helloPar = {
    "whom" : "ketä moikataa?",
}
        
def run( _argv, parentMenu:MenuCtrl = None ):

    logging.info( "create hello")
    hello = HelloIntrument()
    
    mainMenu = {
        "hello"                 : ( "Say hello", helloPar, hello.greet),
        MenuCtrl.MENU_QUIT      : ( "Exit", None, None),
    }
    cmdController = MenuCtrl(args=_argv, instrument=hello
                             , parentMenu=parentMenu, prompt="[hello, q=quit]")

    cmdController.mainMenu( mainMenu=mainMenu)
    return cmdController

def _main( _argv ):
    # global gSkooppi
    logging.set_verbosity(FLAGS.debug)
    run(_argv)


def main():
    try:
        app.run(_main)
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
