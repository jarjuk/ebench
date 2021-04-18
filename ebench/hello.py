#!/usr/bin/env python3

from ebench import MenuCtrl, Instrument
from absl import app, logging
from absl.flags import FLAGS


class HelloIntrument(Instrument):

    def __init__( self, greetCount=0):
        self.greetCnt=greetCount


    def greet( self, whom:str ):
        self.greetCnt = self.greetCnt + 1
        print( "Hello  {} {}".format(self.greetCnt, whom ))

    def greetCount(self) -> int:
        return self.greetCnt
    
    def greetCount2(self, added) -> int:
        return self.greetCnt + int(added)

            
    def close( self ):
        super().close()
        self.greetCnt = 0

helloPar = {
    "whom" : "ketä moikataa?",
}
        
def run( _argv, runMenu:bool= True, greetCount = 0 ):

    logging.info( "create hello")
    hello = HelloIntrument( )
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
