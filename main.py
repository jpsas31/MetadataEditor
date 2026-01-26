import sys
import threading

import src.viewInfo as viewInfo
from src.singleton import BorgSingleton
from src.urwid_components.mainLoop import MainLoopManager

state = BorgSingleton()


def main():
    if len(sys.argv) <= 1:
        raise Warning("Provide a valid dir")
    else:
        dir = sys.argv[1]

    state.viewInfo = viewInfo.ViewInfo(dir)
    main_loop_manager = MainLoopManager(state)
    main_loop_manager.start()

    for th in threading.enumerate():
        if th != threading.current_thread():
            th.join()


if __name__ == "__main__":
    main()
