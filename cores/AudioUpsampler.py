import torch, torchaudio, yaml

import numpy as np

from audiosr.pipeline import default_audioldm_config, super_resolution, seed_everything
from audiosr.utils import wav_feature_extraction, lowpass_filtering_prepare_inference, normalize_wav, pad_wav
from audiosr.latent_diffusion.models.ddpm import LatentDiffusion

from utils.environment import ap, hp

seed_everything(42)

class AudioSR:
    def __init__(self, 
                 ckpt_path=str(ap.inner_checkpoint_path/'upsampler'/'audiosr'/f'pytorch_model_{hp.audiosr_model_name}.bin'),
                 config=None, 
                 device=hp.device, 
                 model_name="speech"):

        self.audiosr = self.build_upsampler_model(ckpt_path=ckpt_path, 
                                            config=config,
                                            device=device,
                                            model_name=model_name)

    def build_upsampler_model(self, ckpt_path=None, config=None, device=None, model_name="basic", use_fp16=False):
        if device is None or device == "auto":
            if torch.cuda.is_available():
                device = torch.device("cuda:0")
            elif torch.backends.mps.is_available():
                device = torch.device("mps")
            else:
                device = torch.device("cpu")

        print("Loading AudioSR: %s" % model_name)
        print("Loading model on %s" % device)
        
        # if not ckpt_path:
        #     ckpt_path = download_checkpoint(model_name)

        if config is not None:
            assert type(config) is str
            config = yaml.load(open(config, "r"), Loader=yaml.FullLoader)
        else:
            config = default_audioldm_config(model_name)

        # # Use text as condition instead of using waveform during training
        config["model"]["params"]["device"] = device

        # No normalization here
        latent_diffusion = LatentDiffusion(**config["model"]["params"])

        checkpoint = torch.load(ckpt_path, map_location=device)

        latent_diffusion.load_state_dict(checkpoint["state_dict"], strict=False)

        latent_diffusion.eval()
        latent_diffusion = latent_diffusion.to(device)

        return latent_diffusion


    def read_wav_from_array(self, wav:np.ndarray, sample_rate:int=24000):
        waveform = wav[None, ...]  # shape: (1, samples)
        # Resample to 48kHz if necessary
        if sample_rate != hp.output_upsample_rate:
            waveform = torch.FloatTensor(waveform)  # Convert to Tensor
            waveform = torchaudio.functional.resample(waveform, orig_freq=sample_rate, new_freq=hp.output_upsample_rate)
            waveform = waveform.numpy()  # Convert back to numpy for compatibility

        # Normalize waveform
        waveform = normalize_wav(waveform[0])

        # Calculate duration and pad waveform to a multiple of 5.12 seconds
        duration = waveform.shape[-1] / hp.output_upsample_rate  # Assuming 48kHz
        if duration > 10.24:
            print("\033[93m {}\033[00m".format("Warning: audio is longer than 10.24 seconds, which may degrade model performance."))
        if duration % 5.12 != 0:
            pad_duration = duration + (5.12 - duration % 5.12)
        else:
            pad_duration = duration

        # Pad waveform
        waveform = pad_wav(waveform[None, ...], target_length=int(hp.output_upsample_rate * pad_duration))
        target_frame = int(pad_duration * 100)

        return waveform, duration, pad_duration, target_frame
    
    def upsample_wavfile(self, input_wav_path:str, ddim_steps:int=50):
        latent_t_per_second=12.8
        guidance_scale=3.5        
        upsample_wavform = super_resolution(self.audiosr,
                                            input_file=input_wav_path,
                                            seed=42,
                                            ddim_steps=ddim_steps,
                                            guidance_scale=guidance_scale,
                                            latent_t_per_second=latent_t_per_second)
        return upsample_wavform.squeeze()
    
    def upsample_wav(self, wav:np.ndarray, sr:int, ddim_steps:int=50):
        waveform, duration, pad_duration, target_frame = self.read_wav_from_array(wav, sr)

        # Generate spectrograms and other features
        log_mel_spec, stft = wav_feature_extraction(waveform, target_frame)

        batch = {
            "waveform": torch.FloatTensor(waveform),
            "stft": torch.FloatTensor(stft),
            "log_mel_spec": torch.FloatTensor(log_mel_spec),
            "sampling_rate": hp.output_upsample_rate,
        }
        batch.update(lowpass_filtering_prepare_inference(batch))
        assert "waveform_lowpass" in batch.keys()

        lowpass_mel, lowpass_stft = wav_feature_extraction(batch["waveform_lowpass"], target_frame)
        batch["lowpass_mel"] = lowpass_mel
        
        for k in batch.keys():
            if isinstance(batch[k], torch.Tensor):
                batch[k] = batch[k].unsqueeze(0)  # Add batch dimension

        with torch.no_grad():
            upsample_wavform = self.audiosr.generate_batch(batch,
                                                        unconditional_guidance_scale=hp.guidance_scale,
                                                        ddim_steps=ddim_steps,
                                                        duration=pad_duration)
            

        upsample_wavform = upsample_wavform.squeeze()
        original_length = int(duration * hp.output_upsample_rate)
        new_y = upsample_wavform[:original_length]        
        new_sr = hp.output_upsample_rate

        return new_y, new_sr