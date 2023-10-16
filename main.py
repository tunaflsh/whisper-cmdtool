#!/usr/bin/env python
import argparse
import glob
import json
import os
import re

from audio_processing import extract_url_from_metadata, getid, yt_dlp
from tagger import create_tags_from_transcription
from transcribe import transcribe_audio, translate_audio
from transcription_processing import filter_no_speech

# Set up argument parser
parser = argparse.ArgumentParser(
    description="""Transcribes an audio source to text using the OpenAI's Whisper API. The result is saved in the timestamps/ folder as a Markdown file. In case the input is a YouTube URL, the timestamps link to the video at the corresponding time."""
)
parser.add_argument(
    "input",
    type=str,
    help="Path or URL to the audio source to transcribe, in one of these formats: mp3, mp4, mpeg, mpga, m4a, wav, or webm.",
)
parser.add_argument(
    "-p",
    "--prompt",
    type=str,
    help="An optional text to guide the model's style or continue a previous audio segment. The prompt should match the audio language.",
    default=None,
)
parser.add_argument(
    "-l",
    "--language",
    type=str,
    help="The language of the input audio. Supplying the input language in ISO-639-1 format will improve accuracy and latency.",
    default=None,
)
parser.add_argument(
    "-t",
    "--translate",
    action="store_true",
    help="Translate the audio file to English.",
)

args = parser.parse_args()


def check_not_overwrite(file):
    if (files := glob.glob(glob.escape(file))) and input(
        f'File "{files[0]}" already exists. Overwrite? Default is "no". [(y)es/(n)o] '
    ).lower() not in ["y", "yes"]:
        return files[0]
    return None


# Check if input is a URL
if re.match(r"^https?://", args.input):
    # Download the audio file
    url = args.input
    video_id = getid(url)

    # Check if ./audios/{video_id}.* exists
    audio_file = check_not_overwrite(f"./audios/{video_id}.*") or yt_dlp(url)
else:
    audio_file = args.input
    url = extract_url_from_metadata(audio_file)

# Get the base name of the audio file
base_name, extension = os.path.splitext(os.path.basename(audio_file))

if extension not in [".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"]:
    raise argparse.ArgumentTypeError(
        f"Invalid file extension: {extension}. The file extension must be one of these formats: mp3, mp4, mpeg, mpga, m4a, wav, or webm."
    )

if args.translate:
    base_name += "[English]"

# Check if ./jsons/{base_name}.json exists
transcription_json = f"./jsons/{base_name}.json"
if check_not_overwrite(transcription_json):
    with open(transcription_json) as f:
        transcription = json.load(f)
else:
    transcription = (
        translate_audio(audio_file, args.prompt)
        if args.translate
        else transcribe_audio(audio_file, args.prompt, args.language)
    )
    with open(transcription_json, "w") as f:
        json.dump(transcription, f, indent=4, ensure_ascii=False)

    tags = create_tags_from_transcription(url, transcription)
    with open(f"timestamps/{base_name}.md", "w") as audio_file:
        print(*tags, sep="\\\n", file=audio_file, end="\n")

# Filter out segments with no speech
speech, no_speech = filter_no_speech(transcription)

if no_speech:
    with open(f"./jsons/{base_name}-speech.json", "w") as f:
        json.dump(speech, f, indent=4, ensure_ascii=False)

    speech_tags = create_tags_from_transcription(url, speech)
    with open(f"timestamps/{base_name}-speech.md", "w") as audio_file:
        print(*speech_tags, sep="\\\n", file=audio_file, end="\n")

    with open(f"./jsons/{base_name}-no_speech.json", "w") as f:
        json.dump(no_speech, f, indent=4, ensure_ascii=False)

    no_speech_tags = create_tags_from_transcription(url, no_speech)
    with open(f"timestamps/{base_name}-no_speech.md", "w") as audio_file:
        print(*no_speech_tags, sep="\\\n", file=audio_file, end="\n")
