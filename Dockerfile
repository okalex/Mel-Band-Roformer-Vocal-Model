FROM pytorch/pytorch:latest

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  cmake \
  git \
  wget \
  vim \
  python3-dev \
  && rm -rf /var/lib/apt/lists/*

# Set up environment variables (optional)
ENV TORCH_CUDA_ARCH_LIST="Pascal;Volta;Turing;Ampere"
ENV PATH="/opt/conda/bin:${PATH}"

# Copy project files (optional)
COPY . /app
ADD https://huggingface.co/KimberleyJSN/melbandroformer/resolve/main/MelBandRoformer.ckpt?download=true /app/MelBandRoformer.ckpt

WORKDIR /app

# Install Python packages (optional)
RUN pip install --no-cache-dir -r requirements.txt

# Command to run on container start
CMD ["python3", "-u", "rp_inference.py"]
