import sys
import threading

from src.urwid_components.mainLoop import MainLoopManager


def main():
    if len(sys.argv) <= 1:
        raise Warning("Provide a valid dir")
    else:
        dir = sys.argv[1]

    main_loop_manager = MainLoopManager(dir)
    main_loop_manager.start()

    for th in threading.enumerate():
        if th != threading.current_thread():
            th.join()


if __name__ == "__main__":
    main()
