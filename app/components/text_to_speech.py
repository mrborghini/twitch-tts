from dataclasses import dataclass
import os
import random
from TTS.api import TTS
import torch

@dataclass
class Voice:
    file_path: str
    name: str

class TextToSpeech:
    def __init__(self, voices_dir: str, lang = "en"):
        # Get device
        if torch.cuda.is_available():
            print("Using GPU")
            device = "cuda"
        else:
            print("Using CPU")
            device = "cpu"

        # Init TTS
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        self.lang = lang

        self.voices = self.get_voices(voices_dir)

    def sanitize_filename(self, filename: str, max_length: int = 150) -> str:
        # Replace invalid characters with hyphens and truncate to max_length
        invalid_chars = '\\/:*?"<>|'
        sanitized = ''.join(c if c not in invalid_chars else '-' for c in filename)
        return sanitized[:max_length]

    def get_voices(self, voice_dir: str) -> list[Voice]:
        print("Available voices:")
        voices: list[Voice] = []
        files = os.listdir(voice_dir)
        name_count = {}
        
        for file in files:
            file_path = os.path.join(voice_dir, file)
            name = file.split(".")[0]
            
            if name in name_count:
                name_count[name] += 1
                name = f"{name}_{name_count[name]}"
            else:
                name_count[name] = 0
            
            print(name)
            voices.append(Voice(
                file_path=file_path,
                name=name
            ))

        if len(voices) == 0:
            raise ValueError("No voices found in voices folder")
        
        return voices
    
    def choose_voice(self) -> Voice:
        random_number = random.randint(0, len(self.voices) - 1)
        return self.voices[random_number]
    
    def generate_speech(self, text: str):
        voice = self.choose_voice()
        return self.tts.tts_to_file(text=text, speaker_wav=voice.file_path, language=self.lang, file_path="out.wav")