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
patterns = {
    "ja": r'[ぁ-んァ-ン一-龯]',  # 일본어 (히라가나, 가타카나, 한자)
    "en-us": r'[A-Za-z]',      # 영어 (알파벳)
    "ko": r'[가-힣]'           # 한국어 (한글)
}

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

def ja_checker(text):
    ja_check = False
    for char in text:
        if re.match(patterns["ja"], char):
            ja_check = True
            break
    return ja_check

def split_and_tag_multilingual_text(text):
    # 결과 저장 리스트
    tagged_sentences = []
    tag_list = []

    # 현재 문자 종류 추적
    current_type = None
    buffer = []

    for char in text:
        char_type = current_type  # 기본적으로 현재 유형 유지

        # 현재 문자의 유형을 결정
        for type_, pattern in patterns.items():
            if re.match(pattern, char):
                char_type = type_  # 새로운 언어 유형 발견 시 업데이트
                break

        # 문자의 유형이 바뀌는 경우
        if char_type != current_type:
            if buffer:
                # 이전 유형의 문장을 저장
                tagged_sentences.append(''.join(buffer))
                tag_list.append(current_type)
                buffer = []
            current_type = char_type

        # 현재 유형에 문자를 추가
        buffer.append(char)

    # 남은 문자 처리
    if buffer and current_type:
        tagged_sentences.append(''.join(buffer))
        tag_list.append(current_type)

    return tagged_sentences, tag_list

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


def get_space_position(text):
    return [index for index, char in enumerate(text) if char == ' ']

def seconds_to_time_format(seconds) -> str:
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def _time_str_to_sec(t_str: str) -> float:
    """
    'HH:MM:SS,mmm' 또는 'HH:MM:SS.mmm' 형태의 문자열을 초(float)로 변환
    """
    # 쉼표를 점으로 통일
    t_str = t_str.replace(',', '.')
    # 시, 분, 초.밀리초 분리
    h, m, s = t_str.split(':')
    sec, ms = s.split('.')
    hours = int(h)
    minutes = int(m)
    seconds = int(sec)
    milliseconds = int(ms)
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds/1000
    return total_seconds

def parse_vtt(vtt_file_path:Path):
    """
    VTT 파일을 파싱해서 
    [
        {"start": float, "end": float, "text": str},
        {"start": float, "end": float, "text": str},
        ...
    ]
    형태의 리스트를 반환.
    """
    lines = vtt_file_path.read_text(encoding="utf-8").splitlines()
    
    # VTT 포맷 중 시간 정보 파싱용 정규표현식
    #   00:00:00,000 --> 00:00:01,980
    # 혹은   00:00:00.000 --> 00:00:01.980 (점 사용)
    time_pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2}[\.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[\.,]\d{3})"
    )

    blocks = []
    current_block = {"start": 0.0, "end": 0.0, "text": ""}
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("WEBVTT") or not line:
            # 'WEBVTT' 헤더나 빈 줄은 무시
            i += 1
            continue

        # 자막 번호 (예: "1", "2" 등)은 여기서는 무시 가능
        # 다음 줄에서 시간 정보 탐색
        match = time_pattern.search(line)
        if match:
            # 시간 줄이 맞다면 그 다음 줄(들)에 자막 텍스트가 온다고 가정
            start_str, end_str = match.groups()
            start_time = _time_str_to_sec(start_str)
            end_time = _time_str_to_sec(end_str)

            # 다음 줄(들)에서 자막 내용 추출
            text_lines = []
            i += 1
            # 시간 정보 바로 아래 행부터, 빈 줄이나 다음 시간 정보 전까지 text 수집
            while i < len(lines):
                if not lines[i].strip():
                    break
                # 다음 시간 정보 패턴 만났으면 종료
                if time_pattern.search(lines[i]):
                    # 바로 i를 감소시켜 다음 루프에서 처리
                    i -= 1
                    break
                text_lines.append(lines[i].strip())
                i += 1
            
            text = " ".join(text_lines).strip()
            if text:
                blocks.append({
                    "start": start_time,
                    "end": end_time,
                    "text": text
                })
        i += 1
    
    return blocks


