from dataclasses import dataclass
import json

@dataclass
class UserVoice:
    name: str
    voice: str

@dataclass
class TwitchConfig:
    twitch_access_token: str
    twitch_name: str
    streamer_channel: str

@dataclass
class TTSConfig:
    voices_dir: str
    user_chance_tts_percentage: float
    tts_everyone: bool
    specific_users: UserVoice
    volume: float
    wait_for_audio_to_finish_playing: bool

@dataclass
class Config:
    twitch_config: TwitchConfig
    tts_config: TTSConfig

class ConfigReader:
    @staticmethod
    def read_and_parse() -> Config:
        with open("config.json") as f:
            json_data: dict = json.load(f)

            twitch_config: dict = json_data["twitch_config"]
            tts_config: dict = json_data["tts_config"]

            specific_users: list[UserVoice] = []

            for user in tts_config["specific_users"]:
                specific_users.append(UserVoice(
                    name=user["name"],
                    voice=user["voice"],
                ))

            return Config(twitch_config=TwitchConfig(
                twitch_access_token=twitch_config.get("twitch_access_token", ""),
                twitch_name=twitch_config.get("twitch_name", ""),
                streamer_channel=twitch_config.get("streamer_channel", ""),
            ), tts_config=TTSConfig(
                voices_dir=tts_config.get("voices_dir", ""),
                user_chance_tts_percentage=tts_config.get("user_chance_tts_percentage", ""),
                tts_everyone=tts_config.get("tts_everyone", False),
                specific_users=specific_users,
                volume=tts_config.get("volume", 0.5),
                wait_for_audio_to_finish_playing=tts_config.get("wait_for_audio_to_finish_playing", True)
            ))