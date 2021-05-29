#!/usr/bin/env python3
'''
    Bored by the same videos? Get the complete media overkill thanks to this little moviepi/ pygame script.
    https://github.com/argv1/random-video-player
'''
from configparser import ConfigParser
from datetime import datetime
import hashlib
from moviepy.editor import * 
from pathlib import Path
import pygame
import random

# Global settings
base_path = Path(__file__).parent.absolute()
config_file = ConfigParser()
config_file.read(base_path / 'config.ini')
video_folder    = config_file['SETTINGS']['video_folder']
recursive       = bool(config_file['SETTINGS']['recursive'])
formats         = config_file['SETTINGS']['formats'].split(",")
max_sources     = int(config_file['SETTINGS']['max_sources'])
reuse           = bool(config_file['SETTINGS']['reuse'])
reuse_logfile   = config_file['SETTINGS']['reuse_logfile']
total_length    = float(config_file['SETTINGS']['total_length'])
min_length      = float(config_file['SETTINGS']['min_length'])
max_length      = float(config_file['SETTINGS']['max_length'])
resolution      = int(config_file['SETTINGS']['resolution'])
fullscreen      = bool(config_file['SETTINGS']['fullscreen'])
sound           = config_file['SETTINGS']['sound']
sound_folder    = config_file['SETTINGS']['sound_folder']
sound_recursive = bool(config_file['SETTINGS']['sound_recursive'])

def hashfile(file):
    # by https://www.geeksforgeeks.org/compare-two-files-using-hashing-in-python/
    BUF_SIZE = 65536 
    sha256 = hashlib.sha256()
    with open(file, 'rb') as f:  
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()

def get_clips():
    # scrap all video files
    file_lst, clip_lst, used_videos = [], [], []
    [file_lst.extend(list(Path(video_folder).rglob(f"*.{extension}")) if(recursive == True) else list(Path(video_folder).glob(f"*.{extension}"))) for extension in formats]

    # remove to short videos
    for file in file_lst:
        if(VideoFileClip(str(file)).duration >= min_length):
            clip_lst.append([file, VideoFileClip(str(file)).duration, hashfile(file)])
        if(len(clip_lst) >= max_sources):
            break

    # reuse = False and clip already used
    with open(reuse_logfile,"r") as logfile:
        used_videos = logfile.read().splitlines()
    if(reuse == False):
        video_lst = clip_lst[:]
        for clip in video_lst:
            if(clip[2] in used_videos):
                clip_lst.remove(clip)

    return(clip_lst, used_videos)

def create_videofile(clip_lst, used_videos):
    # create four randomized playlist based on the previous found video files
    clips = []
    for n in range(0,4):
        duration, clip_order = 0, []
        while(True):
            random_clip = random.choice(clip_lst)
            clip_order.append(VideoFileClip(str(random_clip[0])))
            duration += random_clip[1]
            used_videos.append(random_clip[2])
            if(duration >= total_length):
                # concatenate
                clips.append(concatenate_videoclips(clip_order))
                break

    # add new files to logfile
    used_videos = set(used_videos)
    with open(reuse_logfile,"w") as logfile:
        for hash in used_videos:
            logfile.write(f"{hash}\n")

    audio = get_sound(clips)

    # combining the four clips to one
    final_video = clips_array([[clips[0], clips[1]], [clips[2], clips[3]]])
    final_video.audio = audio
    now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    filename= f"random_video{now}.mp4"
    final_video.resize(width=480).write_videofile(f"{base_path}/{filename}")
    return(final_video)

def get_sound(clips):
    if(sound == "m"):
        sound_lst = []
        sound_lst.extend(list(Path(sound_folder).rglob(f"*.mp3")) if(sound_recursive == True) else list(Path(sound_folder).glob(f"*.mp3")))
        audioclip = AudioFileClip(str(random.choice(sound_lst)))
    elif(sound == "r"):
        audioclip = AudioFileClip(str(random.choice(clips)))
    return audioclip

def play_clip(final_clip):
    pygame.init()
    pygame.display.set_mode((200, 300), pygame.RESIZABLE)
    final_clip.preview()
    pygame.display.quit()

def main():
    # get enough files for the clip
    clip_lst, used_videos = get_clips()

    # create a new video
    final_clip = create_videofile(clip_lst, used_videos)

    # show the new creation
    play_clip(final_clip)
        
if __name__  == "__main__":
    main()
