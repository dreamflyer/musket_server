import os

import subprocess, time

from musket_server import process_streamer, server, tasks
from musket_core import utils

import requests
import shlex

import json

def log(s):
    if(len(s) > 0):
        print(s.strip())

def set_process(p):
    pass

def run(port, setup_for, kaggle_user=None, kaggle_authkey=None):
    dirname = os.path.dirname(__file__)

    setup = utils.load_yaml(os.path.join(dirname, "setup_configs",  setup_for + ".yaml"))

    process_streamer.execute_command("wget " + setup["ngrok"]["distr"], os.getcwd(), log, set_process, True, 0.3)
    process_streamer.execute_command("unzip " + setup["ngrok"]["zip"], os.getcwd(), log, set_process, True, 0.3)

    while(True):
        if not os.path.exists("./ngrok"):
            time.sleep(1)

            continue

        break

    subprocess.Popen(shlex.split("./ngrok http " + str(port)))

    while(True):
        try:
            response = requests.get("http://localhost:4040/api/tunnels")

            if not str(response.status_code) == "200":
                print("response code: " + str(response.status_code))

                continue

            ngrok_cfg = json.loads(response.text)

            if len(ngrok_cfg["tunnels"]) == 0:
                print("ngrok tunnel not created yet...")

                continue

            print("SERVER URL: " + ngrok_cfg["tunnels"][0]['public_url'])

            break
        except:
            print("waiting ngrok...")

            time.sleep(1)

    kaggle_dir = os.path.expanduser("~/.kaggle")

    utils.ensure(kaggle_dir)

    kaggle_json_path = os.path.join(kaggle_dir, "kaggle.json")

    if not os.path.exists(kaggle_json_path):
        with open(kaggle_json_path, "w") as f:
            f.write('{"username":"' + kaggle_user +'","key":"' + kaggle_authkey  + '"}')

    #subprocess.Popen(shlex.split("musket_server " + str(port)))
    #process_streamer.execute_command("musket_server " + str(port), os.getcwd(), log, set_process, True, 0.3)

    server.start_server(int(port), tasks.TaskManager(2))

