# transcriber
Generates sheet music from audio files

===================================================================

This single-file tool transcribes piano audio into MIDI, then converts
it into engravable sheet music (MusicXML, optional PDF).

It uses:
  * basic-pitch (Spotify) for audio→MIDI (robust AMT model)
  * music21 for MIDI→MusicXML/PDF engraving

# Installation
------------
## (Recommended) In a fresh virtual environment:
`python -m venv .venv && source .venv/bin/activate`

## System deps 
* macOS:   `brew install ffmpeg musescore`
* Debian:  `sudo apt-get install ffmpeg musescore3`
* Windows: `Install FFmpeg + MuseScore (add to PATH)`

`pip install --upgrade pip`
`pip install -r requirements.txt`

## (Optional but recommended) Configure music21 to find MuseScore for PDF export
Run this once in Python:
>>> import music21 as m21
>>> us = m21.environment.UserSettings()
>>> us['musicxmlPath'] = '/full/path/to/MuseScore4'  or 'mscore' on Linux
Now PDF export will work.

# Usage
-----
```
python transcriber.py input.mp3 \
  --out outdir \
  --bpm 80 \
  --timesig 4/4 \
  --key auto \
  --quant 1/16 \
  --no-pedal  \
  --save-midi --save-musicxml --save-pdf
```

Common flags:
  input.mp3               Path to an MP3/WAV/MIDI
  -o/--out                Output directory (default: alongside input)
  --bpm                   Tempo to notate at (default: auto from MIDI if present, else 90)
  --timesig               Time signature to engrave (default: 4/4)
  --key                   Key for score header: e.g. C, Eb-, F#, or "auto" to analyze
  --quant                 Quantization grid for notation: e.g. 1/8, 1/12 (triplets), 1/16
  --no-pedal              Strip overly-long sustain pedal events from notation
  --save-midi             Export transcribed MIDI (.mid)
  --save-musicxml         Export MusicXML (.musicxml)
  --save-pdf              Export PDF (requires MuseScore/LilyPond configured in music21)
  --disable-quantization  Keep raw timing

# Notes & tips
------------
* Audio quality matters. Use close-miked or clean piano recordings when possible.
* Transcription is hard; results may need light editing in a notation app.
* For swing/triplet feels, consider --quant 1/12.
* For rubato pieces, engraving to a fixed BPM/time signature is approximate.
