import os
import re
import sys
import shutil
import pathlib
import requests
from mutagen.mp3 import MP3
from mutagen import MutagenError
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC, APIC

# Configuration - Change these settings as needed
RAPID_API_KEY = "PASTE_YOUR_API_KEY_HERE"  # API key for Shazam
SUPPORTED_FILE_FORMATS = (".mp3", ".m4a", ".wav")  # Supported audio (or video) formats
SAMPLE_BYTE_SIZE = 700_000  # Size of the sample sent to the API for recognition
INPUT_DIR = "Input"  # Folder containing unprocessed audio files
OUTPUT_DIR = "Output"  # Folder for successfully processed files
FAILED_DIR = "Failed"  # Folder for files that couldn't be processed
SORTED_FOLDER = "Arranged"  # Folder for organizing processed files by artist
USE_PROXY = False  # Set to True if using a proxy

# API Configuration
SHAZAM_API_URL = "https://shazam-song-recognition-api.p.rapidapi.com/recognize/file"
SHAZAM_HEADERS = {
    "x-rapidapi-key": RAPID_API_KEY,
    "x-rapidapi-host": "shazam-song-recognition-api.p.rapidapi.com",
    "Content-Type": "application/octet-stream"
}


def process_audio_file(file_path):
    """Processes an audio file: identifies it, updates metadata, and moves it to the output folder."""

    file_path = pathlib.Path(file_path)
    ext = file_path.suffix

    # Read a small portion of the file for song identification
    with open(file_path, "rb") as audio_file:
        audio_sample = audio_file.read(SAMPLE_BYTE_SIZE)

    # Send request to Shazam API
    proxies = {"ADD_YOUR_PROXY_HERE": "type://user:pass@ip:port"} if USE_PROXY else None
    response = requests.post(SHAZAM_API_URL, headers=SHAZAM_HEADERS, data=audio_sample, proxies=proxies)

    if response.status_code == 451:
        print("❌ Error 451: This request is blocked. Check your API key or region!")
        return False

    response.raise_for_status()  # Check if request was successful
    track_data = response.json().get("track")  # Extract song information

    if not track_data or not track_data.get("sections"):
        print("❌ The API returned no track information.")
        return False

    metadata = extract_metadata(track_data)  # Extract relevant metadata
    new_filename = f"{metadata['artist']} - {metadata['title']}{ext}"
    sanitized_file_name = sanitize_filename(new_filename)
    new_file_path = os.path.join(OUTPUT_DIR, sanitized_file_name)

    if ext == ".mp3" and not update_audio_tags(file_path, metadata):
        move_to_failed(file_path)
        return False

    return move_file(file_path, new_file_path)


def move_file(file_path, new_file_path):
    """Moves the file to the specified new location and handles errors."""

    try:
        shutil.move(file_path, new_file_path)
        print(f"✅ Processed: {os.path.basename(file_path)} → {os.path.basename(new_file_path)}")
        return True

    except (FileNotFoundError, PermissionError, shutil.Error, OSError) as e:
        print(f"❌ Error moving file {file_path}: {e}")
        return False


def extract_metadata(track_data):
    """Extracts and returns song metadata from the API response."""

    try:
        album = track_data.get("sections", [{}])[0].get("metadata", [{}])[0].get("text", "Unknown Album")
    except IndexError:
        album = "Unknown Album"

    try:
        genre = track_data.get("genres", {}).get("primary", "Unknown Genre")
    except IndexError:
        genre = "Unknown Genre"

    try:
        year = track_data.get("sections", [{}])[0].get("metadata", [{}])[2].get("text", "Unknown Year")
    except IndexError:
        year = "Unknown Year"

    try:
        # Extract cover image URLs
        cover_url = track_data.get("images", {}).get("coverarthq", "")  # High-quality cover image
    except IndexError:
        cover_url = ""

    if not cover_url:  # Fallback to coverart if coverarthq is not available
        try:
            cover_url = track_data.get("images", {}).get("coverart", "")
        except IndexError:
            cover_url = ""

    return {
        "title": track_data.get("title"),
        "artist": track_data.get("subtitle"),
        "album": album,
        "genre": genre,
        "year": year,
        "cover_url": cover_url
    }


