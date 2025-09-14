#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from midi_conversion import transcribe_to_midi
from musicxml_generation import engrave_midi_to_musicxml, export_pdf_from_musicxml
from util import _log

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe piano audio files to MIDI and engrave sheet music (MusicXML/PDF)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('audio', type=Path, help='Input audio file (mp3/wav/midi)')
    parser.add_argument('-o', '--out', type=Path, default=None, help='Output directory. Exclude to use same directory as input')

    parser.add_argument('--bpm', type=int, default=None, help='Tempo for engraving')
    parser.add_argument('--timesig', type=str, default='4/4', help='Time signature, e.g. 3/4')
    parser.add_argument('--key', type=str, default='auto', help='Key name or "auto"')
    parser.add_argument('--quant', type=str, default='1/16', help='Quantization grid')
    parser.add_argument('--no-pedal', action='store_true', help='Strip sustain pedal events')

    parser.add_argument('--save-midi', action='store_true', help='Export transcribed MIDI')
    parser.add_argument('--save-musicxml', action='store_true', help='Export MusicXML')
    parser.add_argument('--save-pdf', action='store_true', help='Export PDF (requires MuseScore/LilyPond)')
    parser.add_argument('--disable-quantization', action='store_true', help='Keep raw timing')

    args = parser.parse_args(argv)

    audio_path: Path = args.audio
    if not audio_path.exists():
        parser.error(f"Input file not found: {audio_path}")

    out_dir = args.out or audio_path.with_suffix('').parent
    out_dir.mkdir(parents=True, exist_ok=True)
    midi_input = str(audio_path).lower().endswith(".mid")

    # Acquire MIDI file
    if midi_input:
        _log("Input file is MIDI")
        midi_path = audio_path
    else:
        try:
            midi_path = transcribe_to_midi(audio_path, out_dir)
        except Exception as e:
            _log("ERROR: Basic Pitch transcription failed.")
            _log(str(e))
            return 2

    # Convert MIDI to MusicXML
    musicxml_path = None
    try:
        musicxml_path, _ = engrave_midi_to_musicxml(
            midi_path,
            out_dir,
            bpm=args.bpm,
            timesig=args.timesig,
            key_choice=args.key,
            quant=args.quant,
            strip_pedal=args.no_pedal,
            quantize=not args.disable_quantization,
        )
    except Exception as e:
        _log("ERROR: Engraving (MIDI→MusicXML) failed.")
        _log(str(e))
        return 3

    # Select which artifacts to keep
    if not midi_input and not args.save_midi:
        try:
            _log("Cleaning up midi file")
            midi_path.unlink(missing_ok=True)
        except Exception:
            pass

    pdf_path = None
    if args.save_pdf or args.save_pfd:
        try:
            pdf_path = export_pdf_from_musicxml(musicxml_path)
        except Exception as e:
            _log("WARN: PDF export failed. Ensure MuseScore/LilyPond is installed and configured in music21.")
            _log(str(e))

    if not args.save_musicxml:
        try:
            # If user didn’t ask to keep MusicXML and PDF succeeded, we could remove XML.
            # But keep XML by default; it’s useful for tweaking in notation editors.
            pass
        except Exception:
            pass

    _log("Done.")
    _log(f"Outputs in: {out_dir}")
    if args.save_midi:
        _log(f"  MIDI:     {midi_path}")
    if musicxml_path and args.save_musicxml:
        _log(f"  MusicXML: {musicxml_path}")
    if pdf_path:
        _log(f"  PDF:      {pdf_path}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
