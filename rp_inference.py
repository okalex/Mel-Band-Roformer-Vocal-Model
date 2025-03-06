import runpod
import json
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
from inference import run_model

def handler(job):
  config_path = "/tmp/config_vocals_mel_band_roformer.yaml"
  model_path = "/tmp/MelBandRoformer.ckpt"
  input_folder = "/tmp/in"
  store_dir = "/tmp/out"
  file_name = job["input"]["file_name"]
  num_overlap = job["input"]["num_overlap"]

  firebase_key = os.environ.get('FIREBASE_SECRET')
  print('firebase_key')
  print(firebase_key)
  firebase_key_file = '/tmp/firebase-key.json'
  print('firebase_key_file')
  print(firebase_key_file)
  with open(firebase_key_file, 'w', encoding="utf-8") as output_file:
    output_file.write(firebase_key)
  
  cred = credentials.Certificate(firebase_key_file)
  firebase_admin.initialize_app(cred, {
      'storageBucket': 'stemulator-4606f.firebasestorage.app'
  })

  bucket = storage.bucket()
  blob = bucket.blob(file_name)
  blob.download_to_filename('/tmp/in/orig.wav')

  run_model("mel_band_roformer", config_path, model_path, input_folder, store_dir, 0, num_overlap)

  bucket.blob('orig_vocals.wav').upload_from_filename('/tmp/out/orig_vocals.wav')
  bucket.blob('orig_instrumental.wav').upload_from_filename('/tmp/out/orig_instrumental.wav')

  return json.dumps({"vocals": "orig_vocals.wav", "instrumental": "orig_instrumental.wav"})

runpod.serverless.start({"handler": handler})
