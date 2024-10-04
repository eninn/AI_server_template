from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings

class AbsolutePath(BaseModel):
    checkpoint_path: Path = Path("./resources/checkpoints")
    input_path: Path = Path("./resources/input")
    output_path: Path = Path("./resources/output")

ap = AbsolutePath()

class HyperParams(BaseModel):
    server_host: str = "0.0.0.0"
    server_port: int = 5292
    device: str = "cuda"

hp = HyperParams()

class EnvSetting(BaseSettings):
    env_state: str
    env_index: int
    debug: bool = False

    class Config:
        env_file = "envs/.env"
        env_file_encoding = "utf-8"

env = EnvSetting()

class LabelInfo(BaseModel):
    style_dict:dict = {'S1': 'Oral', 'S2': 'Mono', 'Read': 'News', 'S4': 'Conv', 'S5': 'Relay'}
    emotion_dict:dict = {'E1': 'Happy', 'E2': 'Sad', 'E3': 'Angry', 'E4': 'Anxious', 'E5': 'Hurt', 'E6': 'Embarrassed', 'E7': 'Neutrality'}

li = LabelInfo()