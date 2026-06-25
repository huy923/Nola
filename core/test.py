import os
from huggingface_hub import snapshot_download


os.system("python -m unidic download")
print(" > Tải mô hình...")
snapshot_download(repo_id="thinhlpg/viXTTS",
                  repo_type="model",
                  local_dir="model",
                  local_files_only=True)
