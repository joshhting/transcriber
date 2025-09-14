from basic_pitch.inference import predict_and_save, ICASSP_2022_MODEL_PATH
from pathlib import Path
from util import _log

def transcribe_to_midi(audio_path: Path, out_dir: Path) -> Path:
    """Run Basic Pitch to get a MIDI file from audio.

    Returns the path to the generated MIDI file.
    """

    audio_path = audio_path.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    _log(f"Transcribing with Basic Pitch → {out_dir} ...")
    # predict_and_save writes files named like <stem>_basic_pitch.mid
    predict_and_save(
        [str(audio_path)],
        str(out_dir),
        save_midi=True,
        save_notes=True,
        sonify_midi=False,
        save_model_outputs=False,
        # model_or_model_path=ICASSP_2022_MODEL_PATH,
        # midi_tempo=90,  # Only used for sonification; engraving sets tempo later.
    )

    stem = audio_path.stem
    candidates = list(out_dir.glob(f"{stem}*basic_pitch*.mid"))
    if not candidates:
        raise RuntimeError("Basic Pitch did not produce a MIDI file.")
    # Pick the most recent candidate (handles re-runs)
    midi_path = max(candidates, key=lambda p: p.stat().st_mtime)
    _log(f"MIDI created: {midi_path}")
    return midi_path