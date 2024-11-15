# Audio Transcription App

A web application that transcribes audio files into text documents using AI. The app supports multiple audio formats and provides real-time progress tracking.

## Features

- Supports multiple audio formats (.m4a, .mp3, .wav, .aac, .wma, .ogg)
- Real-time transcription progress tracking
- GPU-accelerated processing
- Output in DOCX format
- Cross-platform support (Windows, Linux, MacOS)

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- NVIDIA GPU (recommended) with CUDA support

## Installation

### For Windows Users

1. Clone this repository
2. Open PowerShell and navigate to the project directory
3. Run the setup script:

```
.\setup.ps1
```

4. Start the application:

```
.\run.ps1
```

### For Linux/MacOS Users

1. Clone this repository
2. Open terminal and navigate to the project directory
3. Give execution permission to the scripts:

```
chmod +x setup.sh run.sh
```

4. Run the setup script:

```
./setup.sh
```

5. Start the application:

```
./run.sh
```

## Usage

1. Open your browser and go to `http://localhost:3000`
2. Click "Choose File" and select an audio file
3. Click "Avvia Trascrizione" to start the transcription
4. Wait for the process to complete
5. The transcribed document will be automatically downloaded as a DOCX file

## Supported File Formats

- .m4a
- .mp3
- .wav
- .aac
- .wma
- .ogg

## Technical Details

### Backend

- FastAPI for the REST API
- OpenAI Whisper for audio transcription
- PyTorch for GPU acceleration
- Python-docx for document generation

### Frontend

- React with TypeScript
- Axios for API communication
- Real-time progress tracking

## Project Structure

/audio-transcription-app
├── backend/
│ ├── main.py
│ ├── requirements.txt
│ ├── temp/
│ └── output/
├── frontend/
│ ├── src/
│ ├── public/
│ └── package.json
├── setup.sh
├── run.sh
├── setup.ps1
└── run.ps1

## Error Handling

The application includes comprehensive error handling for:

- Unsupported file formats
- File upload failures
- Transcription errors
- Network issues

## Cleanup

The application automatically:

- Removes temporary files after processing
- Cleans up old jobs (older than 24 hours)
- Manages GPU memory efficiently

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
