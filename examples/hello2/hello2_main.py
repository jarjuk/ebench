#!/usr/bin/env python3
from hello2 import run

from absl import app, flags, logging
from absl.flags import FLAGS 

# --------------------------------------
# Command line configurations

flags.DEFINE_integer('greetCount', 0, "Initial number of greets already made") 

# --------------------------------------
# Application main - call hello2.run()


def _main( _argv ):
    logging.set_verbosity(FLAGS.debug)

    # Start standalone application
    menuController = run( _argv, greetCount = FLAGS.greetCount )

    # q from menu or end of CLI parameters
    menuController.close()




def main():
    try:
        app.run(_main)
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
