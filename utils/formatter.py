import os, csv, logging

from pathlib import Path

logger = logging.getLogger(__name__)

def styletts2(root_path, meta_file, ignored_speakers=None):
    """Interal dataset formatter."""
    filepath = os.path.join(root_path, meta_file)
    # ensure there are 4 columns for every line
    with open(filepath, "r", encoding="utf8") as f:
        lines = f.readlines()
    num_cols = len(lines[0].split("|"))  # take the first row as reference
    for idx, line in enumerate(lines[1:]):
        if len(line.split("|")) != num_cols:
            logger.warning("Missing column in line %d -> %s", idx + 1, line.strip())
    # load metadata
    with open(Path(root_path) / meta_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")
        metadata = list(reader)
    assert all(x in metadata[0] for x in ["audio_file", "text"])
    speaker_name = None if "speaker_name" in metadata[0] else "coqui"
    emotion_name = None if "emotion_name" in metadata[0] else "neutral"
    items = []
    not_found_counter = 0
    for row in metadata:
        if speaker_name is None and ignored_speakers is not None and row["speaker_name"] in ignored_speakers:
            continue
        audio_path = os.path.join(root_path, row["audio_file"])
        if not os.path.exists(audio_path):
            not_found_counter += 1
            continue
        items.append(
            {
                "text": row["text"],
                "audio_file": audio_path,
                "speaker_name": speaker_name if speaker_name is not None else row["speaker_name"],
                "emotion_name": emotion_name if emotion_name is not None else row["emotion_name"],
                "root_path": root_path,
            }
        )
    if not_found_counter > 0:
        logger.warning("%d files not found", not_found_counter)
    return items
