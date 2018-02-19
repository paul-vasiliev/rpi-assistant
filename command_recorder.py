import threading
import asyncio
import functools
import pyaudio
import audioop
from collections import deque
import os
import time
import math
import functools
import logging
import wave

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
THRESHOLD = 1000
SILENCE_LIMIT = 1
PREV_AUDIO = 0.5

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.NOTSET)

class CommandRecorderTask(threading.Thread):
    def __init__(self, callback, interrupt_check):
        super(CommandRecorderTask, self).__init__()
        self.callback = callback
        self.interrupt_check = interrupt_check

    def run(self):
        num_phrases = -1

        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        logger.info("* Listening mic. ")
        audio2send = []
        rel = RATE / CHUNK
        slid_win = deque(maxlen=math.ceil(SILENCE_LIMIT * rel))
        prev_audio = deque(maxlen=math.ceil(PREV_AUDIO * rel))
        started = False
        n = num_phrases
        response = []

        while not self.interrupt_check():
            cur_data = stream.read(CHUNK, exception_on_overflow=False)

            slid_win.append(math.sqrt(abs(audioop.avg(cur_data, 4))))
            if sum([x > THRESHOLD for x in slid_win]) > 0:
                if not started:
                    logger.info("Starting record of phrase")
                    started = True
                audio2send.append(cur_data)
            elif started is True:
                logger.info("Finished")
                # logger.info("Playing back")
                # self._play(list(prev_audio) + audio2send, p)
                logger.info("Saving")
                filename = self._save_speech(list(prev_audio) + audio2send, p)
                logger.info("Callback")
                self.callback(filename)
                # Reset all
                started = False
                slid_win = deque(maxlen=math.ceil(SILENCE_LIMIT * rel))
                prev_audio = deque(maxlen=math.ceil(0.5 * rel))
                audio2send = []
                n -= 1
                logger.info("Listening ...")
            else:
                prev_audio.append(cur_data)

        logger.info("* Done recording")
        stream.close()
        p.terminate()

        return response

    def play(self, command ,p):
        command = functools.reduce(lambda acc, i: acc + i, command, bytes())
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,
                        frames_per_buffer=CHUNK)

        while 1:
            if stream.is_active() and len(command) >= CHUNK * 1:
                data = command[:CHUNK]
                command = command[CHUNK:]
                stream.write(data)

        stream.close()

    def _save_speech(self, data, p):
        filename = 'output_' + str(int(time.time()))
        data = functools.reduce(lambda acc, i: acc + i, data, bytes())
        wf = wave.open(filename + '.wav', 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(data)
        wf.close()
        return filename + '.wav'

# TODO: Refactor into threaded executor
class CommandRecorder():
    def __init__(self, loop):
        self.loop = loop
        self.command_data_future = None
        self.should_stop = False
        self.task = None
        self.running = False

    def __should_stop(self):
        """ Called from a separate thread """
        return self.should_stop

    def command(self):
        self.command_data_future = asyncio.Future()
        return self.command_data_future

    def trigger(self, data):
        """ Called from a separate thread """
        if self.command_data_future:
            self.loop.call_soon_threadsafe(
                functools.partial(lambda f: f.set_result(data), self.command_data_future)
            )
            self.command_data_future = None

    def start(self):
        self.running = True
        self.should_stop = False
        self.task = CommandRecorderTask(
            callback=self.trigger,
            interrupt_check=self.__should_stop
        )
        self.task.start()

    def stop(self):
        if self.running:
            self.should_stop = True
            logger.info("STOP REQUESTED")
            self.task.join()
            self.task = None

        self.running = False
