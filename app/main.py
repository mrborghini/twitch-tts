from dataclasses import dataclass
import os
import subprocess
import threading
import time
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

playback_queue: list[str] = []
playback_queue_lock = False

generation_queue: list[TwitchWSResponse] = []
generation_queue_lock = False

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
    if config.tts_config.delete_generations_after_playing:
        os.remove(audio_path)

def generate_and_play(text: str, username: str):
    time.sleep(0.1)
    output = tts.generate_speech(text, username)
    threading.Thread(target=play_sound, args=(output,), daemon=True).start()

def update_playback_queue():
    global playback_queue_lock
    if playback_queue_lock:
        return
    
    playback_queue_lock = True

    for audio in playback_queue:
        thread = threading.Thread(target=play_sound, args=(audio,), daemon=True)
        thread.start()
        if config.tts_config.wait_for_audio_to_finish_playing:
            thread.join()

        playback_queue.pop(0)

    if len(playback_queue) != 0:
        update_playback_queue()

    playback_queue_lock = False

def update_generation_queue():
    global generation_queue_lock
    if generation_queue_lock:
        return
    
    generation_queue_lock = True

    for item in generation_queue:
        print(f"generating {item.content}...")
        output = tts.generate_speech(item.content, item.username)
        playback_queue.append(output)
        threading.Thread(target=update_playback_queue, daemon=True).start()
        generation_queue.pop(0)

    if len(generation_queue) != 0:
        update_generation_queue()
    
    generation_queue_lock = False

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
    generation_queue.append(twitch_response)
    update_generation_queue()

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
