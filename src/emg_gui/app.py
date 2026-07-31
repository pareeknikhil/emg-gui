from emg_gui.utils.log_utils import Logger
from emg_gui.visualizer.window import EMGSignalAnalyzer


class App(EMGSignalAnalyzer):
    pass

def main():
    logger = Logger.get_instance()
    App.run(logger)

if __name__=="__main__":
    main()
