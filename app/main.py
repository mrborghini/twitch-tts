from dataclasses import dataclass
import os
import subprocess
import threading
import websocket
import rel
from components import splash_screen
from components.text_to_speech import TextToSpeech
from components.config_reader import ConfigReader

@dataclass
class TwitchWSResponse:
    username: str
    email: str
    channel: str
    content: str

splash_screen.splash_screen()

config = ConfigReader.read_and_parse()
if config.tts_config.volume > 2:
    print(f"Warning: your volume is set to '{config.tts_config.volume}'. This is extemely loud.")
    print("An acceptable volume is between '0.1' and '2.0'")
    confirmation = input("Do you wish to continue? (y/n): ")

    lowered_confirmation = confirmation.lower().strip()

    if not lowered_confirmation == "yes" and not lowered_confirmation == "y":
        exit(0)

queue: list[TwitchWSResponse] = []
busy = False
tts = TextToSpeech(config.tts_config.voices_dir, config.tts_config.specific_users)

def play_sound(audio_path: str):
    subprocess.run(
        [
            "ffplay", 
            "-nodisp", 
            "-autoexit", "-loglevel", 
            "quiet", audio_path, 
            "-af", 
            f"volume={config.tts_config.volume}"
        ])

def generate_and_play(text: str, username: str):
    output = tts.generate_speech(text, username)
    threading.Thread(target=play_sound, args=(output,), daemon=True).start()
    # os.remove(output)

def update_queue():
    global busy
    if busy:
        return
    
    busy = True

    for item in queue:
        print(f"generating {item.content}...")
        generate_and_play(item.content, item.username)
        queue.pop(0)

    if len(queue) != 0:
        update_queue()
    
    busy = False

def convert_message(received_message: str) -> TwitchWSResponse:
    split_colon = received_message.split(":")
    split_exclamation = split_colon[1].split("!")
    split_spaces = split_exclamation[1].split(" ")

    channel = split_spaces[2].replace("#", "")
    email = split_spaces[0]
    username = split_exclamation[0]
    message = received_message.split(" :")[1]

    twitchResponse = TwitchWSResponse(
        username=username,
        email=email,
        channel=channel,
        content=message,
    )

    return twitchResponse
        

def on_message(ws: websocket.WebSocketApp, message: str):
    trimmed_message = message.strip()
    if trimmed_message.startswith("PING"):
        ws.send("PONG :tmi.twitch.tv")
        return
    
    if not "PRIVMSG" in trimmed_message:
        return
    
    twitch_response = convert_message(trimmed_message)
    print(f"Received message from {twitch_response.username}: '{twitch_response.content}'")
    queue.append(twitch_response)
    update_queue()

def on_error(ws: websocket.WebSocketApp, error):
    print(error)

def on_close(ws: websocket.WebSocketApp, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws: websocket.WebSocketApp):
    ws.send(f"PASS oauth:{config.twitch_config.twitch_access_token}")
    ws.send(f"NICK {config.twitch_config.twitch_name}")
    ws.send(f"JOIN #{config.twitch_config.streamer_channel}")
    connection_message = f"Successfully connected to Twitch channel {config.twitch_config.streamer_channel.lower()}!"
    print(connection_message)
    generate_and_play(connection_message, "")

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
