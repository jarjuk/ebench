#!/usr/bin/env python3
# Tangled from TEMPLATE.org - changes will be overridden

# main for instrument controller define in module
from example import run

from absl import app, flags, logging
from absl.flags import FLAGS

# Run time configurations of instrument controller
flags.DEFINE_string('ip', None, "IP -address of device")

def _main( _argv ):
    logging.set_verbosity(FLAGS.debug)
    menuController = run(
           _argv
          , ip=FLAGS.ip   # pass run time configuration parameters to controller
          , captureDir=FLAGS.captureDir
          , recordingDir=FLAGS.recordingDir
          , outputTemplate=FLAGS.outputTemplate 
          )
    menuController.close()


def main():
    try:
        app.run(_main)
    except SystemExit:
        pass
    
    
if __name__ == '__main__':
    main()
