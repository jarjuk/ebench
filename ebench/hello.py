#!/usr/bin/env python3

from ebench import MenuCtrl, Instrument
from absl import app, logging
from absl.flags import FLAGS


class HelloIntrument(Instrument):

    def __init__( self):
        self.cnt=0

    @property
    def cnt(self) -> int :
        if not hasattr(self, "_cnt"):
             return None
        return self._cnt

    @cnt.setter
    def cnt( self, cnt:int):
        self._cnt = cnt




    def greet( self, whom:str ):
        self.cnt = self.cnt + 1
        print( "Hello {}".format(whom, self.cnt))

    def greetCount(self) -> int:
        return self.cnt
    
    def greetCount2(self, added) -> int:
        return self.cnt + int(added)

            
    def close( self ):
        super().close()
        self.cnt = 0

helloPar = {
    "whom" : "ketä moikataa?",
}
        
def run( _argv, runMenu:bool= True, initCount = None ):

    logging.info( "create hello")
    hello = HelloIntrument()
    if initCount is not None:
        hello.cnt = int(initCount)
    
    mainMenu = {
        "hello"                 : ( "Say hello", helloPar, hello.greet),
        MenuCtrl.MENU_QUIT      : ( "Exit", None, None),
    }

    cmdController = MenuCtrl(args=_argv, instrument=hello, prompt="[hello, q=quit]")
    cmdController.setMenu( menu = mainMenu )

    if runMenu: cmdController.mainMenu()
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
