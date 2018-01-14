import signal
import logging
import snowboy.detector
import asyncio

class Application:
    def __init__(self):
        signal.signal(signal.SIGINT, lambda s, f: self.stop())

        self.logger = self._init_logger()
        self.loop = asyncio.get_event_loop()
        self.detector = snowboy.detector.Detector(loop=self.loop)

    def _init_logger(self):
        logging.basicConfig()
        logger = logging.getLogger()
        logger.setLevel(logging.NOTSET)
        return logger

    def start(self):
        self.detector.start()
        self.logger.info("Application started")
        self.loop.create_task(self.wait())
        self.loop.run_forever()

    async def wait(self):
        self.logger.info("WAITING")
        await self.detector.hotword()
        await self.speak("Yes, Paul")
        command = await self.listen()
        if command:
            await self.speak("Ok")
            await self.execute(command)
        else:
            await self.speak("I'm going to wait")

        self.loop.create_task(self.wait())

    def speak(self, message):
        f = asyncio.Future()
        self.logger.info("SPEAKING: {0}".format(message))
        self.loop.call_later(2, lambda: f.set_result(True))
        return f

    def listen(self):
        command = "JOKE"
        f = asyncio.Future()
        self.logger.info("LISTENING...")
        self.loop.call_later(5, lambda: f.set_result(command))
        return f

    def execute(self, command):
        f = asyncio.Future()
        self.logger.info("EXECUTING: {0}".format(command))
        self.loop.call_later(2, lambda: f.set_result(True))
        return f

    def stop(self):
        self.loop.stop()
        self.detector.stop()
        self.logger.info("Application stopped")


if __name__ == '__main__':
    app = Application()
    app.start()
