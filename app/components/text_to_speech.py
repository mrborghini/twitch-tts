from dataclasses import dataclass
import os
import random
import time
from TTS.api import TTS
import torch
from components.config_reader import UserVoice

@dataclass
class Voice:
    file_path: str
    name: str

class TextToSpeech:
    def __init__(self, voices_dir: str, predefined_users: list[UserVoice], lang = "en"):
        # Get device
        if torch.cuda.is_available():
            print("Using GPU")
            device = "cuda"
        else:
            print("Using CPU")
            device = "cpu"
        
        self.predefined_users = predefined_users
        self.runtime_users: list[UserVoice] = []

        # Init TTS
        print("Loading model. This might take a very long time...")
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        print("Model successfully loaded!")
        self.lang = lang

        self.voices = self.get_voices(voices_dir)

    def chance(percentage: float):
        return random.uniform(0, 100) < percentage

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
    
    def choose_voice(self, username: str) -> Voice:
        if username == "":
            random_number = random.randint(0, len(self.voices) - 1)
            return self.voices[random_number]

        for user in self.predefined_users:
            if user.name == username:
                for voice in self.voices:
                    if user.voice == voice.name:
                        return voice
        
        voice: Voice | None = None

        for user in self.runtime_users:
            if user.name == username:
                for voice in self.voices:
                    if voice.name == user.voice:
                        return voice

        while not voice:
            random_number = random.randint(0, len(self.voices) - 1)
            selected_voice = self.voices[random_number]

            duplicate = False
            for user in self.predefined_users:
                if selected_voice.name == user.voice:
                    duplicate = True

            if not duplicate:
                voice = selected_voice
                self.runtime_users.append(UserVoice(username, selected_voice.name))
            
        return voice
    
    def create_generations_dir(self):
        dir_name = "generations"
        if os.path.exists(dir_name):
            if os.path.isdir(dir_name):
                return dir_name
        os.mkdir(dir_name)
        return dir_name
            
    def generate_speech(self, text: str, username: str):
        dir_name = self.create_generations_dir()

        voice = self.choose_voice(username)
        current_time = f"{time.time() / 1000}"
        return self.tts.tts_to_file(text=text, speaker_wav=voice.file_path, language=self.lang, file_path=f"{dir_name}/{current_time}.wav")