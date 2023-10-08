import json
import re
import subprocess


def extract_metadata(file_path):
    meta_data = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            file_path,
        ],
        chekc=True,
        capture_output=True,
    ).stdout
    return json.loads(meta_data)


def extract_url_from_metadata(file_path):
    metadata = extract_metadata(file_path)
    try:
        url = metadata["format"]["tags"]["comment"]
    except KeyError as e:
        file = file_path.replace('"', '\\"')
        print(f'KeyError: {e} in the metadata of "{file}"')
        url = None
    return url


def getid(url):
    video_id = subprocess.run(
        ["yt-dlp", "--get-id", url], text=True, check=True, capture_output=True
    ).stdout.strip()
    return video_id


def yt_dlp(url):
    output = subprocess.run(
        [
            "yt-dlp",
            "--format",
            "bestaudio/best",
            "--format-sort",
            "+size,+br,+res,+fps",
            "--extract-audio",
            "--paths",
            "./audios",
            "--output",
            "%(id)s.%(ext)s",
            "--embed-metadata",
            url,
        ],
        text=True,
        check=True,
        capture_output=True,
    ).stdout
    destination = re.findall(
        r"\[(?:.*)\] (?:Destination: (.*)|(.*) has already been downloaded)",
        output,
    )[-1]
    destination = destination[0] or destination[1]
    return destination
