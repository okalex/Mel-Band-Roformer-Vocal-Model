import runpod
import json
import os
from pathlib import Path
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
from inference import run_model

# Test build

def handler(job):
  config_path = "/tmp/config_vocals_mel_band_roformer.yaml"
  model_path = "/tmp/MelBandRoformer.ckpt"
  input_folder = "/tmp/in"
  store_dir = "/tmp/out"
  file_name = job["input"]["file_name"]
  bucket_url = job["input"]["bucket_name"]
  num_overlap = job["input"]["num_overlap"]

  os.mkdir(input_folder)
  os.mkdir(store_dir)

  firebase_key = os.environ.get('FIREBASE_SECRET')
  firebase_key_file = '/tmp/firebase-key.json'
  with open(firebase_key_file, 'w', encoding="utf-8") as output_file:
    output_file.write(firebase_key)
  
  cred = credentials.Certificate(firebase_key_file)
  firebase_admin.initialize_app(cred, {
      'storageBucket': bucket_url
  })

  bucket = storage.bucket()
  blob = bucket.blob(file_name)
  blob.download_to_filename('/tmp/in/orig.wav')

  for message in run_model("mel_band_roformer", config_path, model_path, input_folder, store_dir, 0, num_overlap):
    yield message

  file_without_extension = Path(file_name).stem
  vocal_file = file_without_extension + '_vocals.wav'
  instrumental_file = file_without_extension + '_instrumental.wav'
  bucket.blob(vocal_file).upload_from_filename('/tmp/out/orig_vocals.wav')
  bucket.blob(instrumental_file).upload_from_filename('/tmp/out/orig_instrumental.wav')

  yield json.dumps({"vocals": vocal_file, "instrumental": instrumental_file})

runpod.serverless.start({
  "handler": handler,
  "return_aggregate_stream": True,
})
