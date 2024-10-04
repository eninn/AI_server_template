import librosa
import soundfile as sf

def resample_and_save_wav(input_path, output_path, target_sample_rate=22050):
    """Resample a WAV file to the target sample rate and save it to the output path."""
    audio, sample_rate = librosa.load(input_path, sr=None)

    if sample_rate != target_sample_rate:
        audio_resampled = librosa.resample(audio, orig_sr=sample_rate, target_sr=target_sample_rate)
    else:
        audio_resampled = audio

    sf.write(output_path, audio_resampled, target_sample_rate)