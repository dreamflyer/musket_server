import os

import sys

import io

import shlex

import asyncio

import time

import threading

import requests

import subprocess

class Streamer:
    def __init__(self, timeout, logger):
        self.logger = logger

        self.timeout = timeout

        self.lines = ""

        self.expired = time.time() + timeout

        self.running = True

        self.thread = threading.Thread(target=self.listen)

        self.thread.start()

    def write_line(self, line):
        self.lines += line

    def stop(self):
        self.running = False

    def send(self):
        if len(self.lines):
            self.logger(self.lines)

            self.lines = ""

    def listen(self):
        while self.running:
            current_time = time.time()

            if current_time > self.expired:
                self.send()

                self.expired = current_time + self.timeout

            time.sleep(1)

        self.send()

def stream_subprocess(cmd, streamer, cwd=None):
    os.environ["PATH"]=os.environ["PATH"] + ":/Users/dreamflyer/.conda/envs/surf360cam/bin"

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=cwd)

    for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):
        streamer.write_line(line)

    streamer.stop()

def execute(command_line, streamer, cwd=None):
    stream_subprocess(shlex.split(command_line), streamer, cwd)

def execute_command(command_line, cwd, logger):
    execute(command_line, Streamer(10, logger), cwd = cwd)


