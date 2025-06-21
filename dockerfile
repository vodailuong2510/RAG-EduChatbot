FROM python:3.10-slim

# ngrok http --url=suitable-violently-polliwog.ngrok-free.app 8000
# Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force

RUN pip-autoremove torch torchvision torchaudio -y
Run pip install torch torchvision torchaudio xformers --index-url https://download.pytorch.org/whl/cu121