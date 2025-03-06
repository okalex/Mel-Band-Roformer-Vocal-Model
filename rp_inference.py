import runpod
import base64
from inference import run_model
import json

def handler(job):
  config_path = "/app/configs/config_vocals_mel_band_roformer.yaml"
  model_path = "/app/MelBandRoformer.ckpt"
  input_folder = "/app/in"
  store_dir = "/app/out"
  audiob64 = job["input"]["audio"]
  num_overlap = job["input"]["num_overlap"]

  decoded = base64.b64decode(audiob64)
  with open('app/in/orig.wav', 'w', encoding="utf-8") as output_file:
    output_file.write(decoded.decode("utf-8"))

  run_model("mel_band_roformer", config_path, model_path, input_folder, store_dir, 0, num_overlap)

  with open('/app/out/orig_vocals.wav', 'r') as input_file:
    coded_string = input_file.read()
    vocals_b64 = base64.b64encode(coded_string)
  
  with open('/app/out/orig_instrumental.wav', 'r') as input_file:
    coded_string = input_file.read()
    instrumental_b64 = base64.b64encode(coded_string)

  return json.dumps({"vocals": vocals_b64, "instrumental": instrumental_b64})

runpod.serverless.start({"handler": handler})
