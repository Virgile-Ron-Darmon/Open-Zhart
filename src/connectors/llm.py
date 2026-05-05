import subprocess
import requests
import time
import os
import sys
import signal

LLAMA_SERVER = "/opt/llama.cpp/build/bin/llama-server"
VULKAN_PATH  = "/opt/vulkan"

class LLM:
    def __init__(
        self,
        model_path="./models/google_gemma-4-E2B-it-Q4_K_M.gguf",
        server_path=LLAMA_SERVER,
        mode="gpu",
        port=8080,
        gpu_layers=99,
        hybrid_layers=40,
        vulkan_path=VULKAN_PATH,
        timeout=60,
    ):
        self.model_path  = model_path
        self.server_path = server_path
        self.mode        = mode
        self.port        = port
        self.gpu_layers  = gpu_layers
        self.hybrid_layers = hybrid_layers
        self.vulkan_path = vulkan_path
        self.timeout     = timeout
        self.base_url    = f"http://localhost:{port}"
        self._process    = None

    # ------------------------------------------------------------------ #
    #  Context manager support:  with LLM() as llm:                       #
    # ------------------------------------------------------------------ #
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()

    # ------------------------------------------------------------------ #
    #  Server lifecycle                                                    #
    # ------------------------------------------------------------------ #
    def start(self):
        if self._process is not None:
            print("⚠️  Server already running.")
            return

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        if not os.path.exists(self.server_path):
            raise FileNotFoundError(f"llama-server not found: {self.server_path}")

        cmd = [
            self.server_path,
            "-m", self.model_path,
            "--chat-template", "gemma",
            "--port", str(self.port),
        ]

        if self.mode == "gpu":
            cmd += ["-ngl", str(self.gpu_layers)]
        elif self.mode == "hybrid":
            cmd += ["-ngl", str(self.hybrid_layers)]
        elif self.mode != "cpu":
            raise ValueError(f"Unknown mode '{self.mode}'. Use: gpu | cpu | hybrid")

        env = self._build_env()

        print(f"🚀 Starting llama-server [{self.mode.upper()}] on port {self.port}...")
        self._process = subprocess.Popen(
            cmd,
            env=env,
            stdout=None,   # <-- print to terminal so we can see what's happening
            stderr=None,   # <-- same
        )

        self._wait_until_ready()
    def stop(self):
        if self._process is None:
            return
        print("🛑 Stopping llama-server...")
        self._process.send_signal(signal.SIGTERM)
        try:
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
        self._process = None

    def restart(self):
        self.stop()
        self.start()

    @property
    def is_running(self):
        return self._process is not None and self._process.poll() is None

    # ------------------------------------------------------------------ #
    #  Inference                                                           #
    # ------------------------------------------------------------------ #
    def chat(self, prompt, system=None, max_tokens=512, temperature=0.7):
        if not self.is_running:
            raise RuntimeError("Server is not running. Call .start() first.")

        # Gemma does not support the system role — prepend it to the user message
        if system:
            user_content = f"{system}\n\n{prompt}"
        else:
            user_content = prompt

        messages = [{"role": "user", "content": user_content}]

        return self._complete(messages, max_tokens, temperature)

    def conversation(self, messages, max_tokens=512, temperature=0.7):
        """
        Multi-turn chat. Pass the full message history as a list:
            [
                {"role": "user",      "content": "Hello"},
                {"role": "assistant", "content": "Hi!"},
                {"role": "user",      "content": "Tell me a joke"},
            ]
        Returns the assistant reply as a string.
        """
        if not self.is_running:
            raise RuntimeError("Server is not running. Call .start() first.")

        return self._complete(messages, max_tokens, temperature)

    # ------------------------------------------------------------------ #
    #  Internals                                                           #
    # ------------------------------------------------------------------ #
    def _complete(self, messages, max_tokens, temperature):
        # Build prompt manually instead of relying on llama.cpp's chat template
        prompt = ""
        for msg in messages:
            if msg["role"] == "user":
                prompt += f"<start_of_turn>user\n{msg['content']}<end_of_turn>\n"
            elif msg["role"] == "assistant":
                prompt += f"<start_of_turn>model\n{msg['content']}<end_of_turn>\n"
        prompt += "<start_of_turn>model\n"  # open the assistant turn

        payload = {
            "prompt":      prompt,
            "n_predict":   max_tokens,
            "temperature": temperature,
            "stop":        ["<end_of_turn>", "<start_of_turn>"],
        }

        print(f"DEBUG prompt length: {len(prompt)} chars")

        resp = requests.post(
            f"{self.base_url}/completion",   # <-- raw endpoint, not /v1/chat/completions
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["content"].strip()

    def _wait_until_ready(self):
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            try:
                r = requests.get(f"{self.base_url}/health", timeout=2)
                if r.status_code == 200:
                    print("✅ Server ready.")
                    return
            except requests.ConnectionError:
                pass
            time.sleep(1)
        self.stop()
        raise TimeoutError("llama-server did not become ready in time.")

    def _build_env(self):
        env = os.environ.copy()
        if self.mode == "cpu":
            return env

        vulkan_lib = os.path.join(self.vulkan_path, "lib")
        vulkan_bin = os.path.join(self.vulkan_path, "bin")

        existing_ld   = env.get("LD_LIBRARY_PATH", "")
        existing_path = env.get("PATH", "")

        env["LD_LIBRARY_PATH"] = f"{vulkan_lib}:{existing_ld}" if existing_ld else vulkan_lib
        env["PATH"]            = f"{vulkan_bin}:{existing_path}" if existing_path else vulkan_bin
        env.setdefault("VK_ICD_FILENAMES", os.path.join(self.vulkan_path, "etc/vulkan/icd.d"))

        return env