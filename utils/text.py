import csv

from phonemizer import phonemize
from hangul_romanize import Transliter
from hangul_romanize.rule import academic

ts = Transliter(academic)

def romanize_ko_to_en(ko_text:str):
    return ts.translit(ko_text)

def phonemize_text(text:str, language:str='en-us') -> list:
    '''recommeded language: en-us, ko'''
    return phonemize(text, language=language, backend='espeak', strip=True, preserve_punctuation=True, with_stress=True)


def export_metadata_to_txt(sentences:list, file_path:str, encoding:str='utf-8'):
    with open(file_path, 'w', encoding=encoding) as f:
        for sentence in sentences:
            line = "|".join(sentence)
            f.write(line + '\n')

def export_metadata_to_csv(sentences:list, coulmn_name:list, file_path:str, encoding:str='utf-8'):
    with open(file_path, 'w', newline='', encoding=encoding) as csvfile:
        writer = csv.writer(csvfile)
        if coulmn_name is not None:
            writer = csv.writer(coulmn_name)
        for sentence in sentences:
            writer.writerow(sentence) 
            
def add_metadata_to_txt(sentences:list, file_path:str, encoding:str='utf-8'):
    with open(file_path, 'a', encoding=encoding) as f:
        for sentence in sentences:
            line = "|".join(sentence)
            f.write(line + '\n')

def add_metadata_to_csv(sentences:list, coulmn_name:list, file_path:str, encoding:str='utf-8'):
    with open(file_path, 'a', newline='', encoding=encoding) as csvfile:
        writer = csv.writer(csvfile)
        if coulmn_name is not None:
            writer = csv.writer(coulmn_name)
        for sentence in sentences:
            writer.writerow(sentence) 

def load_speaker_dict(json_file):
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            speaker_dict = json.load(f)
    else:
        speaker_dict = {}
    return speaker_dict

def save_speaker_dict(speaker_dict, json_file):
    with open(json_file, 'w') as f:
        json.dump(speaker_dict, f, indent=4)

def update_speaker_encoding(speaker_list, json_file):
    speaker_dict = load_speaker_dict(json_file)
    current_index = len(speaker_dict)
    
    for speaker in speaker_list:
        if speaker not in speaker_dict:
            speaker_dict[speaker] = current_index
            current_index += 1
    
    save_speaker_dict(speaker_dict, json_file)

    return speaker_dict

def one_hot_encode(speaker_list, json_file):
    speaker_dict = update_speaker_encoding(speaker_list, json_file)
    
    num_speakers = len(speaker_dict)
    encoded_list = []

    for speaker in speaker_list:
        one_hot_vector = [0] * num_speakers
        speaker_index = speaker_dict[speaker]
        one_hot_vector[speaker_index] = 1
        encoded_list.append(one_hot_vector)

    return encoded_list
