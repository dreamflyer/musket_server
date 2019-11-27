import sys

from musket_server import server, tasks

def main():
    server.start_server(int(sys.argv[1]), tasks.TaskManager(2))

#main()