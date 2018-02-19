from . import snowboydecoder
import threading
import os
import asyncio
import functools


class DetectorTask(threading.Thread):
    def __init__(self, snowboy, hotword_callback, interrupt_check):
        super(DetectorTask, self).__init__()
        self.snowboy = snowboy
        self.hotword_callback = hotword_callback
        self.interrupt_check = interrupt_check

    def run(self):
        self.snowboy.start(self.hotword_callback, self.interrupt_check)
        self.snowboy.terminate()


class Detector(object):
    """
    Runs Snowboy detector in a separate thread
    """
    TOP_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_FILE = os.path.join(TOP_DIR, "resources/common.res")

    def __init__(self, model="snowboy/resources/alexa.umdl", sensitivity=0.75, loop = asyncio.get_event_loop()):
        self.task = None
        self.model = model
        self.sensitivity = sensitivity
        self.should_stop = True
        self.hotword_future = None
        self.loop = loop
        self.running = False

    def __should_stop(self):
        """ Called from a separate thread """
        return self.should_stop

    def trigger(self):
        """ Called from a separate thread """
        if self.hotword_future:
            self.loop.call_soon_threadsafe(
                functools.partial(lambda f: f.set_result(True), self.hotword_future)
            )
            self.hotword_future = None

    def hotword(self):
        self.hotword_future = asyncio.Future()
        return self.hotword_future

    def start(self):
        self.running = True
        self.should_stop = False
        self.task = DetectorTask(
            snowboy=snowboydecoder.HotwordDetector(
                decoder_model=self.model,
                resource=Detector.RESOURCE_FILE,
                sensitivity=self.sensitivity
            ),
            hotword_callback=self.trigger,
            interrupt_check=self.__should_stop
        )
        self.task.start()

    def stop(self):
        """
        Stops detector and blocks until Snowboy thread is terminated
        :return:
        """
        if self.running:
            self.should_stop = True
            self.task.join()
            self.task = None

        self.running = False
