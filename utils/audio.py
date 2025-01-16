import io, os, glob, shutil, multiprocessing
import wave, contextlib, librosa, ffmpeg

import soundfile as sf
import numpy as np
import scipy.signal as signal
import pyrubberband as pyrb

from functools import partial
from pydub import AudioSegment
from pydub.silence import split_on_silence
from tqdm import tqdm  # tqdm 라이브러리 임포트
from scipy.signal import resample, butter, lfilter
from demucs.separate import main as demucs_run

def load_wav(input_path:str, sample_rate:int=None):
    return librosa.load(input_path, sr=sample_rate)

def resample_wav(wav:np.ndarray, orig_sr:int, new_sr:int):
    return librosa.resample(wav, orig_sr=orig_sr, target_sr=new_sr)

def save_wav(wav:np.ndarray, output_path:str, sample_rate:int):
    sf.write(output_path, wav, sample_rate)

def get_wav_duration(file_path):
    try:
        with contextlib.closing(wave.open(file_path, 'r')) as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            return duration
    except wave.Error as e:
        print(f"Error processing {file_path}: {e}")
        return 0

def print_duration(duration:int):
    total_seconds = duration
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)    
    print(f"Total duration: {hours} hours, {minutes} minutes, {seconds} seconds")

def load_bytes_to_wav(audio_bytes:bytes, sample_rate:int):
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    wav_bytes_io = io.BytesIO()
    audio.export(wav_bytes_io, format='wav')
    wav_bytes_io.seek(0)
    wav, sr = librosa.load(wav_bytes_io, sr=sample_rate)
    return wav, sr

def load_wav_to_bytes(wav:np.ndarray, sample_rate:int):
    wav_buffer = io.BytesIO()
    sf.write(wav_buffer, wav, sample_rate, format='WAV')
        
    wav_buffer.seek(0)

    return wav_buffer, sample_rate

def load_audiosegment(input_path:str):
    return AudioSegment.from_file(input_path)

def export_audiosegment(segment:AudioSegment, output_path:str, fmt:str="wav"):
    segment.export(output_path, format=fmt, bitrate="320k")

def wav_to_audiosegment(wav, sample_rate):
    wav = np.int16(wav / np.max(np.abs(wav)) * 32767)
    
    audio_segment = AudioSegment(
        wav.tobytes(), 
        frame_rate=sample_rate, 
        sample_width=2,  # 16-bit (2 bytes per sample)
        channels=1  # Mono
    )
    return audio_segment

def audiosegment_to_wav(audio_segment):
    return np.array(audio_segment.get_array_of_samples())
    
def remove_silence_and_add_margin(audio, silence_thresh=-40, min_silence_len=300, keep_silence=300):
    non_silent_audio = split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence
    )
    
    if len(non_silent_audio) <= 1:
        return None

    combined_audio = non_silent_audio[0]
    
    for part in non_silent_audio[1:]:
        combined_audio += part  

    return combined_audio

def process_audio_file(wav_file, folder_path, backup_folder):
    try:
        # 오디오 파일 불러오기
        audio = AudioSegment.from_wav(wav_file)

        # 최초 발화 이전과 종료 이후의 무음만 제거
        processed_audio = remove_silence_and_add_margin(audio, silence_thresh=-40, min_silence_len=300, keep_silence=300)
        
        if processed_audio:
            # 기존 파일을 백업 폴더로 이동
            backup_path = os.path.join(backup_folder, os.path.basename(wav_file))
            shutil.move(wav_file, backup_path)
            # print(f"{wav_file}을(를) 백업 폴더로 이동했습니다.")
        
            # 무음이 제거된 오디오를 원래 경로에 저장
            new_file_path = os.path.join(folder_path, os.path.basename(wav_file))
            processed_audio.export(new_file_path, format="wav")
            # print(f"무음 구간이 제거된 {wav_file}을(를) {new_file_path}에 저장했습니다.")


    except Exception as e:
        print(f"파일 {wav_file} 처리 중 오류 발생: {e}")