def text_normalization_number(text):
    def remove_commas(s):
        return re.sub(r'(?<=\d),(?=\d)', '', s)
    
    if isinstance(text, str):  # 문자열 처리
        return remove_commas(text)
    elif isinstance(text, list):  # 리스트 처리
        return [remove_commas(t) for t in text]
    else:
        raise ValueError("Input must be a string or a list of strings.")
    
def text_normalization_ko_number_count(text):
    def transform(text):
        # 숫자와 단위를 매칭하는 정규식
        pattern = r'(\d+)(개|명|권|마리|병|집|대|시간|칸)'
        # 숫자 -> 한글 숫자 변환 사전
        number_to_korean = {
            1: "한", 2: "두", 3: "세", 4: "네", 5: "다섯", 6: "여섯", 7: "일곱", 8: "여덟", 9: "아홉", 10: "열"
            # 11: "열하나", 12: "열둘", 13: "열세", 14: "열네", 15: "열다섯", 16: "열여섯", 17: "열일곱", 18: "열여덟", 19: "열아홉", 20: "스무"
        }
        
        def replace_match(match):
            num = int(match.group(1))  # 숫자
            unit = match.group(2)     # 단위
            if 1 <= num <= 10:        # 1부터 10까지만 한글 숫자로 변환
                return f"{number_to_korean[num]}{unit}"
            return f"{num}{unit}"     # 11 이상은 그대로 유지
        
        # 정규식으로 변환 처리
        return re.sub(pattern, replace_match, text)

    if isinstance(text, str):
        return transform(text)
    elif isinstance(text, list):
        return [transform(t) for t in text]
    else:
        raise ValueError("Input must be a string or a list of strings.")
    
def text_normalization_ko_rule_mapping(text):
    def transform(text):
        # 숫자 -> 한글 숫자 변환 사전
        rule_book = {
            # 단위
            r'(\d+)(km)': r'\1 킬로미터', r'(\d+)(m)': r'\1 미터', r'(\d+)(cm)': r'\1 센티미터', r'(\d+)(mm)': r'\1 밀리미터', 
            r'(\d+)(kg)': r'\1 킬로그램', r'(\d+)(g)': r'\1 그램', r'(\d+)(mg)': r'\1 밀리그램', 
            r'(\d+)(L)': r'\1 리터', r'(\d+)(mL)': r'\1 밀리리터',
            r'(\d+)(kHz)': r'\1 킬로헤르츠', r'(\d+)(Hz)': r'\1 헤르츠',
            r'/h': r'퍼아워', r'/m': r'퍼미닛', r'/s': r'퍼세컨드', 
            # 수학기호
            r'(\d+)\+(\d+)': r'\1 더하기 \2', r'(\d+)-(\d+)': r'\1 빼기 \2', r'(\d+)\*(\d+)': r'\1 곱하기 \2', r'(\d+)/(\d+)': r'\1 나누기 \2',
            # 특수기호
            r'&': r'앤드', r'%': r'퍼센트', r'\$': r'달러', r'#': r'샾', r'@': r'골뱅이', r'/': r'슬래시', r':': r'콜론', r';': r'세미콜론',
            r'￥': r'엔', r'元': r'위안',
            # 고유명사
            r'WIFI': r'와이파이',
            r'4$': r'사딸라',
        }
        
        # 숫자=숫자 패턴을 동적으로 처리
        def handle_equals(match):
            first_number = match.group(1)
            second_number = match.group(2)

            # 마지막 숫자의 받침 여부 확인
            last_digit = int(first_number[-1])
            particle = "은" if last_digit in [1, 3, 6, 7, 8, 0] else "는"

            return f"{first_number}{particle} {second_number}"
        
        for pattern, replacement in rule_book.items():
            text = re.sub(pattern, replacement, text)
    
        # 숫자=숫자 패턴 처리 (동적 조사를 위해)
        text = re.sub(r'(\d+)=(\d+)', handle_equals, text)

        return text

    if isinstance(text, str):
        return transform(text)
    elif isinstance(text, list):
        return [transform(t) for t in text]
    else:
        raise ValueError("Input must be a string or a list of strings.")
