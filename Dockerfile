FROM okalex/mel-band-base

COPY . /app
WORKDIR /app

# Clean up
RUN rm -rf .git
RUN rm -rf firebase
RUN rm -rf scripts
RUN rm -rf tmp
RUN rm -rf venv
RUN rm -f build_base
RUN rm -f test_input.json
RUN rm -f .gitignore
RUN rm -f BaseDockerfile
RUN cp ./configs/config_vocals_mel_band_roformer.yaml /tmp/config_vocals_mel_band_roformer.yaml

CMD ["python3", "-u", "rp_inference.py"]