def remove_silence_and_backup_multiprocess(folder_path, backup_folder):
    # Backup 폴더가 없으면 생성
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    # WAV 파일 경로 목록
    wav_files = glob.glob(os.path.join(folder_path, "*.wav"))

    # 멀티프로세싱을 위한 풀 생성
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        # tqdm을 pool.imap_unordered에 직접 연결하여 진행상황 표시
        # pool.starmap을 사용하여 각 작업에 (wav_file, folder_path, backup_folder)를 전달
        for _ in tqdm(pool.starmap(process_audio_file, [(wav_file, folder_path, backup_folder) for wav_file in wav_files]), total=len(wav_files), desc=folder_path):
            pass  # 각 작업은 pool.starmap가 처리

def noise_reduction_filter(audio: np.ndarray, sr: int) -> np.ndarray:
    """
    주파수 영역에서 노이즈를 감소시키기 위한 필터링.
    """
    # 노이즈 감소를 위한 Spectral Subtraction 기법
    # 음성의 주파수 성분을 추출하고, 노이즈 성분을 제거
    S, phase = librosa.magphase(librosa.stft(audio))
    avg_noise = np.mean(S, axis=1, keepdims=True)  # 노이즈 추정 (평균값 사용)
    S_denoised = np.maximum(S - avg_noise, 0)  # 노이즈 제거
    audio_denoised = librosa.istft(S_denoised * phase)
    return audio_denoised

def bandpass_filter_audio(audio: np.ndarray, sr: int) -> np.ndarray:
    """
    대역 통과 필터를 통해 300Hz ~ 3kHz 사이의 신호만 남기기.
    """
    # 대역 통과 필터 정의 (300Hz ~ 3kHz)
    lowcut = 300.0
    highcut = 3000.0
    nyquist = 0.5 * sr
    low = lowcut / nyquist
    high = highcut / nyquist

    # 필터 설계
    b, a = signal.butter(4, [low, high], btype='band')
    filtered_audio = signal.filtfilt(b, a, audio)
    return filtered_audio

def pitch_smoothing_filter(audio: np.ndarray, sr: int) -> np.ndarray:
    """
    피치를 스무딩하여 떨림을 줄이는 필터.
    """
    # librosa를 사용하여 피치를 추출하고 수정
    # 피치 추출
    pitches, magnitudes = librosa.core.piptrack(y=audio, sr=sr)

    # 피치가 급격하게 변하지 않도록 일정 간격으로 피치를 스무딩
    smoothed_pitches = np.array([np.mean(pitch[pitch > 0]) for pitch in pitches.T])
    smoothed_audio = librosa.effects.harmonic(audio)  # 고조파 성분 강조
    return smoothed_audio

