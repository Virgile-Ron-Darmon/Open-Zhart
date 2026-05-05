sudo apt update
sudo apt install -y \
  build-essential cmake git \
  libvulkan-dev vulkan-tools \
  glslc libshaderc-dev \
  mesa-vulkan-drivers  # for AMD/Intel iGPUs


cd /opt
sudo git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

sudo cmake -B build -DGGML_VULKAN=ON
sudo cmake --build build --config Release -j$(nproc)

pip3 install huggingface_hub

hf download bartowski/google_gemma-4-E2B-it-GGUF \
  --include "google_gemma-4-E2B-it-Q4_K_M.gguf" \
  --local-dir ./models