from enum import Enum
import signal
import logging
import snowboy.detector
import time


class ApplicationState(Enum):
    LIMBO = 0
    LISTENING = 1
    SPEAKING = 2
    EXECUTING = 3
    STOPPED = 4


class Application:
    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, value):
        self.__state = value
        self.logger.info("State set to {0}".format(value.name))

    def __init__(self, logger, detector):
        self.logger = logger
        self.detector = detector
        self.state = ApplicationState.LIMBO
        self.running = True

    def start(self):
        signal.signal(signal.SIGINT, lambda s, f: self.stop())
        self.detector.start()

        self.state = ApplicationState.LISTENING
        while self.running:
            if self.state == ApplicationState.LISTENING:
                if self.detector.is_triggered():
                    self.logger.info("Hotword detected")
                    self.detector.clear_triggered()
                    self.state = ApplicationState.SPEAKING
            time.sleep(0.03)

        self.logger.info("End app")

    def stop(self):
        self.state = ApplicationState.STOPPED
        self.running = False
        self.detector.stop()
        self.logger.info("End stop")


if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET)

    detector = snowboy.detector.Detector()

    app = Application(logger=logger, detector=detector)
    app.start()
