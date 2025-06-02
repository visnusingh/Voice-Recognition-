import os
import json
import vosk
import sounddevice as sd
import queue
import difflib

class VoiceAssistant:
    def __init__(self, model_path):
        # Load model once
        self.model = vosk.Model(model_path)
        self.commands = {
            "start recording": "start",
            "stop recording": "stop",
            "clear screen": "clear",
            "save file": "save",
            "exit program": "exit",
            "shutdown": "exit"
        }
        self.running = False
        self.stream = None
        self.audio_queue = None
        self.recognizer = None

    def reset(self):
        """Re-init recognizer and audio queue for each listening session."""
        self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
        self.recognizer.SetWords(True)
        self.audio_queue = queue.Queue()

    def speak(self, text):
        os.system(f'say "{text}"')

    def audio_callback(self, indata, frames, time, status):
        if status:
            print("⚠️ Audio error:", status)
        self.audio_queue.put(bytes(indata))

    def match_command(self, spoken):
        matches = difflib.get_close_matches(
            spoken, self.commands.keys(), n=1, cutoff=0.6
        )
        return self.commands[matches[0]] if matches else None

    def listen(self, on_transcription, on_command, on_partial=None):
        """
        Listen and dispatch:
          - on_transcription(text) for final results
          - on_command(label) when a command is detected
          - on_partial(text) for partial (in-flight) results
        """
        # Prepare fresh session
        self.reset()
        self.running = True

        # Open and start the audio stream
        self.stream = sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype='int16',
            channels=1,
            callback=self.audio_callback
        )
        self.stream.start()

        try:
            while self.running:
                try:
                    data = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Final result
                if self.recognizer.AcceptWaveform(data):
                    res = json.loads(self.recognizer.Result())
                    text = res.get("text", "")
                    if text:
                        if on_transcription:
                            on_transcription(text)
                        cmd = self.match_command(text.lower())
                        if cmd and on_command:
                            on_command(cmd)
                # Partial result
                else:
                    partial = json.loads(self.recognizer.PartialResult()).get("partial", "")
                    if partial and on_partial:
                        on_partial(partial)
        finally:
            # Ensure stream is stopped & closed every session
            self.running = False
            if self.stream:
                self.stream.stop()
                self.stream.close()

    def stop(self):
        # Signal the listen loop to exit
        self.running = False