def control_audio_speed_ffmpeg(audio: np.ndarray, sr: int, speed_rate: float) -> np.ndarray:
    """
    FFmpeg의 atempo 필터를 사용하여 오디오의 재생 속도를 조절하고, 결과를 NumPy ndarray로 반환합니다.

    :param audio: 입력 오디오 신호 (1D 또는 2D NumPy ndarray). Shape: (samples,) 또는 (samples, channels)
    :param sr: 샘플 레이트 (Hz)
    :param speed_rate: 속도 비율 (>1.0: 빠르게, <1.0: 느리게)
    :return: 속도가 조절된 오디오 신호 (NumPy ndarray)
    """
    # 오디오가 float32 형식인지 확인하고 아니면 변환
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    # 오디오가 1D (모노) 또는 2D (스테레오)인지 확인
    if audio.ndim == 1:
        channels = 1
    else:
        channels = audio.shape[1]

    # NumPy 배열을 바이트로 변환
    audio_bytes = audio.tobytes()

    # atempo 필터는 0.5~2.0 범위의 속도 비율만 지원
    # 그 외의 속도 비율은 여러 개의 atempo 필터를 연속으로 적용하여 처리
    factors = []
    remaining_speed = speed_rate

    while remaining_speed < 0.5 or remaining_speed > 2.0:
        if remaining_speed < 0.5:
            factors.append(0.5)
            remaining_speed /= 0.5
        elif remaining_speed > 2.0:
            factors.append(2.0)
            remaining_speed /= 2.0

    factors.append(remaining_speed)

    # atempo 필터 체인 생성
    atempo_filter = ",".join([f"atempo={f}" for f in factors])

    try:
        # FFmpeg 명령어 구성
        process = (
            ffmpeg
            .input('pipe:0', format='f32le', ac=channels, ar=sr)
        )

        # 각 atempo 필터를 순차적으로 적용
        for factor in factors:
            process = process.filter('atempo', factor)

        # 결과를 raw float32 형태로 출력
        process = process.output('pipe:1', format='f32le', ac=channels, ar=sr)

        # FFmpeg 프로세스 실행
        out, _ = process.run(input=audio_bytes, capture_stdout=True, capture_stderr=True)

        # 출력 데이터를 NumPy 배열로 변환
        new_audio = np.frombuffer(out, dtype=np.float32)

        # 오디오가 스테레오인 경우, 채널을 유지하도록 reshape
        if channels > 1:
            new_audio = new_audio.reshape(-1, channels)

        return new_audio, sr

    except ffmpeg.Error as e:
        print('FFmpeg error:', e.stderr.decode())
        raise e
    
def bandpass_filter(audio, sr, lowcut, highcut, order=5):
    """
    대역통과 필터를 설계하고 데이터를 필터링합니다.
    
    :param data: 입력 오디오 신호 (1D numpy 배열)
    :param lowcut: 필터의 하한 주파수 (Hz)
    :param highcut: 필터의 상한 주파수 (Hz)
    :param sr: 샘플 레이트 (Hz)
    :param order: 필터의 차수
    :return: 필터링된 오디오 신호
    """
    nyquist = 0.5 * sr
    low = lowcut / nyquist
    high = highcut / nyquist
    # Butterworth 대역통과 필터 설계
    b, a = butter(order, [low, high], btype='band')
    y = lfilter(b, a, audio)
    return y, sr

def demucs_inference(input_audio_path:str, output_dir:str, model_name:str, sample_rate:int, stems:str='vocals'):
    input_audio_stem = os.path.basename(input_audio_path).split('.')[0]
    vocals_path = os.path.join(output_dir, model_name, input_audio_stem, f"{stems}.mp3")
    # "https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/f7e0c4bc-ba3fe64a.th" to /home/ubuntu/.cache/torch/hub/checkpoints/f7e0c4bc-ba3fe64a.th

    demucs_run(["--mp3", 
                "--two-stems", "vocals", 
                "-n", model_name,
                "-o", output_dir,
                "--filename", "{track}/{stem}.{ext}",
                input_audio_path])
    
    y, sr = librosa.load(vocals_path, sample_rate)
    shutil.rmtree(os.path.join(output_dir, model_name, input_audio_stem))   

    return y, sr

def demucs_inference_file(input_audio_path:str, output_audio_path:str, output_dir:str, model_name:str, stems:str='vocals'):
    input_audio_stem = os.path.basename(input_audio_path).split('.')[0]
    vocals_path = os.path.join(output_dir, model_name, input_audio_stem, f"{stems}.mp3")
    # "https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/f7e0c4bc-ba3fe64a.th" to /home/ubuntu/.cache/torch/hub/checkpoints/f7e0c4bc-ba3fe64a.th

    demucs_run(["--mp3", 
                "--two-stems", "vocals", 
                "-n", model_name,
                "-o", output_dir,
                "--filename", "{track}/{stem}.{ext}",
                input_audio_path])
    
    shutil.move(vocals_path, output_audio_path)
    shutil.rmtree(os.path.join(output_dir, model_name, input_audio_stem))
