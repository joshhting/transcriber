import music21 as m21
from typing import Optional, Tuple

from pathlib import Path
from util import _log


def engrave_midi_to_musicxml(
    midi_path: Path,
    out_dir: Path,
    bpm: Optional[int] = None,
    timesig: str = "4/4",
    key_choice: str = "auto",
    quant: str = "1/16",
    strip_pedal: bool = False,
    quantize: bool = True,
) -> Tuple[Path, Optional[Path]]:
    """Convert MIDI → MusicXML (and optionally PDF) via music21.

    Returns (musicxml_path, pdf_path_or_None).
    """

    out_dir.mkdir(parents=True, exist_ok=True)

    _log("Loading MIDI into music21 ...")
    s = m21.converter.parse(str(midi_path))

    # Create a score and split by parts if needed
    s = s.flatten().chordify(False) if len(s.parts) == 0 else s
    score = m21.stream.Score()

    # Use two staves by pitch (piano grand staff) if polyphonic
    upper = m21.stream.Part(id='RH')
    lower = m21.stream.Part(id='LH')

    # Meter & tempo
    try:
        numer, denom = [int(x) for x in timesig.split('/')]
        score.insert(0, m21.meter.TimeSignature(timesig))
    except Exception:
        score.insert(0, m21.meter.TimeSignature('4/4'))

    if bpm is None:
        # Try to extract from MIDI; else default
        tempos = [el for el in s.recurse().getElementsByClass(m21.tempo.MetronomeMark)]
        bpm = int(round(tempos[0].number)) if tempos else 90
    score.insert(0, m21.tempo.MetronomeMark(number=bpm))

    # Key signature
    if key_choice and key_choice.lower() != 'auto':
        try:
            score.insert(0, m21.key.Key(key_choice))
        except Exception:
            pass
    else:
        analyzed = estimate_key_with_music21(s)
        if analyzed:
            try:
                score.insert(0, m21.key.Key(analyzed))
            except Exception:
                pass

    # Optional: strip overly-long sustain pedal (helps notation readability)
    if strip_pedal:
        for ped in list(s.recurse().getElementsByClass(m21.expressions.Pedal)):
            ped.active = False
            ped.end()

    # Simple split: allocate notes to hands by pitch threshold (middle C)
    middle_c = m21.pitch.Pitch('C4').midi
    for n in s.recurse().notesAndRests:
        if n.isRest:
            tgt = upper
            tgt.append(n)
        elif isinstance(n, m21.note.Note):
            tgt = upper if n.pitch.midi >= middle_c else lower
            tgt.append(n)
        elif isinstance(n, m21.chord.Chord):
            # Split the chord: assign each note separately
            for p in n.pitches:
                note = m21.note.Note(p, quarterLength=n.quarterLength)
                tgt = upper if p.midi >= middle_c else lower
                tgt.append(note)

    # Quantization: convert text like '1/16' → quarterLength (0.25)
    try:
        if '/' in quant:
            q_num, q_den = quant.split('/')
            q = float(q_num) / float(q_den)
        else:
            q = float(quant)
    except Exception:
        q = 0.25  # default 1/16

    if quantize:
        _log("Quantizing score")
        for part in (upper, lower):
            # Make measures and quantize note durations
            part.makeMeasures(inPlace=True)
            # Coerce durations to the grid
            for n in part.recurse().notesAndRests:
                # Snap offset and duration to nearest grid
                def _snap(x: float, grid: float) -> float:
                    return round(x / grid) * grid
                try:
                    n.offset = _snap(n.offset, q)
                    if hasattr(n, 'duration') and n.duration is not None:
                        n.duration.quarterLength = max(q, _snap(n.duration.quarterLength, q))
                except Exception:
                    pass
    else:
        _log("Skipping score quantization")

    # Wrap into a Piano grand staff
    upper.insert(0, m21.clef.TrebleClef())
    lower.insert(0, m21.clef.BassClef())

    p = m21.instrument.Piano()
    upper.insert(0, p)
    lower.insert(0, p)

    score.append(upper)
    score.append(lower)

    # Title
    score.metadata = m21.metadata.Metadata()
    score.metadata.title = midi_path.stem.replace('_', ' ').title()
    score.metadata.composer = "Transcribed by Piano Transcriber"

    musicxml_path = out_dir / f"{midi_path.stem}.musicxml"
    _log(f"Writing MusicXML → {musicxml_path}")
    score.write('musicxml', fp=str(musicxml_path))

    return musicxml_path, None  # PDF is exported in main() if requested


def export_pdf_from_musicxml(musicxml_path: Path) -> Path:
    """Try to export a PDF from MusicXML via music21 (MuseScore/LilyPond required)."""
    s = m21.converter.parse(str(musicxml_path))
    pdf_path = musicxml_path.with_suffix('.pdf')
    _log(f"Attempting PDF export via music21 → {pdf_path}")
    s.write('musicxml.pdf', fp=str(pdf_path))
    return pdf_path


def estimate_key_with_music21(stream) -> Optional[str]:
    """Try to analyze key signature using music21; return a readable key string."""
    try:
        k = stream.analyze('key')
        # music21 uses e.g., 'E- major' for Eb; convert a touch
        tonic = k.tonic.name.replace('-','b')
        mode = 'minor' if k.mode == 'minor' else 'major'
        return f"{tonic} {mode}"
    except Exception:
        return None
