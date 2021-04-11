#!/usr/bin/env python3
from ebench import MenuCtrl, usage, usageCommand, menuStartRecording, menuStopRecording

import hello

from absl import app, logging
from absl.flags import FLAGS

CMD="ebMenu"

def helloMenu( parentMenu ):
    logging.info( "hello menustart")
    hello.run( _argv = None, parentMenu=parentMenu )

    
def hello1( whom:str ):
    print( "Hello {}!".format(whom))

MENU_HELLO1= "hello1"
MENU_HELLO_MENU= "hello2"    
helloPar = {
    "whom": "Whom to greet?",
}

helpPar = {
      "command": "Command to give help on (None: help on main menu)"
}

defaults = {
    MENU_HELLO1 : { "whom" : "world"}
}

stopRecordingPar = {
    "fileName" : "Filename to store recording, '.' show current playback list",
}



def run( _argv, parentMenu:MenuCtrl=None):

    cmdController = MenuCtrl()


    mainMenu = {
        MENU_HELLO1              : ( "Start hello1", helloPar, hello1),
        MENU_HELLO_MENU          : ( "Start menu", None, lambda : helloMenu(parentMenu=cmdController) ),
        MenuCtrl.MENU_QUIT       : ( "Exit", None, None),
        MenuCtrl.MENU_HELP       : ( "List commands", None,
                                    lambda **argV: usage(cmd=CMD, mainMenu=mainMenu, synopsis="Tool to control Rigol MSO1104Z osciloscope")),
        MenuCtrl.MENU_CMD_PARAM  : ( "List command parameters", helpPar,
                                 lambda **argV: usageCommand(mainMenu=mainMenu, **argV )),

        MenuCtrl.MENU_REC_START  : ( "Start recording", None, menuStartRecording(cmdController) ),
        MenuCtrl.MENU_REC_SAVE   : ( "Stop recording", stopRecordingPar, menuStopRecording(cmdController, pgm=_argv[0], fileDir=FLAGS.recordingDir) ),        
        
    }

    cmdController.mainMenu( _argv, mainMenu=mainMenu, mainPrompt="[?=help, q=quit]", defaults=defaults)
    if cmdController.isTopMenu:
        # Top level closes instruments && cleanup
        cmdController.close()
        cmdController = None

    return cmdController
    

    

def _main( _argv ):
    logging.set_verbosity(FLAGS.debug)
    run( _argv)
    




def main():
    try:
        app.run(_main)
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
