import os, json, csv
import srt

from datetime import timedelta
from phonemizer import phonemize
from phonemizer.backend import EspeakBackend
from phonemizer.separator import Separator
from phonemizer.punctuation import Punctuation

_punctuation = ';:,.!?¡¿—-~"/“” '
english_pattern = re.compile(r'[a-zA-Z]')
kakasi = pykakasi.kakasi()

def phonemize_texts(text:str, language:str='en-us') -> list:
    '''recommeded language: en-us, ko'''
    return phonemize(text, language=language, backend='espeak', strip=True, preserve_punctuation=True, with_stress=True)

def phonemize_text(text:str, language:str='en-us') -> list:
    sentences = text.split('.')  # 문장 분할
    phonemed_sentences = []

    # EspeakBackend 초기화
    backend = EspeakBackend(
        language=language,
        preserve_punctuation=True,
        with_stress=True,
        language_switch='remove-flags'
    )
    separator = Separator(phone=' ', word=' ', syllable='')

    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            phonemed_text = backend.phonemize(
                [sentence],
                separator=separator
            )
            phonemed_sentences.append(phonemed_text[0])  # 리스트에서 문자열 추출

    return phonemed_sentences

def ja_convert_hiragana(text):
    result = kakasi.convert(text)
    return "".join([item['hira'] for item in result]).replace('ー',':')

def ja_convert_katakana(text):
    result = kakasi.convert(text)
    return "".join([item['kana'] for item in result]).replace('ー',':')

def generate_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def generate_unique_name(length:int=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
def seconds_to_time_format(seconds):
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

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

def load_srt(file_path:str, encoding:str='utf-8'):
    '''
    output example:   
        for subtitle in subtitles:
            print("Index:", subtitle.index)
            print("Start:", subtitle.start)
            print("End:", subtitle.end)
            print("Content:", subtitle.content)
    '''

    with open(file_path, 'r', encoding=encoding) as f:
        srt_content = f.read()
    subtitles = list(srt.parse(srt_content))
    return subtitles

def get_space_position(text):
    return [index for index, char in enumerate(text) if char == ' ']
