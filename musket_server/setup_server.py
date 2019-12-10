import os

import subprocess, time

from musket_server import process_streamer
from musket_core import utils

import requests
import shlex

def log(s):
    if(len(s) > 0):
        print(s.strip())

def set_process(p):
    pass

def run(setup_for, kaggle_user=None, kaggle_authkey=None):
    dirname = os.path.dirname(__file__)

    setup = utils.load_yaml(os.path.join(dirname, "setup_configs",  setup_for + ".yaml"))

    process_streamer.execute_command("wget " + setup["ngrok"]["distr"], os.getcwd(), log, set_process, True, 0.3)
    process_streamer.execute_command("unzip " + setup["ngrok"]["zip"], os.getcwd(), log, set_process, True, 0.3)

    while(True):
        if not os.path.exists("./ngrok"):
            time.sleep(1)

            continue

        break

    subprocess.Popen(shlex.split("./ngrok http 9393"))

    while(True):
        try:
            response = requests.get("http://localhost:4040/api/tunnels")

            if not str(response.status_code) == "200":
                print("response code: " + str(response.status_code))

                continue

            print(response.text)

            break
        except:
            print("waiting ngrok...")

            time.sleep(1)
