from faster_whisper import WhisperModel

from utils.text import seconds_to_time_format

class FasterWhisper:
    def __init__(self, model_size:str="large-v3", device:str="cuda", compute_type:str="float16") -> None:
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe_to_vtt(self, file_path:str, language:str, beam_size:int=5):
        segments, info = self.model.transcribe(file_path, language=language, beam_size=beam_size)
        srt_script = "WEBVTT\n\n"
        
        for i, segment in enumerate(segments):
            srt_script = srt_script + f"{i+1}\n"
            srt_script = srt_script + f"{seconds_to_time_format(segment.start)} --> {seconds_to_time_format(segment.end)}\n"
            srt_script = srt_script + f"{segment.text}\n\n"

        return srt_script