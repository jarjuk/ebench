#!/usr/bin/env python3
#!/usr/bin/env python3
from hello3 import run

from absl import app, flags, logging
from absl.flags import FLAGS 

# --------------------------------------
# Application main - call hello3.run()

def _main( _argv ):
    logging.set_verbosity(FLAGS.debug)

    # Start standalone application
    menuController = run( _argv, 
          outputTemplate=FLAGS.outputTemplate, 
          recordingDir=FLAGS.recordingDir )

    # q from menu or end of CLI parameters
    menuController.close()

def main():
    try:
        app.run(_main)
    except SystemExit:
        pass

if __name__ == '__main__':
    main()
