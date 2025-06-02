import os
import sys
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from datetime import datetime

def main():
    # --- Configuration ---
    model_path = "vosk-model-small-en-us-0.15"
    if not os.path.isdir(model_path):
        print(f"❌ Model folder '{model_path}' not found.")
        sys.exit(1)

    # Prepare logs
    os.makedirs("logs", exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logfile = os.path.join("logs", f"live_transcript_{ts}.txt")
    f_log = open(logfile, "w", encoding="utf8")
    print(f"📝 Logging to: {logfile}")

    # Load model & recognizer
    print("🔁 Loading Vosk model...")
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(False)
    print("✅ Model loaded. Listening (Ctrl+C to stop)...")

    # Audio queue and callback
    q = queue.Queue()
    def callback(indata, frames, time, status):
        if status:
            print(f"\n⚠️ Audio status: {status}", file=sys.stderr)
        q.put(bytes(indata))

    # Stream audio
    with sd.RawInputStream(samplerate=16000, blocksize=8000,
                           dtype='int16', channels=1,
                           callback=callback):
        try:
            partial_line = ""
            while True:
                data = q.get()
                if recognizer.AcceptWaveform(data):
                    res = json.loads(recognizer.Result())
                    text = res.get("text", "").strip()
                    if text:
                        # Erase any partial
                        sys.stdout.write("\r" + " " * (len(partial_line) + 3) + "\r")
                        # Timestamped final output
                        now = datetime.now().strftime("%H:%M:%S")
                        line = f"[{now}] {text}"
                        print(line)
                        f_log.write(line + "\n")
                        f_log.flush()
                        partial_line = ""
                else:
                    pr = json.loads(recognizer.PartialResult()).get("partial", "")
                    if pr:
                        # Overwrite the same line with a prefix
                        sys.stdout.write("\r> " + pr + " " * (80 - len(pr)))
                        sys.stdout.flush()
                        partial_line = pr
        except KeyboardInterrupt:
            print("\n🛑 Stopped.")
        finally:
            f_log.close()

if __name__ == "__main__":
    main()
