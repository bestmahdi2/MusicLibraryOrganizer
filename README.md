# Music Library Organizer

Check out our introduction video:

[![Watch the video](https://img.youtube.com/vi/dQw4w9WgXcQ/.jpg)](https://www.youtube.com/watch?v=)

This video provides an overview of how to use the Music Library Organizer.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Contributing](#contributing)
- [Linux Users](#linux-users) 
- [Contact](#contact)

## Introduction

The Music Library Organizer is a Python script that identifies audio files using the Shazam API, updates their metadata,
and organizes them into folders by artist. It supports various audio formats and provides a simple command-line
interface for processing files.

## Features

- Identify songs from audio files using the Shazam API.
- Automatically update metadata (title, artist, album, genre, year) in MP3 files.
- Download and embed album cover images.
- Organize processed files into artist-specific folders.
- Handle errors gracefully and log processing results.

## Requirements

- Python 3.x
- Required Python packages:
    - `mutagen`
    - `requests`

You can install the required packages using pip:

```bash
pip install mutagen requests
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/bestmahdi2/MusicLibraryOrganizer.git
   cd MusicLibraryOrganizer
   ```

2. Install the required packages as mentioned above.

3. Obtain an API key from [RapidAPI](https://rapidapi.com/dashydata-dashydata-default/api/shazam-song-recognition-api)
   for the Shazam API and replace `PASTE_YOUR_API_KEY_HERE` in the code.

## Configuration

Before running the script, configure the following settings in the code:

- `RAPID_API_KEY`: Your Shazam API key.
- `SUPPORTED_FILE_FORMATS`: Supported audio formats (default: `.mp3`, `.m4a`, `.wav`).
- `SAMPLE_BYTE_SIZE`: Size of the audio sample sent to the API for recognition (default: `700000` bytes).
- `INPUT_DIR`: Directory containing unprocessed audio files (default: `Input`).
- `OUTPUT_DIR`: Directory for successfully processed files (default: `Output`).
- `FAILED_DIR`: Directory for files that couldn't be processed (default: `Failed`).
- `SORTED_FOLDER`: Directory for organizing processed files by artist (default: `Arranged`).
- `USE_PROXY`: Set to `True` if using a proxy.

## Usage

1. Place your audio files in the `Input` directory.
2. Run the script:
   ```bash
   python audio_file_processor.py
   ```

3. To archive processed files into artist-specific folders, use:
   ```bash
   python audio_file_processor.py --archive
   ```

## How It Works

1. The script reads audio files from the specified input directory.
2. It sends a sample of each audio file to the Shazam API for identification.
3. Upon receiving a response, it extracts metadata and updates the audio file.
4. Successfully processed files are moved to the output directory, while failed files are moved to the failed directory.
5. Optionally, processed files can be organized into folders by artist.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a
pull request.

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Make your changes and commit them (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

## Linux Users

If you are using Linux, ensure you have Python 3 and pip installed. You can install them using your package manager. For example, on Ubuntu, you can run:

```bash
sudo apt update
sudo apt install python3 python3-pip
```

After installing Python and pip, you can follow the same installation steps as mentioned above. If you encounter any permission issues while running the script, you may need to use `sudo` or adjust the permissions of the directories you are working with.

## Contact

For any inquiries or feedback, please contact:

- Your Name - [bestmahdi2@gmail.com](mailto:bestmahdi2@gmail.com)
- GitHub: [bestmahdi2](https://github.com/bestmahdi2)

---

Thank you for using the Music Library Organizer! Happy processing! 🎶

``` 