import sys
from musket_server import utils

def main():
    print("collecting: " + sys.argv[1])

    utils.collect_results(sys.argv[1])

main()