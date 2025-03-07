import argparse
import yaml
import numpy as np
import time
from ml_collections import ConfigDict
from omegaconf import OmegaConf
from tqdm import tqdm
import sys
import os
import glob
import torch
import soundfile as sf
import torch.nn as nn
import runpod
from utils import demix_track, get_model_from_config

import warnings
warnings.filterwarnings("ignore")

def output(message):
    print(message)
    sys.stdout.flush()
    yield message

def run_folder(model, model_type, config_path, model_path, input_folder, store_dir, device_ids, num_overlap, config, device, verbose=False):
    start_time = time.time()
    model.eval()
    all_mixtures_path = glob.glob(input_folder + '/*.wav')
    total_tracks = len(all_mixtures_path)
    output('Total tracks found: {}'.format(total_tracks))

    instruments = config.training.instruments
    if config.training.target_instrument is not None:
        instruments = [config.training.target_instrument]

    if not os.path.isdir(store_dir):
        os.mkdir(store_dir)

    if not verbose:
        all_mixtures_path = tqdm(all_mixtures_path)

    first_chunk_time = None
    
    if num_overlap is None:
        num_overlap = config.inference.num_overlap

    for track_number, path in enumerate(all_mixtures_path, 1):
        output(f"\nProcessing track {track_number}/{total_tracks}: {os.path.basename(path)}")

        mix, sr = sf.read(path)
        original_mono = False
        if len(mix.shape) == 1:
            original_mono = True
            mix = np.stack([mix, mix], axis=-1)

        mixture = torch.tensor(mix.T, dtype=torch.float32)

        if first_chunk_time is not None:
            total_length = mixture.shape[1]

            num_chunks = (total_length + config.inference.chunk_size // num_overlap - 1) // (config.inference.chunk_size // num_overlap)
            estimated_total_time = first_chunk_time * num_chunks
            output(f"Estimated total processing time for this track: {estimated_total_time:.2f} seconds")
            output(f"Estimated time remaining: {estimated_total_time:.2f} seconds\r")

        res, first_chunk_time = demix_track(config, model, mixture, device, num_overlap, first_chunk_time)

        for instr in instruments:
            vocals_output = res[instr].T
            if original_mono:
                vocals_output = vocals_output[:, 0]

            vocals_path = "{}/{}_{}.wav".format(store_dir, os.path.basename(path)[:-4], instr)
            sf.write(vocals_path, vocals_output, sr, subtype='FLOAT')

        vocals_output = res[instruments[0]].T
        if original_mono:
            vocals_output = vocals_output[:, 0]

        original_mix, _ = sf.read(path)
        instrumental = original_mix - vocals_output

        instrumental_path = "{}/{}_instrumental.wav".format(store_dir, os.path.basename(path)[:-4])
        sf.write(instrumental_path, instrumental, sr, subtype='FLOAT')

    time.sleep(1)
    output("Elapsed time: {:.2f} sec".format(time.time() - start_time))


def run_model(model_type, config_path, model_path, input_folder, store_dir, device_ids, num_overlap):
    torch.backends.cudnn.benchmark = True

    with open(config_path) as f:
      config = ConfigDict(yaml.load(f, Loader=yaml.FullLoader))

    model = get_model_from_config(model_type, config)
    if model_path != '':
        print('Using model: {}'.format(model_path))
        model.load_state_dict(
            torch.load(model_path, map_location=torch.device('cpu'))
        )

    if torch.cuda.is_available():
        output('Using CUDA')
        if type(device_ids)==int:
            device = torch.device(f'cuda:{device_ids}')
            model = model.to(device)
        else:
            device = torch.device(f'cuda:{device_ids[0]}')
            model = nn.DataParallel(model, device_ids=device_ids).to(device)
    elif torch.mps.is_available():
        output('Using MPS')
        device = 'mps'
        model = nn.DataParallel(model).to(device)
    else:
        device = 'cpu'
        output('CUDA is not available. Run inference on CPU. It will be very slow...')
        model = model.to(device)

    yield from run_folder(model, model_type, config_path, model_path, input_folder, store_dir, device_ids, num_overlap, config, device, verbose=False)


def proc_folder(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_type", type=str, default='mel_band_roformer')
    parser.add_argument("--config_path", type=str, help="path to config yaml file")
    parser.add_argument("--model_path", type=str, default='', help="Location of the model")
    parser.add_argument("--input_folder", type=str, help="folder with songs to process")
    parser.add_argument("--store_dir", default="", type=str, help="path to store model outputs")
    parser.add_argument("--device_ids", nargs='+', type=int, default=0, help='list of gpu ids')
    parser.add_argument("--num_overlap", type=int, default=None, help='Number of overlapping chunks')
    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)
    run_model(args.model_type, args.config_path, args.model_path, args.input_folder, args.store_dir, args.device_ids, args.num_overlap)


if __name__ == "__main__":
    proc_folder(None)
