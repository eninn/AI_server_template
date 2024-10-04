import os, shutil, json
import numpy as np

from pathlib import Path
from rich.progress import track

from utils.audio import resample_and_save_wav
from utils.text import phonemize_text, export_metadata_to_csv, export_metadata_to_txt

class DataPreProcessor:
    def __init__(self, 
                 root_path:str, 
                 refine_path:str='',
                 columns:list=['audio_file', 'transcript_text', 'speaker_id', 'emotion_id', 'root_path']) -> None:
        self.dataset_root_dirpath = Path(root_path)
        if not refine_path:
            refine_path = self.dataset_root_dirpath.parent / f"{self.dataset_root_dirpath.name}_refine"
        self.dataset_refine_path = Path(refine_path)

        self.columns = columns

    def get_value_from_json(self, json_path:str) -> dict:
        with open(json_path, 'r') as f:
            item = json.load(f)

        # get value method from json
        value_dict = {
            self.columns[0]: item['key'],
            self.columns[1]: item['key'],
            self.columns[2]: item['key']
        }

        if len(value_dict.keys()) == len(self.columns):
            return value_dict
        else:
            return None

    def make_metadata_list(self, sub_dir_name:str):
        self.metadata = []
        sub_dir_path = self.dataset_root_dirpath/sub_dir_name
        if not sub_dir_path.is_dir():
            raise Exception(f"Sub directory:{sub_dir_path} is not exist.")
        
        for json_path in sorted(sub_dir_path.rglob('*json')):
            value_dict = self.get_value_from_json(json_path)
            row = [value_dict[self.columns[0]], value_dict[self.columns[1]], value_dict[self.columns[2]]]
            self.metadata.append(row)

    def export_matadata_txt(self, output_path:str):
        if self.metadata:
            export_metadata_to_txt(self.metadata, output_path)
        else:
            print("Make metadata list first.")

    def export_metadata_csv(self, output_path:str):
        if self.metadata:
            export_metadata_to_csv(self.metadata, output_path)
        else:
            print("Make metadata list first.")
