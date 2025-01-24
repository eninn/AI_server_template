import multiprocessing as mp

from tqdm import tqdm

def small_data_parallel_processing(num_processes:int, func:callable, data_list:list) -> list:
    chunk_size = len(data_list) // num_processes
    chunks = [data_list[i * chunk_size: (i + 1) * chunk_size] for i in range(num_processes)]
    
    if len(data_list) % num_processes != 0:
        chunks[-1].extend(data_list[num_processes * chunk_size:])

    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.map(func, chunks)
    
    flattened_results = [item for sublist in results for item in sublist]
    return flattened_results

def large_data_parallel_processing(num_processes: int, func: callable, data_list: list) -> list:
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = list(tqdm(pool.imap(func, data_list), total=len(data_list), desc="Processing data"))
    
    return results

        
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