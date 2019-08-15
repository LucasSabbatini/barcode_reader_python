import logging
import os
import sys


def set_log():
    g_application_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    log_level = logging.DEBUG

    log = logging.getLogger(__name__)
    log.setLevel(log_level)

    if "LOG_PATH" in os.environ:
        log_path = os.environ["LOG_PATH"]
    else:
        log_path = "./log"

    if not os.path.isdir(log_path):
        os.mkdir(log_path)

    log_file = os.path.join(log_path, '{0}.log'.format(g_application_name))
    print("Log File: " + log_file)
    fl = logging.FileHandler(filename=log_file)
    formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
    fl.setFormatter(formatter)
    fl.setLevel(log_level)
    log.addHandler(fl)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    return log

log = set_log()

def arg_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("-l", "__image", required=True, help="path to the image file")
    args = vars(ap.parse_args())
    return 