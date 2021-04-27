from absl import app, flags, logging
from absl.flags import FLAGS

flags.DEFINE_string('ip', "skooppi", "IP address of pyvisa instrument")

from .Rigol import run

def _main( _argv ):
    # Run standalone,
    # global gSkooppi
    logging.set_verbosity(FLAGS.debug)
    # set configuration agrugements application FLAGS 
    menuController = run( _argv, ip=FLAGS.ip, captureDir=FLAGS.captureDir, recordingDir=FLAGS.recordingDir)
    menuController.close()

    
def main():
    try:
        app.run(_main)
    except SystemExit:
        pass
    
    
if __name__ == '__main__':
    main()
    
    
