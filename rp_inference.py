import runpod
from inference import run_model

def handler(job):
  config_path = job["input"]["config_path"]
  model_path = job["input"]["model_path"]
  input_folder = job["input"]["input_folder"]
  store_dir = job["input"]["store_dir"]
  num_overlap = job["input"]["num_overlap"]
  run_model("mel_band_roformer", config_path, model_path, input_folder, store_dir, 0, num_overlap)

  return "Inference complete!"

runpod.serverless.start({"handler": handler})
