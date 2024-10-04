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