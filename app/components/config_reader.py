from dataclasses import dataclass
import json

@dataclass
class TwitchConfig:
    twitch_access_token: str
    twitch_name: str
    streamer_channel: str

@dataclass
class TTSConfig:
    voices_dir: str
    user_chance_tts_percentage: float
    tts_specific_users: bool
    specific_users: list[str]
    volume: float

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

            return Config(twitch_config=TwitchConfig(
                twitch_access_token=twitch_config.get("twitch_access_token", ""),
                twitch_name=twitch_config.get("twitch_name", ""),
                streamer_channel=twitch_config.get("streamer_channel", ""),
            ), tts_config=TTSConfig(
                voices_dir=tts_config.get("voices_dir", ""),
                user_chance_tts_percentage=tts_config.get("user_chance_tts_percentage", ""),
                tts_specific_users=tts_config.get("tts_specific_users", ""),
                specific_users=tts_config.get("specific_users", ""),
                volume=tts_config.get("volume", 0.5),
            ))