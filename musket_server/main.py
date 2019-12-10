import sys

from musket_server import server, tasks, setup_server

def main():
    if sys.argv[1] == "setup":
        setup_server.run(sys.argv[2], sys.argv[3], sys.argv[4])

        return

    server.start_server(int(sys.argv[1]), tasks.TaskManager(2))

#main()