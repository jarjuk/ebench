from .ebUnit import run
from absl import app, flags, logging
from absl.flags import FLAGS

ADDR= "USB0::0x6656::0x0834::1485061822::INSTR"
flags.DEFINE_string('addr', ADDR, "pyvisa instrument address")

def _main( _argv ):
    logging.set_verbosity(FLAGS.debug)
    menuController = run( _argv, addr=FLAGS.addr, captureDir=FLAGS.captureDir, recordingDir=FLAGS.recordingDir  )
    menuController.close()


def main():
    try:
        app.run(_main)
    except SystemExit:
        pass
    
    
if __name__ == '__main__':
    main()
    

