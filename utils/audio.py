import io, os, glob, shutil, multiprocessing
import wave, contextlib, librosa

import soundfile as sf
import numpy as np

from functools import partial
from pydub import AudioSegment
from pydub.silence import split_on_silence
from tqdm import tqdm  # tqdm 라이브러리 임포트


def resample_and_save_wav(input_path:str, output_path:str, target_sample_rate:int=22050):
    audio, sample_rate = librosa.load(input_path, sr=None)
    if sample_rate != target_sample_rate:
        audio_resampled = librosa.resample(audio, orig_sr=sample_rate, target_sr=target_sample_rate)
        resampled = True
    else:
        audio_resampled = audio
        resampled = False

    if not resampled and input_path == output_path:
        pass
    else:
        sf.write(output_path, audio_resampled, target_sample_rate)

def load_bytes_to_wav(audio_bytes:bytes, sample_rate:int):
    return librosa.load(io.BytesIO(audio_bytes), sr=sample_rate)

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

def process_directory(root_dir, pool):
    wav_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if f.lower().endswith(".wav"):
                wav_files.append(os.path.join(dirpath, f))
    
    total_duration = sum(pool.map(get_wav_duration, wav_files))
    return total_duration

def calculate_total_wav_duration(root_dir):
    # Create a pool of worker processes
    with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
        total_duration = process_directory(root_dir, pool)
    total_duration = int(total_duration)
    print_duration(total_duration)
    return total_duration

def print_duration(duration:int):
    total_seconds = duration
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    print(f"Total duration: {hours} hours, {minutes} minutes, {seconds} seconds")

def remove_silence_and_add_margin(audio, silence_thresh=-40, min_silence_len=300, keep_silence=300):
    """
    주어진 오디오에서 무음 구간을 제거하고, 구간들 간에 지정된 마진(margin_ms)을 추가하여 결합합니다.
    
    :param audio: 입력 오디오 (pydub AudioSegment)
    :param silence_thresh: 무음 구간을 정의할 때 기준이 되는 데시벨
    :param min_silence_len: 무음 구간으로 간주되는 최소 시간 (밀리초)
    :param margin_ms: 각 음성 구간 사이에 추가할 마진 시간 (밀리초)
    :return: 마진을 추가한 오디오
    """
    # 무음 구간을 기준으로 음성을 분리
    non_silent_audio = split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence
    )
    
    # 만약 음성이 하나만 있으면 무음 구간이 없는 것이므로 그대로 반환
    if len(non_silent_audio) <= 1:
        return None

    # 첫 번째 구간과 마지막 구간은 결합하고, 중간 구간은 그대로 둡니다.
    # 첫 번째 구간
    combined_audio = non_silent_audio[0]
    
    # 중간 구간들
    for part in non_silent_audio[1:]:
        # 각 구간 사이에 margin_ms 만큼의 마진을 추가
        # silence_margin = AudioSegment.silent(duration=margin_ms)  # 지정된 마진 시간만큼 무음 생성
        combined_audio += part  # 무음 + 음성 구간을 결합

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

def wav_to_audiosegment(wav, sample_rate):
    """
    numpy ndarray로 된 오디오 데이터를 pydub AudioSegment로 변환
    :param np_array: numpy ndarray 형태의 오디오 데이터
    :param sample_rate: 샘플링 레이트
    :return: pydub.AudioSegment 객체
    """
    # numpy 배열을 int16 형식으로 변환 (WAV 포맷의 기본)
    wav = np.int16(wav / np.max(np.abs(wav)) * 32767)
    
    # numpy 배열을 pydub AudioSegment로 변환
    audio_segment = AudioSegment(
        wav.tobytes(), 
        frame_rate=sample_rate, 
        sample_width=2,  # 16-bit (2 bytes per sample)
        channels=1  # Mono
    )
    return audio_segment

def audiosegment_to_wav(audio_segment):
    """
    pydub AudioSegment를 numpy ndarray로 변환
    :param audio_segment: pydub.AudioSegment 객체
    :return: numpy ndarray 형태의 오디오 데이터
    """
    # AudioSegment에서 샘플 데이터를 numpy 배열로 변환
    samples = np.array(audio_segment.get_array_of_samples())
    
    return samples