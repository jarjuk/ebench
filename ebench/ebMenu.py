#!/usr/bin/env python3
from .ebench import MenuCtrl

# Menuactions
from .ebench import usage, usageCommand, menuStartRecording, menuStopRecording

from . import hello

from absl import app, logging
from absl.flags import FLAGS

# ------------------------------------------------------------------
# Load dynamically 
# TODO: load from configs


CMD="ebMenu"

# ------------------------------------------------------------------
# Menu actions

    
MENU_HELLO1= "hello1"
MENU_HELLO_MENU= "hello2"

helloPar = {
    "whom": "Whom to greet?",
}

measurePar = {
   "measurements": "Comma serated list of measurements"    
}


stopRecordingPar = {
    "fileName" : "Filename to store recording, '.' show current playback list",
}

defaults = {
    MENU_HELLO1 : { "whom" : "world"},
    MenuCtrl.MENU_REC_SAVE: { "fileName": "apu.sh"},
}

# ------------------------------------------------------------------
subMenuDefs = [
    {
        MenuCtrl.SUB_MENU_MODULE: "ebench.hello",
        MenuCtrl.SUB_MENU_NAME: MENU_HELLO_MENU,
        MenuCtrl.SUB_MENU_PARAMS: { "initCount": "62"},
        
    },
    # {
    #     MenuCtrl.SUB_MENU_MODULE: "ebench.ebRigol",
    #     MenuCtrl.SUB_MENU_NAME: "Rigol",
    #     MenuCtrl.SUB_MENU_PARAMS: { "ip": "skooppi"},
    # },
    # {
    #     MenuCtrl.SUB_MENU_MODULE: "ebench.ebUnit",
    #     MenuCtrl.SUB_MENU_NAME: "UTG962",
    #     MenuCtrl.SUB_MENU_PARAMS: { "addr": "USB0::0x6656::0x0834::1485061822::INSTR"},
    # },
    
]



# ------------------------------------------------------------------
# Menu actions
def hello1( whom:str ):
    print( "Hello {}!".format(whom))




# ------------------------------------------------------------------
# Main && run 

def run( _argv, parentMenu:MenuCtrl=None):

    cmdController = MenuCtrl( args=_argv, prompt="[?=help, q=quit]" )

    subMenus = cmdController.registerSubMenus(subMenuDefs=subMenuDefs)

    mainMenu = subMenus | {
        MENU_HELLO1              : ( "Start hello1", helloPar, hello1),
        # MENU_HELLO_MENU          : ( "Start sub menu", None, subMenu( command=MENU_HELLO_MENU, parentMenu=cmdController, run=hello.run ) ),
        MenuCtrl.MENU_QUIT       : ( "Exit", None, None),
        "Measurements"           : ( None, None, None ),
        "measure"                : ( "Measure", MenuCtrl.MENU_INSTRUMENT_ACCESS_PARAMS, cmdController.intrumentAccessMenuAction()),
        "Other"                  : ( None, None, None ),
        MenuCtrl.MENU_HELP       : ( "List commands", None,
                                    lambda **argV: usage(cmd=CMD, mainMenu=mainMenu, synopsis="Tool to control Rigol MSO1104Z osciloscope")),
        MenuCtrl.MENU_HELP_CMD   : ( "List command parameters", MenuCtrl.MENU_HELP_CMD_PARAM,
                                 lambda **argV: usageCommand(mainMenu=mainMenu, **argV )),

        MenuCtrl.MENU_REC_START  : ( "Start recording", None, menuStartRecording(cmdController) ),
        MenuCtrl.MENU_REC_SAVE   : ( "Stop recording", stopRecordingPar, menuStopRecording(cmdController, pgm=_argv[0], fileDir=FLAGS.recordingDir) ),        

        
    }

    cmdController.setMenu( menu = mainMenu, defaults = defaults)
    # Exec it 
    cmdController.mainMenu()
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
