## 0.0.10-SNAPSHOT/20210415-14:55:49
## 0.0.9/20210415-14:55:29


- Features fixed
  - --ebRigol: mesaurenmet Statiscits not used
  
- Features added:
  - README.org: problem statement
  - Document files HELLO.org, ebUnit.org, EBMENU.org
  - ebMenu --config type: `subMenu`, type: `apiCalls`
  - Depreacted `MENU_CMD_PARAM` -> `MENU_HELP_CMD`, 
  - added `MENU_HELP_CMD_PARAM`, `MENU_REC_SAVE_PARAM`
  - ebRigol 
    - stat: added, ch USER added, timebase

- Known issues/missing features
  - `ebUnit`: external waveform documentation missing
  - architecture diagram
  - installation instructions
  - users guide of the tools

## 0.0.8/20210404-22:49:09


- Issues fixed:
  - ebRigol (no device found): _version command does not work


- Features added
  - ebRigol setTrigger: added
  - ebRigol measure: uses AVEREGE  statistics
  - HELLO.org w. hello.py && hello2.py
  - hidden menu item: menu command starting with _-char

- Known issues:
  - ebRigol: setup triggering not implemented
  - README.org: API -usage documentation should be enhanced
  - `UTG900.py arb` external waveform, implementation not working
  - `UTG900.py arb` external waveform file, format documentation missing


## 0.0.7/20210402-19:44:32

- From from https://github.com/jarjuk/UTG900 0.0.6-SNAPSHOT

- Features added
  - CLI ebRigol: added
  - CLI ebUnit: added

- Implementation changes
  - Refractored

## 0.0.6-SNAPSHOT/20210330-10:09:33

- Contributions: https://github.com/W3AXL data/simplewave.*

- Known issues:
  - README.org: API -usage documentation should be enhanced
  - `UTG900.py arb` internal waveform, implementation missing
  - `UTG900.py arb` external waveform, implementation not working
  - `UTG900.py arb` external waveform file, format documentation missing

## 0.0.5/20210330-10:07:31

- Issues fixed:
  - README.org: added toc
  - README.org: first version of API usage

- Known issues:
  - README.org: API -usage documentation should be enhanced
  - `UTG900.py arb` implementation not working
  - `UTG900.py arb` waveform file format documentation missing

## 0.0.4/20210329-09:06:37

- Issues fixed
  - Document fixes: 
    - document order of command parameters
    - document interactive mode
    - on-line help: added `--addr` -documentation
    - added DEVELOPMENT.org (moved delivery section from README.org)
    - installation: rewritten, based on git clone

- Features added:
  - `UTG900.py list_resources` -command added
  - `UTG900.py version`  -command added

- Known issues:
  - README.org: missing API -usage documentation

  

## 0.0.3/20210328-23:08:07

- README.org: installation

## 0.0.2/20210328-23:01:53



## 0.0.1/20210328-22:51:12

* Initial release

## 0.0.0/18.00.2013

* Base release

