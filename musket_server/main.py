import sys

from musket_server import server, tasks, setup_server

def sysarg(num):
    sys.argv[num] if len(sys.argv) > num else None

def main():
    if sysarg(1) == "setup":
        setup_server.run(sysarg(2) , sysarg(3), sysarg(4))

        return

    server.start_server(int(sysarg(1)), tasks.TaskManager(2))

#main()