"""Bake source SOUNDINFO ranges and channel envelopes into 44.1 kHz PCM.

Input WAVs must be exported from the retained SWF by the pinned JPEXS tool.
The original timeline and MP3 assets remain unchanged.
"""
import argparse
from array import array
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import wave


def segment(samples, channels, event):
    if event.get('sync_stop') or event.get('loop_count'):
        raise ValueError('Stop/loop sound events require separate lifecycle handling')
    envelope = event.get('envelope', [])
    if len(envelope) > 1 or (envelope and envelope[0]['pos44'] != 0):
        raise ValueError('Dynamic envelopes require source interpolation support')
    levels = envelope[0] if envelope else {'left_level': 32768, 'right_level': 32768}
    start = int(event.get('in_point', 0))
    end = min(int(event.get('out_point', len(samples) // channels)), len(samples) // channels)
    if not 0 <= start < end:
        raise ValueError('Invalid source sound range')
    result = array('h')
    for index in range(start, end):
        for channel, key in enumerate(['left_level', 'right_level']):
            sample = samples[index * channels + (channel if channels == 2 else 0)]
            result.append(round(sample * levels[key] / 32768))
    return result, start, end


def build(directory, wavs, ffmpeg):
    timeline = json.loads((directory / 'timeline.json').read_text())
    decoded = {}
    frames = {}
    outputs = directory / 'sound_segments'
    outputs.mkdir(exist_ok=True)
    for frame in timeline['frames']:
        records = []
        for event in frame.get('events', []):
            if event.get('type') != 'start_sound':
                continue
            sound_id = int(event['sound_id'])
            source = wavs / f'{sound_id}.wav'
            if sound_id not in decoded:
                with wave.open(str(source)) as original:
                    channels = original.getnchannels()
                if channels not in [1, 2]:
                    raise ValueError('Unexpected source channel count')
                pcm = subprocess.run([str(ffmpeg), '-v', 'error', '-i', str(source),
                    '-ar', '44100', '-f', 's16le', '-acodec', 'pcm_s16le', '-'],
                    capture_output=True, check=True).stdout
                samples = array('h'); samples.frombytes(pcm)
                if sys.byteorder != 'little': samples.byteswap()
                decoded[sound_id] = samples, channels
            samples, start, end = segment(*decoded[sound_id], event)
            key = hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()[:16]
            path = outputs / f'{sound_id}-{key}.wav'
            if sys.byteorder != 'little': samples.byteswap()
            with wave.open(str(path), 'wb') as stream:
                stream.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
                stream.writeframes(samples.tobytes())
            records.append({'sound_id': sound_id, 'stream': path.relative_to(directory).as_posix(),
                            'start_sample': start, 'end_sample': end, 'sample_count': end-start,
                            'source_event': event, 'source_wav_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        if records: frames[str(frame['frame'])] = records
    result = {'format': 'bvn26-sound-segments-v1', 'sample_rate': 44100,
              'envelope_baked': True, 'source_swf': timeline['source_swf'], 'frames': frames,
              'decoder': 'Pinned JPEXS WAV export; ffmpeg PCM resampling',
              'ffmpeg_version': subprocess.run([str(ffmpeg), '-version'], capture_output=True, text=True, check=True).stdout.splitlines()[0]}
    (directory / 'sound_segments.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--ffmpeg', type=Path, required=True)
    args = parser.parse_args()
    timeline = json.loads((args.directory / 'timeline.json').read_text())
    root = Path(__file__).resolve().parents[2]
    swf = root / timeline['source_swf']['path']
    if hashlib.sha256(swf.read_bytes()).hexdigest() != timeline['source_swf']['sha256']:
        raise ValueError('Retained source SWF hash mismatch')
    with tempfile.TemporaryDirectory(prefix='bvn-sound-segments-') as directory:
        wavs = Path(directory)
        subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(args.ffdec),
            '-format', 'sound:wav', '-export', 'sound', str(wavs), str(swf)],
            capture_output=True, check=True)
        result = build(args.directory, wavs, args.ffmpeg)
    result['ffdec_sha256'] = hashlib.sha256(args.ffdec.read_bytes()).hexdigest()
    (args.directory / 'sound_segments.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'frames': len(result['frames']), 'format': result['format']}))