def update_audio_tags(file_path, metadata):
    """Adds metadata (title, artist, album, genre, year, cover image) to the MP3 file."""

    try:
        audio = MP3(file_path, ID3=ID3)
        audio.tags = ID3()  # Initialize tags
    except MutagenError:
        print(f"❌ Permission denied: Unable to load \"{file_path}\".")
        return False

    # Add basic metadata tags
    tags = {"title": TIT2, "artist": TPE1, "album": TALB, "genre": TCON, "year": TDRC}
    for tag, frame in tags.items():
        if metadata.get(tag):
            audio.tags.add(frame(encoding=3, text=metadata[tag]))

    # Add album cover image if available
    if metadata["cover_url"]:
        try:
            response = requests.get(metadata["cover_url"], timeout=10)
            response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
            cover_data = response.content
            audio.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=cover_data))
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"⚠️ Failed to download cover image: {e}")
            return False

    try:
        audio.save()
    except MutagenError:
        print(f"❌ Permission denied: Unable to save metadata to \"{file_path}\". Probably your file is not an MP3!")
        return False

    return True


def sanitize_filename(filename):
    """Removes or replaces invalid characters in the filename."""

    return re.sub(r'[<>:"/\\|?*]', '_', filename)


def move_to_failed(file_path):
    """Moves unprocessed files to the Failed directory for review."""

    try:
        shutil.move(file_path, os.path.join(FAILED_DIR, os.path.basename(file_path)))
        print(f"❌ Moved to failed directory: {file_path}")
    except (FileNotFoundError, PermissionError, shutil.Error, OSError) as e:
        print(f"❌ Error moving file {file_path}: {e}")


def archive_mp3_files():
    """Sorts processed songs into folders by artist name."""

    os.makedirs(SORTED_FOLDER, exist_ok=True)
    mp3_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")]

    for mp3_file in mp3_files:
        singer = mp3_file.split(" - ")[0] if " - " in mp3_file else "Unknown Artist"
        singer_folder = os.path.join(SORTED_FOLDER, singer)
        os.makedirs(singer_folder, exist_ok=True)

        base_name, extension = os.path.splitext(mp3_file)
        dest_path = os.path.join(singer_folder, mp3_file)
        counter = 1

        while os.path.exists(dest_path):
            dest_path = os.path.join(singer_folder, f"{base_name} ({counter}){extension}")
            counter += 1

        move_file(os.path.join(OUTPUT_DIR, mp3_file), dest_path)


def main():
    """Main function to process audio files."""

    # Ensure necessary directories exist (this could be moved outside main if needed)
    for folder in [OUTPUT_DIR, FAILED_DIR]:
        os.makedirs(folder, exist_ok=True)

    if any(arg in sys.argv for arg in ("--archive", "-a")):
        archive_mp3_files()
        return

    if RAPID_API_KEY == "PASTE_YOUR_API_KEY_HERE" or not RAPID_API_KEY:
        print("✏️ Please fill in the RAPID_API_KEY variable with the API key you copied from the website.")
        return

    try:
        # Process all supported audio files in the input directory
        audio_files = [f for f in os.listdir(INPUT_DIR) if
                       os.path.isfile(os.path.join(INPUT_DIR, f)) and f.lower().endswith(SUPPORTED_FILE_FORMATS)]

        if not audio_files:
            print("❌ There are no audio files in this directory.")
            return

        total_files = len(audio_files)
        for i, audio_file in enumerate(audio_files, 1):
            file_path = os.path.join(INPUT_DIR, audio_file)
            print(f"➖ [{i}/{total_files}] Processing: {audio_file}")
            try:
                process_audio_file(file_path)
            except FileNotFoundError:
                print(f"❌ This file does not exist: {file_path}")
            except PermissionError:
                print(f"❌ You don't have the right permission for this file: {file_path}")

    except FileNotFoundError:
        print(f"❌ The system cannot find the path specified: {INPUT_DIR}")
    except PermissionError:
        print(f"❌ You don't have the right permission for this path: {INPUT_DIR}")


if __name__ == "__main__":
    main()
    print(f"\n📍 Program Ended!")
