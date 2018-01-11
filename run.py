import pyaudio
import time
import wave

FORMAT = pyaudio.paInt32
CHANNELS = 2
RATE = 44100

class Recorder(object):
    '''A recorder class for recording audio to a WAV file.
    Records in mono by default.
    '''

    def __init__(self, channels=1, rate=44100, frames_per_buffer=1024):
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer

    def open(self, fname, mode='wb'):
        return RecordingFile(fname, mode, self.channels, self.rate,
                            self.frames_per_buffer)

class RecordingFile(object):
    def __init__(self, fname, mode, channels,
                rate, frames_per_buffer):
        self.fname = fname
        self.mode = mode
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self._pa = pyaudio.PyAudio()
        self.wavefile = self._prepare_file(self.fname, self.mode)
        self._stream = None

    def __enter__(self):
        return self

    def __exit__(self, exception, value, traceback):
        self.close()

    def record(self, duration):
        # Use a stream with no callback function in blocking mode
        self._stream = self._pa.open(format=pyaudio.paInt16,
                                        channels=self.channels,
                                        rate=self.rate,
                                        input=True,
                                        frames_per_buffer=self.frames_per_buffer)
        for _ in range(int(self.rate / self.frames_per_buffer * duration)):
            audio = self._stream.read(self.frames_per_buffer)
            self.wavefile.writeframes(audio)
        return None

    def start_recording(self):
        # Use a stream with a callback in non-blocking mode
        self._stream = self._pa.open(format=pyaudio.paInt16,
                                        channels=self.channels,
                                        rate=self.rate,
                                        input=True,
                                        frames_per_buffer=self.frames_per_buffer,
                                        stream_callback=self.get_callback())
        self._stream.start_stream()
        return self

    def stop_recording(self):
        self._stream.stop_stream()
        return self

    def get_callback(self):
        def callback(in_data, frame_count, time_info, status):
            self.wavefile.writeframes(in_data)
            return in_data, pyaudio.paContinue
        return callback


    def close(self):
        self._stream.close()
        self._pa.terminate()
        self.wavefile.close()

    def _prepare_file(self, fname, mode='wb'):
        wavefile = wave.open(fname, mode)
        wavefile.setnchannels(self.channels)
        wavefile.setsampwidth(self._pa.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        return wavefile

rec = Recorder(channels=CHANNELS, rate=RATE)
with rec.open('nonblocking.wav', 'wb') as recfile2:
    recfile2.start_recording()
    time.sleep(5.0)
    recfile2.stop_recording()

# audio = pyaudio.PyAudio()
# print()
# for i in range(audio.get_device_count()):
#     print(i, audio.get_device_info_by_index(i)["name"],audio.get_device_info_by_index(i)["maxInputChannels"])
# print()
#
# wavefile = wave.open("~/record_from_python.wav", "wb")
# wavefile.setnchannels(CHANNELS)
# wavefile.setsampwidth(audio.get_sample_size(FORMAT))
# wavefile.setframerate(RATE)
#
# def audio_callback(in_data, frame_count, time_info, status):
#     print(in_data)
#     play_data = chr(0) * len(in_data)
#     return play_data, pyaudio.paContinue
#
# stream_in = audio.open(
#     input=True, output=False,
#     format=FORMAT,
#     channels=CHANNELS, #self.detector.NumChannels(),
#     rate=RATE, #self.detector.SampleRate(),
#     frames_per_buffer=2048,
#     stream_callback=audio_callback,
#     input_device_index=2)
#
# stream_in.start_stream()
#
# while stream_in.is_active():
#     time.sleep(0.1)
#
# # stop stream (6)
# stream_in.stop_stream()
# stream_in.close()
#
# # close PyAudio (7)
# audio.terminate()