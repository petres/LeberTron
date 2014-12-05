import wave
import time
import logging
import threading

try:
    import pyaudio
except ImportError as e:
    logging.warning(e.message)

class Sound():
    def __init__(self, path='sounds/peng.wav'):
        
        self.soundThread = False
        self._start = False
        self._stop = False
        self._close = False
        self._loop = False

        self.p = pyaudio.PyAudio()
        self.wf = wave.open(path, 'rb')

        self.stream = self.p.open(format=self.p.get_format_from_width(self.wf.getsampwidth()),
                channels=self.wf.getnchannels(),
                rate=self.wf.getframerate(),
                output=True)

        

    def soundCallback(self):
        while not self._close:
            self.wf.rewind()

            self._start = False
            # Started Loop
            while not self._close:
                data = self.wf.readframes(1024)
                if self._start or self._stop or data == '':
                    break
                self.stream.write(data)

            if self._loop and not self._stop:
                continue

            # Stopped Loop
            self._stop = False
            while not self._close:
                if self._start:
                    break
                time.sleep(0.1)

            if self._start:
                continue

        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def firstStart(self):
        self.soundThread = threading.Thread(target=self.soundCallback)
        self.soundThread.start()

    def play(self):
        if not self.soundThread:
            self.firstStart()
        self._start = True
        
    def stop(self):
        self._stop = True

    def close(self):
        self._close = True

    def loop(self):
        self._loop = True
        self.play()

    def stopLoop(self):
        self._loop = False
        self.stop()


if __name__ == '__main__':

    sound = Sound()
    sound.loop()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sound.stopLoop()

    time.sleep(2)
    sound.loop()

    try:
        while True:
            #sound.play()
            time.sleep(1)
    except KeyboardInterrupt:
        sound.close()
        print "Ciao..."

    # theme.play()
    # time.sleep(2)

    # s = Sound()
    # s.play()
    # time.sleep(1)
    # s.play()
    # time.sleep(1)
    # s.close()
