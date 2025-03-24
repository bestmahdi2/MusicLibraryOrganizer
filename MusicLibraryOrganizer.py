import os
import sys
import shutil
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC, APIC

# Configuration - Change these settings as needed
RAPID_API_KEY = "PASTE_YOUR_API_KEY_HERE"  # API key for Shazam
SUPPORTED_FILE_FORMATS = (".mp3", ".m4a", ".wav")  # Supported audio(or video) formats
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

    try:
        # Read a small portion of the file for song identification
        with open(file_path, "rb") as audio_file:
            audio_sample = audio_file.read(SAMPLE_BYTE_SIZE)

        # Send request to Shazam API
        if USE_PROXY:
            response = requests.post(SHAZAM_API_URL, headers=SHAZAM_HEADERS, data=audio_sample)
        else:
            response = requests.post(SHAZAM_API_URL, headers=SHAZAM_HEADERS, data=audio_sample,
                                     proxies={"ADD_YOUR_PROXY_HERE": "type://user:pass@ip:port"})

        response.raise_for_status()  # Check if request was successful
        track_data = response.json().get("track")  # Extract song information

        if not track_data:
            raise ValueError("Shazam API returned no track information.")

        metadata = extract_metadata(track_data)  # Extract relevant metadata

        # Create new filename in the format: 'Artist - Title.mp3'
        new_filename = f"{metadata['artist']} - {metadata['title']}.mp3".replace("/", "_")
        new_file_path = os.path.join(OUTPUT_DIR, new_filename)

        update_audio_tags(file_path, metadata)  # Add metadata to file
        shutil.move(file_path, new_file_path)  # Move file to output folder

        print(f"✅ Processed: {os.path.basename(file_path)} → {new_filename}")
        return True  # Indicate successful processing

    except (requests.exceptions.RequestException, ValueError, AttributeError, OSError) as e:  # Catch expected errors
        print(f"❌ Error processing {os.path.basename(file_path)}: {e}")
        move_to_failed(file_path)
        return False


def extract_metadata(track_data):
    """Extracts and returns song metadata from the API response."""

    album = track_data.get("sections", [{}])[0].get("metadata", [{}])[0].get("text", "Unknown Album")
    genre = track_data.get("genres", {}).get("primary", "Unknown Genre")
    year = track_data.get("sections", [{}])[0].get("metadata", [{}])[2].get("text", "Unknown Year")
    cover_url = track_data.get("images", {}).get("coverarthq", "")

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

    audio = MP3(file_path, ID3=ID3)
    audio.tags = ID3()

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

    audio.save()


def move_to_failed(file_path):
    """Moves unprocessed files to the Failed directory for review."""

    try:
        shutil.move(file_path, os.path.join(FAILED_DIR, os.path.basename(file_path)))
    except OSError as e:  # Handle potential file move errors
        print(f"❌ Error moving file to failed directory: {e}")


def archive_files():
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

        shutil.move(os.path.join(OUTPUT_DIR, mp3_file), dest_path)
        print(f"Moved: {mp3_file} → {dest_path}")


if __name__ == "__main__":
    # Ensure necessary directories exist
    for folder in [OUTPUT_DIR, FAILED_DIR, FAILED_DIR]:
        os.makedirs(folder, exist_ok=True)

    if "-archive" in sys.argv:
        archive_files()

    else:
        # Process all supported audio files in the input directory
        audio_files = [f for f in os.listdir(INPUT_DIR) if
                       os.path.isfile(os.path.join(INPUT_DIR, f)) and f.lower().endswith(SUPPORTED_FILE_FORMATS)]

        for i, audio_file in enumerate(audio_files, 1):
            file_path = os.path.join(INPUT_DIR, audio_file)
            print(f"➖ {i}/{len(audio_files)} Processing: {audio_file}")
            process_audio_file(file_path)
