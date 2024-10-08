import os, json

import numpy as np

from pathlib import Path
from tqdm import tqdm
from abc import *

from utils.text import phonemize_text, one_hot_encode, update_speaker_encoding
from utils.environment import hp

class DataPreProcessor(metaclass=ABCMeta):
    def __init__(self, 
                 root_path:str, 
                 refine_path:str=None,
                 columns:list=['audio_file', 'transcript_text', 'speaker_id', 'emotion_id']) -> None:
        self.dataset_root_dirpath = Path(root_path)
        if refine_path:
            self.dataset_refine_path = Path(refine_path)
        else:
            self.dataset_refine_path = None

        self.columns = columns

    @abstractmethod
    def get_value_from_json(self, json_path:str, select_language:str) -> list:
        '''Initialize spesific dataset case'''
        with open(json_path, 'r', encoding='utf-8-sig') as f:
            item = json.load(f)
            value_list = [
                itme['wavfile'],
                item['transcript_text'],
                item['speaker_id'],
                item['emotion']
            ]
        return value_list
    
    def make_metadata_list(self, sub_dir_name:str, language:str='ko'):
        sub_dir_labels_path = self.dataset_root_dirpath / sub_dir_name / 'labels'
        metadata_list_path = self.dataset_root_dirpath / f"metadata_{sub_dir_name}_{language}.txt"
        if not sub_dir_labels_path.is_dir():
            raise Exception(f"Sub directory:{sub_dir_labels_path} is not exist.")
        
        json_files = sorted([_ for _ in os.listdir(str(sub_dir_labels_path))])

        with open(metadata_list_path, 'w', encoding='utf-8') as f:
            for json_file in tqdm(json_files, desc=f"{sub_dir_name}|{language}:"):    
                try:    
                    json_path = sub_dir_labels_path / json_file    
                    row = self.get_value_from_json(str(json_path), language)
                    wav_file = self.dataset_root_dirpath / sub_dir_name / 'wavs' / row[0]
                    if not row or not wav_file.is_file():
                        continue
                    
                    line = "|".join(row)
                    f.write(line + '\n')
                except Exception as e:
                    print(f"Error file: {json_file}")
                    print(f"Error text: {e}")
            
    def make_phonemized_list(self, sub_dir_name:str, language:str='ko'):
        metadata_list_path = self.dataset_root_dirpath / f"metadata_{sub_dir_name}_{language}.txt"
        phonemized_list_path = self.dataset_root_dirpath / f"metadata_{sub_dir_name}_phonemize.txt"
        if not metadata_list_path.is_file():
            raise Exception(f"Sub directory:{metadata_list_path} is not exist.")

        with open(metadata_list_path, 'r', encoding='utf-8') as f:
            data = f.readlines()

        get_texts = []
        for line in tqdm(data):
            row = line.split('|')
            get_texts.append(row[1])

        phonemed_text = phonemize_text(get_texts, language='ko')

        modified_data = []
        for idx, line in tqdm(enumerate(data)):
            row = line.split('|')
            row[1] = phonemed_text[idx]
            modified_data.append('|'.join(row))

        with open(phonemized_list_path, 'w', encoding='utf-8') as f:
            f.writelines(modified_data)

    def make_out_of_data_list(self, sub_dir_name:str, ratio:float, language:str='ko'):
        sub_dir_labels_path = self.dataset_root_dirpath / sub_dir_name / 'labels'
        sub_dir_wavs_path = self.dataset_root_dirpath / sub_dir_name / 'wavs'
        metadata_list_path = self.dataset_root_dirpath / f"metadata_{sub_dir_name}_{language}.txt"
        if not sub_dir_labels_path.is_dir():
            raise Exception(f"Sub directory:{sub_dir_labels_path} is not exist.")
        
        json_files = sorted([_ for _ in os.listdir(str(sub_dir_labels_path))])

        total_files = len(json_files)
        num_to_move = int(total_files * ratio)

        np.random.seed(hp.np_random_seed)
        selected_indices = np.random.choice(total_files, size=num_to_move, replace=False)        


        with open(metadata_list_path, 'w', encoding='utf-8') as f:
            for idx in tqdm(selected_indices, desc=f"{sub_dir_name}|{language}:"):    
                try:    
                    
                    json_path = sub_dir_labels_path / json_files[idx]
                    row = self.get_value_from_json(str(json_path), language)
                    if not row:
                        continue
                    row[0] = str(sub_dir_wavs_path / row[0])
                    line = "|".join(row)
                    f.write(line + '\n')
                except Exception as e:
                    print(f"Error file: {json_files[idx]}")
                    print(f"Error text: {e}")

    def get_speaker_id_encode(self, json_file:str, sub_dir_name:str, language:str='ko'):
        metadata_list_path = self.dataset_root_dirpath / f"metadata_{sub_dir_name}_{language}.txt"
        if not metadata_list_path.is_file():
            raise Exception(f"Sub directory:{metadata_list_path} is not exist.")

        with open(metadata_list_path, 'r', encoding='utf-8') as f:
            data = f.readlines()

        get_speaker_ids = []
        for line in tqdm(data):
            row = line.split('|')
            try:
                get_speaker_ids.append(row[2])
            except Exception as e:
                print(row)

        encoded_speakers = update_speaker_encoding(get_speaker_ids, json_file)

