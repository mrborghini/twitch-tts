from dataclasses import dataclass
import json
import logging
import os
import subprocess
import websocket
import rel
from components.text_to_speech import TextToSpeech
from components.config_reader import ConfigReader

@dataclass
class TwitchWSResponse:
    username: str
    email: str
    channel: str
    content: str


config = ConfigReader.read_and_parse()

queue: list[str] = []
busy = False
tts = TextToSpeech(config.tts_config.voices_dir)

def play_sound(audio_path: str):
    subprocess.run(["ffplay", "-nodisp", "-autoexit", audio_path, "-af", f"volume={config.tts_config.volume}"])

def generate_and_play(text: str):
    output = tts.generate_speech(text)
    play_sound(output)
    os.remove(output)

def convert_message(received_message: str) -> TwitchWSResponse:
    split_colon = received_message.split(":")
    split_exclamation = split_colon[1].split("!")
    split_spaces = split_exclamation[1].split(" ")

    channel = split_spaces[2].replace("#", "")
    email = split_spaces[0]
    username = split_exclamation[0]
    message = split_colon[len(split_colon) - 1]

    twitchResponse = TwitchWSResponse(
        username=username,
        email=email,
        channel=channel,
        content=message,
    )

    return twitchResponse;

def update_queue():
    global busy
    if busy:
        return
    
    busy = True

    for item in queue:
        generate_and_play(item)
        queue.pop(0)

    if len(queue) != 0:
        update_queue()
    
    busy = False
        

def on_message(ws: websocket.WebSocketApp, message: str):
    trimmed_message = message.strip()
    if trimmed_message.startswith("PING"):
        ws.send("PONG :tmi.twitch.tv")
        return
    
    if not "PRIVMSG" in trimmed_message:
        return
    
    twitch_response = convert_message(trimmed_message)
    print(twitch_response)
    queue.append(twitch_response.content)
    update_queue()

def on_error(ws: websocket.WebSocketApp, error):
    print(error)

def on_close(ws: websocket.WebSocketApp, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws: websocket.WebSocketApp):
    ws.send(f"PASS oauth:{config.twitch_config.twitch_access_token}")
    ws.send(f"NICK {config.twitch_config.twitch_name}")
    ws.send(f"JOIN #{config.twitch_config.streamer_channel}")
    connection_message = f"Successfully connected to Twitch channel {config.twitch_config.streamer_channel}!"
    print(connection_message)
    generate_and_play(connection_message)

def main():
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp("wss://irc-ws.chat.twitch.tv:443",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    ws.run_forever(dispatcher=rel, reconnect=5)
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()

if __name__ == "__main__":
    main()
