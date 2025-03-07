FROM pytorch/pytorch:latest AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  cmake \
  git \
  wget \
  python3-dev \
  && rm -rf /var/lib/apt/lists/*

ENV TORCH_CUDA_ARCH_LIST="Pascal;Volta;Turing;Ampere"
ENV PATH="/opt/conda/bin:${PATH}"

FROM base AS downloader
ADD https://huggingface.co/KimberleyJSN/melbandroformer/resolve/main/MelBandRoformer.ckpt?download=true /tmp/MelBandRoformer.ckpt

FROM downloader AS installer
COPY ./configs/config_vocals_mel_band_roformer.yaml /tmp/config_vocals_mel_band_roformer.yaml
COPY . /app
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

FROM installer AS final
CMD ["python3", "-u", "rp_inference.py"]
