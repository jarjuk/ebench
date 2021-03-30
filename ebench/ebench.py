#!/usr/bin/env python3

from typing import Dict, List

import os
from absl import flags, app, logging
from absl.flags import FLAGS
import re


flags.DEFINE_integer('debug', -1, '-3=fatal, -1=warning, 0=info, 1=debug')

def version():
    versionPath = os.path.join( os.path.dirname( __file__), "..", "VERSION")
    with open( versionPath, "r") as fh:
        version = fh.read().rstrip()
    return version



class Cmd:
    """Abstract class to implement user interface"""

    def promptValue( prompt:str, key:str=None, cmds:List[str]=None, validValues:List[str]=None ):
        ans = None
        if cmds is None:
            # ans <- interactive
            ans = input( "{} > ".format(prompt) )
        else:
            if len(cmds ) > 0:
                # ans <- batch
                if key is None:
                    # not expecting key-value pair - take first
                    ans = cmds.pop(0)
                else:
                    # expecting key=value
                    peek1st = cmds[0]
                    match = re.search( r"(?P<key>.+)=(?P<value>.*)", peek1st )
                    if match is not None:
                        # key-value pair found
                        if match.group('key') == key:
                            # key matches
                            cmds.pop(0)
                            ans = match.group('value')
                        else:
                            # key does not match
                            ans = None
                    else:
                        # no key-value pair (when expecting one)
                        ans = None



        # ans found - lets check validity
        if validValues is not None:
            if ans not in  validValues:
                print( "{} > expecting one of {} - got '{}'".format( prompt, validValues, ans  ))
                return None
        return ans 

    def mainMenu( _argv, mainMenu:Dict[str,List] ):
        """For interactive usage, prompt user for menu command and command
        paramaters, for command line usage parse commands and
        parameters from command line. Invoke action for command.

        :_argv: command line paramaters

        :mainMenu: menu structuer

        """
        
        cmds = None
        if len(_argv) > 1:
            cmds = _argv[1:]
        logging.info( "Starting cmds={}".format(cmds))

        
        goon = True
        while goon:
            if cmds is not None and len(cmds) == 0:
                # all commands consumed - quit batch
                break
            cmd = Cmd.promptValue( "Command [q=quit,?=help]", cmds=cmds, validValues=mainMenu.keys() )
            logging.debug( "Command '{}'".format(cmd))
            if cmd is None:
                continue
            elif cmd == 'q' or cmd == 'Q':
                goon = False
            else:
                # Extract mainMenu elements
                menuSelection = mainMenu[cmd]
                menuParameters = menuSelection[1]
                menuAction =  menuSelection[2]
                propVals = {}

                if menuParameters is not None:
                    # Promp user/read CLI keyvalue parameters
                    propVals = {
                        k: Cmd.promptValue(v,key=k,cmds=cmds) for k,v in menuParameters.items()
                    }
                if menuAction is not None:
                    # Call menu action (w. parameters)
                    menuAction( cmd, **propVals )

    def usage( menuKey, mainMenu, mainMenuHelp, subMenuHelp, command=None  ):
        """Output 'mainMenuHelp' if 'command' is None else 'subMenuHelp' for
        'command'

        :menuKey: menu option chosen by user to start usage

        :mainMenu: application main commands

        :mainMenuHelp: lambda to start if 'command' is None, output mainMenu

        :subMenuHelp: lambda to start if 'command' is not None, output
        one liner from mainMenu for command synopsis, and then command
        parameters from mainMenu

        """
        if command is None or not command:
            mainMenuHelp(mainMenu=mainMenu)
        else:
            commandParameters = {} if mainMenu[command][1] is None else mainMenu[command][1]
            subMenuHelp( command, menuText=mainMenu[command][0], commandParameters=commandParameters )

        


# ------------------------------------------------------------------
# Test setup

class Tst(Cmd):

    def tst1( menuKey, par1, par2="default par2 value"):
        logging.info( "menuKey: {}, par1:{}, par2:{}".format( menuKey, par1, par2))
        print( "tst1: ")
        print( " - par1: {} ".format(par1))
        print( " - par2: {} ".format(par2))
    def tst2( menuKey, par1="par1", tstPar2=1 ):
        logging.info( "menuKey={}, par1:{}, tstPar2:{}".format( menuKey, par1, tstPar2))
        print( "menuKey={}, par1:{}, tstPar2:{}".format( menuKey, par1, tstPar2))

def tstMainMenuHelp(  mainMenu ):
     print( "Commands:")
     for k,v in mainMenu.items():
         print( "%15s  : %s" % (k,v[0]) )
        
def tstSubMenuHelp( command, menuText, commandParameters ):
    print( "{} - {}".format( command, menuText))
    print( "" )
    if len(commandParameters.keys()) > 0:
       for k,v in commandParameters.items():
           print( "%10s  : %s" % (k,v) )
    else:
        print( "*No parameters*")
        
tst1Par = {
      "par1": "Par1 value",
      "par2": "Par2 value",
}

tst2Par = {
      "par1": "Par1 value",
      "tstPar2": "Test Par2 value",
}

helpPar = {
      "command": "Command to give help on"
}
        
tstMenu = {
    'q'              : ("Exit", None, None),
    'Q'              : ("Exit", None, None ),
    '?'              : ("Usage help",helpPar,
                          lambda menuKey, **argV: Cmd.usage( menuKey, mainMenu=tstMenu, mainMenuHelp=tstMainMenuHelp, subMenuHelp=tstSubMenuHelp, **argV ) ),
    "tst1"           : ("Test action 1", tst1Par, Tst.tst1),
    "tst2"           : ("Test action( 2",  tst2Par, Tst.tst2 ),
    "version"        : ("Output version() number", None, lambda x: print(version())),
}
    
def main( _argv ):
    logging.set_verbosity(FLAGS.debug)
    Cmd.mainMenu( _argv, tstMenu)

if __name__ == '__main__':
    try:
        app.run(main)
    except SystemExit:
        pass

 
