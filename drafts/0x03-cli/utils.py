# utils.py

import os


def get_audio_files(path):
    audio_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith((".mp3", ".wav", ".ogg")):
                audio_files.append(os.path.join(root, file))
    return audio_files
