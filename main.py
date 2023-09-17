import argparse
import logging
import pysrt
import time
from os.path import exists
from googletrans import Translator


TRANSLATOR = Translator()
SENTENCE_DELIMITERS = [".", "!", "?", ".\"", ".)"]


def is_completed_sentence(s):
    s = s.strip()
    return bool(s and any(map(s.endswith, SENTENCE_DELIMITERS)))


def translate(s, retry = 1):
    try:
        tr = TRANSLATOR.translate(s, src="fi", dest="en")
        tr = tr.text \
            .replace("?", "? ") \
            .replace(" -", "-") \
            .replace(" \"", "\"") \
            .replace(",\"", ", \"") \
            .replace(".(", ". (")
        return tr
    except Exception:
        if retry < 5:
            time.sleep((retry) * 60)
            translate(s, retry + 1)
        else:
            logging.error(f"Error translating: {s}")
    return ""


def process(in_file, out_file):
    cues = pysrt.open(in_file)
    lines = []
    lines_per_cue = {cue.index: len(cue.text.splitlines()) for cue in cues}

    # Translation pass
    for index, cue in enumerate(cues):
        cue.text = cue.text
        if not cue.text:
            continue
        i = index
        while not is_completed_sentence(cue.text):
            cue.text = cue.text + "\n" + cues[i + 1].text
            cues[i + 1].text = ""
            i = i + 1
        cue.text = translate(cue.text).strip()
        lines = lines + cue.text.splitlines()
        print(f"{int((index / len(cues)) * 100)}%", end="\r", flush=True)

    # Cue re-index pass
    line_index = 0
    lines = [line for line in lines if line]
    for cue in cues:
        n = lines_per_cue.get(cue.index)
        result = "\n".join(lines[line_index:n + line_index])
        line_index = line_index + n
        cue.text = result

    cues.save(out_file, encoding="utf-8")


def is_srt(f):
    if not exists(f):
        raise argparse.ArgumentTypeError("File does not exist.")
    if not len(pysrt.open(f)):
        raise argparse.ArgumentTypeError("Not a valid SRT file.")
    return f


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="translateSRT")
    parser.add_argument("-i", "--input", type=is_srt, help="Input SRT file")
    parser.add_argument("output", type=str, help="Output SRT file")
    args = parser.parse_args()
    process(args.input, args.output)
