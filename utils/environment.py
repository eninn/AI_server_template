import os, json

from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from utils.logger import loggerConfig

class EnvSetting(BaseSettings):
    ENV_STATE: str = 'loc'
    ENV_INDEX: int = 0
    GPU_DEVICE_INDEX: int = 0

    TTS_SERVER_HOST: str = '0.0.0.0'
    TTS_SERVER_PORT: int = 8080

    INNER_RESOURCES_PATH: str = './resources'
    OUTER_RESOURCES_PATH: str = './resources'

    if os.getenv("RUNENV"):
        model_config = SettingsConfigDict(env_file=os.path.join('envs', f'.env.{os.getenv("RUNENV")}'))

envs = EnvSetting()

class AbsolutePath(BaseModel):
    inner_checkpoint_path: Path
    outer_checkpoint_path: Path
    inner_input_path: Path
    outer_input_path: Path
    inner_output_path: Path
    outer_output_path: Path
    inner_log_path: Path

    @classmethod
    def with_base_path(cls, inner_base_path:str, outer_base_path:str):
        inner_base_path = Path(inner_base_path)
        outer_base_path = Path(outer_base_path)
        return cls(
            inner_checkpoint_path=inner_base_path / "models",
            outer_checkpoint_path=outer_base_path / "models",
            inner_input_path=inner_base_path / "inputs",
            outer_input_path=outer_base_path / "inputs",
            inner_output_path=inner_base_path / "outputs",
            outer_output_path=outer_base_path / "outputs",
            inner_log_path=inner_base_path / "logs",
        )
    
if envs:
    ap = AbsolutePath.with_base_path(inner_base_path=envs.INNER_RESOURCES_PATH, outer_base_path=envs.OUTER_RESOURCES_PATH)
else:
    ap = AbsolutePath.with_base_path(inner_base_path='./resources', outer_base_path='./resources')

class HyperParams(BaseModel):
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    device: str = "cuda"
    bot_token: str = "telegram-bot-token"
    chat_id: str = "telegram-chat-id"  # 메시지를 보낼 대상의 채팅 ID
    
    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types

if envs:
    hp = HyperParams(server_host=envs.TTS_SERVER_HOST,
                     server_port=envs.TTS_SERVER_PORT)
else:
    hp = HyperParams()

class LabelInfo(BaseModel):
    language_code:dict = {"en": "en-us", "ko": "ko", "es": "es", "jp": "ja", "ch": "cmn"}
    a133_style_dict:dict = {'독백체': 'Mono', '대화체': 'Conv', '구연체': 'Oral', '중계체': 'Relay', '친절체': 'Kind', '애니체': 'Anime', '낭독체': 'Read'} # Oral: 구연체
    a133_emotion_dict:dict = {'기쁨': 'Happy', '분노': 'Angry', '슬픔': 'Sad', '무감정': 'Neutrality'}
    default_style_dict:dict = {'default': 'Read'}
    default_emotion_dict:dict = {'default': 'Neutrality'}
    a015_style_tag_dict:dict = {'S0': 'Relay', 'S1': 'Oral', 'S2': 'Mono', 'S3': 'Read', 'S4': 'Conv', 'S5': 'Relay'} # S3 뉴스체 -> 낭독체
    a015_style_dict:dict = {'N/A': 'Oral', '구연체': 'Oral', '낭독체': 'Mono', '뉴스체': 'Read', '대화체': 'Conv', '중계체': 'Relay'} # S3 뉴스체 -> 낭독체
    a015_emotion_dict:dict = {'E1': 'Happy', 'E2': 'Sad', 'E3': 'Angry', 'E4': 'Anxious', 'E5': 'Hurt', 'E6': 'Embarrassed', 'E7': 'Neutrality'}
    a015_foldering_rule:dict = {'1.감정': 'E1~7', '2.스타일': 'S1~5', '3.캐릭터': 'C0~9', '4.감정x스타일': 'E1~6S1,4'}
    stts_model_config_dict:dict = {
        "epoch_2nd_00001_tmp.pth": {
            "language": "ko",
            "config": "epoch_2nd_00001_tmp.yml",
            "cleaner": "old"
        }
    }

avaliable_model_list_file_path = ap.inner_checkpoint_path / 'available_model_list.json'
with open(str(avaliable_model_list_file_path), 'r') as f:
    model_configs = json.load(f)
li = LabelInfo(stts_model_config_dict=model_configs)

service_logger = loggerConfig(logger_name=f'stts_inference_{envs.ENV_STATE}_{envs.ENV_INDEX}',
                              log_dir=ap.inner_log_path,
                              log_type='file')