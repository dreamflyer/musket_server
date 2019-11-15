from musket_server import server, tasks

def main():
    server.start_server(9393, tasks.TaskManager(2))

if __name__ == '__main__':
    main()
