import pytest

import ebench
# from ebench import  ebench


def test_framework():
    assert 1 == 1


# ------------------------------------------------------------------
# Fixtures

@pytest.fixture(scope="module")
def menu1_cmds():
    yield [ 1,2,3]
    
@pytest.fixture(scope="module")    
def menu1(menu1_cmds):
    args = menu1_cmds
    prompt = "hello"
    menu = ebench.MenuCtrl( args=args, prompt=prompt)
    yield menu

    

# ------------------------------------------------------------------
# Misc

@pytest.mark.skip
def test_version():
    assert ebench.version() == "0.0.11-SNAPSHOT"
     
def test_TOOLNAME():
    assert ebench.ebench.TOOLNAME == "ebench"

# ------------------------------------------------------------------
# menu

def test_menu1( menu1, menu1_cmds):
    assert isinstance( menu1, ebench.MenuCtrl)
    assert menu1.isTopMenu
    assert menu1.cmds == menu1_cmds[1:]

# ------------------------------------------------------------------
# promptValue

def test_promptValue_no_key():
    cmds = ["cmd1", "cmd2"]
    expect1 = cmds[0]
    # accepts first in cmds (when key is none )
    ans = ebench.MenuCtrl.promptValue( prompt=None, key=None, cmds=cmds )
    print( f"ans={ans}")
    assert ans == expect1
    # one entry eaten away from cmds
    assert len(cmds) == 1
    
def test_promptValue_key_given():
    cmds = ["key1=val1", "cmd2"]
    expect1 = cmds[0]
    # accepts first in cmds (when key is none )
    ans = ebench.MenuCtrl.promptValue( prompt=None, key="keyxx", cmds=cmds )
    assert ans is None
    ans = ebench.MenuCtrl.promptValue( prompt=None, key="key1", cmds=cmds )
    assert ans == "val1"
    

def test_promptValue_default():
    cmds = ["key1=val1", "cmd2"]
    # accepts first in cmds (when key is none )
    ans = ebench.MenuCtrl.promptValue( prompt=None, key="key1", cmds=cmds )
    # not using default value because found key1 in cmds
    assert ans == "val1"
    defaultParameters = { "key1":"dVal1"}
    ans = ebench.MenuCtrl.promptValue( prompt=None, key="key1", cmds=["dd"], defaultParameters=defaultParameters )
    # Finds default value
    print( f"ans2={ans}")
    assert ans == "dVal1"
    
def test_promptValue_updates_defaultValue():
    key = "key1"
    val = "valia1"
    cmds = [f"{key}={val}", "cmd2"]
    # accepts first in cmds (when key is none )
    defaultParameters = { key: "dVal1"}
    assert defaultParameters[key] != val
    ans = ebench.MenuCtrl.promptValue( prompt=None, key=key, cmds=cmds, defaultParameters=defaultParameters )
    # not using default value because found key1 in cmds
    assert ans == val
    assert defaultParameters[key] == val

# ------------------------------------------------------------------
# MenuCtrl.mainMenu

def test_menu(capfd):
    cliParameters=[ "pgm", "hello"]
    menu = ebench.MenuCtrl( prompt=None, args=cliParameters )
    menu.menu = { cliParameters[1]: ("say hello", None, lambda: print( "hello called") ) }
    menu.mainMenu()
    out,err = capfd.readouterr()
    assert out == "hello called\n"
    

def test_menu_onepar(capfd):
    cliParameters=[ "pgm", "hello", "x=äksä"]
    menu = ebench.MenuCtrl( prompt="gimme cmd", args=cliParameters )
    helloPar = { "x": "gimme x" }
    menu.menu = { cliParameters[1]: ("say hello", helloPar, lambda x: print( f"hello called x={x}") ) }
    menu.mainMenu()
    out,err = capfd.readouterr()
    assert out == "hello called x=äksä\n"

def test_menu_onepar_default(capfd):
    cmd = "hello"
    key="x"
    xDefaultValue = "deffix"
    cliParameters=[ "pgm", cmd ]
    menu = ebench.MenuCtrl( prompt="gimme cmd", args=cliParameters )
    helloPar = { key: "gimme x" }
    defaultParameters = {
        cmd: {
            key: xDefaultValue
        }
    }
    # config menu
    menu.menu = { cliParameters[1]: ("say hello", helloPar, lambda x: print( f"hello called x={x}") ) }
    menu.defaults = defaultParameters
    # run menu
    menu.mainMenu()
    out,err = capfd.readouterr()
    assert out == f"hello called x={xDefaultValue}\n"
    

def test_menu_twopars_ordered(capfd):
    cliParameters=[ "pgm", "hello", "x=äksä", "y=yyy"]
    menu = ebench.MenuCtrl( prompt="gimme cmd", args=cliParameters )
    helloPar = { "x": "gimme x", "y": "gimme Y" }
    menu.menu = { cliParameters[1]: ("say hello", helloPar, lambda x, y: print( f"hello called x={x}, y={y}") ) }
    menu.mainMenu()
    out,err = capfd.readouterr()
    assert out == "hello called x=äksä, y=yyy\n"
    

def test_menu_twopars_unordered(capfd):
    cliParameters=[ "pgm", "hello", "y=yyy", "x=äksä" ]
    menu = ebench.MenuCtrl( prompt="gimme cmd", args=cliParameters )
    helloPar = { "x": "gimme x", "y": "gimme Y" }
    menu.menu = { cliParameters[1]: ("say hello", helloPar, lambda x, y: print( f"hello called x={x}, y={y}") ) }
    menu.mainMenu()
    out,err = capfd.readouterr()
    assert out == "hello called x=äksä, y=yyy\n"
    

    
def test_menu_twopars_default(capfd):
    k1="x"
    k2="y"
    k2Val="yyYY"
    cmd = "hello"
    defaultParameters = {
        cmd: {
            k1: "defaultk1",
            k2: "defaultk2",
        }
    }
    cliParameters=[ "pgm", cmd, f"{k2}={k2Val}" ]
    menu = ebench.MenuCtrl( prompt="gimme cmd", args=cliParameters )
    helloPar = { k1: "gimme x", k2: "gimme Y" }
    menu.menu = { cliParameters[1]: ("say hello", helloPar, lambda x, y: print( f"hello called x={x}, y={y}") ) }
    menu.defaults = defaultParameters
    menu.mainMenu()
    out,err = capfd.readouterr()
    assert out == f"hello called x={defaultParameters[cmd][k1]}, y={k2Val}\n"
    
def test_menu_twopars_default2(capfd):
    k1="x"
    k2="y"
    k1Val="xxxXXXxx"
    k2Val="yyYY"
    cmd = "hello"
    defaultParameters = {
        cmd: {
            k1: "defaultk1",
            k2: "defaultk2",
        }
    }
    cliParameters=[ "pgm", cmd, f"{k1}={k1Val}" ]
    menu = ebench.MenuCtrl( prompt="gimme cmd", args=cliParameters )
    helloPar = { k1: "gimme x", k2: "gimme Y" }
    menu.menu = { cliParameters[1]: ("say hello", helloPar, lambda x, y: print( f"hello called x={x}, y={y}") ) }
    menu.defaults = defaultParameters
    menu.mainMenu()
    out,err = capfd.readouterr()
    assert out == f"hello called x=xxxXXXxx, y=defaultk2\n"
    
