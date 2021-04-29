#!/usr/bin/env python3
from .ebench import MenuCtrl

# Menuactions
from .ebench import usage, usageCommand, menuStartRecording, menuStopRecording, list_resources


import yaml
import sys
import os
from absl import app, flags, logging
from absl.flags import FLAGS

flags.DEFINE_string('config', None, "Path configuration yaml file")
flags.DEFINE_string('syspath', None, "Append to syspath")


# ------------------------------------------------------------------
# Load dynamically 
# TODO: load from configs


CMD="ebMenu"
SYNOPSIS="Menu of ebench toolset"

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
# Main && run 

def run( _argv, parentMenu:MenuCtrl=None, config=None, outputTemplate=None, captureDir=None, recordingDir=None ):
    """
    :outputTemplate: CLI configuration, None(default): =execute
    cmds/args, not None: map menu actions to strings using
    'outputTemplate',

    """

    def loadsubMenuDefs(config):
        subMenuDefs = []
        if config is not None:
            with open( config, "r") as y:
                subMenuDefs = yaml.safe_load(y)
        else:
            pkgDefault = os.path.join( os.path.dirname(__file__), "ebMenu.yaml")
            logging.info("loadsubMenuDefs: config was none loading pkgDefault={}".format(pkgDefault))
            if os.path.exists( pkgDefault ):
               with open( pkgDefault, "r") as y:
                   subMenuDefs = yaml.safe_load(y)
        return subMenuDefs

    menuController = MenuCtrl( args=_argv, prompt="[?=help, q=quit]", outputTemplate=outputTemplate,  )

    # Load submenus con ebMenu.yaml?
    subMenuDefs = loadsubMenuDefs(config=config)

    subMenus = menuController.registerSubMenus(subMenuDefs=subMenuDefs)

    mainMenu = subMenus | {
        # MENU_HELLO_MENU          : ( "Start sub menu", None, subMenu( command=MENU_HELLO_MENU, parentMenu=menuController, run=hello.run ) ),
        MenuCtrl.MENU_QUIT       : ( "Exit", None, None),
        "Other"                  : ( None, None, None ),
        MenuCtrl.MENU_HELP       : ( "List commands", None,
                                    lambda **argV: usage(cmd=CMD, mainMenu=mainMenu, synopsis=SYNOPSIS)),
        MenuCtrl.MENU_HELP_CMD   : ( "List command parameters", MenuCtrl.MENU_HELP_CMD_PARAM,
                                 lambda **argV: usageCommand(mainMenu=mainMenu, **argV )),

        MenuCtrl.MENU_REC_START  : ( "Start recording", None, menuStartRecording(menuController) ),
        MenuCtrl.MENU_REC_SAVE   : ( "Stop recording", stopRecordingPar, menuStopRecording(menuController, recordingDir=FLAGS.recordingDir) ),
        # Hidden 
        MenuCtrl.MENU_YAML       : MenuCtrl.MENU_YAML_TUPLE,
        MenuCtrl.MENU_VERSION    : MenuCtrl.MENU_VERSION_TUPLE,
        MenuCtrl.MENU_LIST_RES   : MenuCtrl.MENU_LIST_RES_TUPLE,
    }

    menuController.setMenu( menu = mainMenu, defaults = defaults)
    # Exec it 
    menuController.mainMenu()

    return menuController
    

    

def _main( _argv ):
    logging.set_verbosity(FLAGS.debug)
    if FLAGS.syspath:
        sys.path.insert( 0, FLAGS.syspath )
    logging.info( "sys.path={}".format(sys.path))
    menuController = run( _argv, config=FLAGS.config)
    if menuController is not None:
        logging.info( "Closing menuController: {}".format(menuController))
        menuController.close()

    




def main():
    try:
        app.run(_main)
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
