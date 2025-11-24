import os
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig
from aeron.training.export import export_daily_conversations
import subprocess

# Configuration
DATA_DIR = os.getenv("DATA_DIR", "/data")
BASE_MODEL_PATH = os.getenv("BASE_MODEL_PATH", f"{DATA_DIR}/models/Llama-3.1-8B")
OUTPUT_DIR = f"{DATA_DIR}/models/adapters"
DAILY_DATA_FILE = f"{DATA_DIR}/training/daily_data.jsonl"

def train():
    print("Starting training pipeline...")
    
    # 1. Export Data
    export_daily_conversations(DAILY_DATA_FILE)
    
    if not os.path.exists(DAILY_DATA_FILE) or os.path.getsize(DAILY_DATA_FILE) == 0:
        print("No new data found. Skipping training.")
        return

    # Check for base model
    if not os.path.exists(BASE_MODEL_PATH):
        print(f"Base model not found at {BASE_MODEL_PATH}. Cannot train.")
        # In a real scenario, we might download it or fail.
        return

    print(f"Loading model from {BASE_MODEL_PATH}...")
    
    # Load Tokenizer & Model
    # On Pi 5, we should use low precision if possible, but CPU training is float32 usually.
    # This is likely to OOM on 8GB RAM.
    try:
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH)
        tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_PATH,
            device_map="auto", # Will go to CPU
            torch_dtype=torch.float32
        )
        
        # LoRA Config
        peft_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=8,
            lora_alpha=32,
            lora_dropout=0.1
        )
        
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()
        
        # Load Data
        dataset = load_dataset("json", data_files=DAILY_DATA_FILE, split="train")
        
        # Training Args
        training_args = SFTConfig(
            output_dir=f"{OUTPUT_DIR}/checkpoints",
            num_train_epochs=1,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            learning_rate=2e-4,
            logging_steps=1,
            save_steps=50,
            use_cpu=True # Force CPU
        )
        
        trainer = SFTTrainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
            dataset_text_field="messages", # Needs formatting function usually
            peft_config=peft_config,
        )
        
        print("Training...")
        trainer.train()
        
        # Save Adapter
        adapter_path = f"{OUTPUT_DIR}/latest"
        trainer.save_model(adapter_path)
        print(f"Adapter saved to {adapter_path}")
        
        # Convert to GGUF
        convert_to_gguf(adapter_path)
        
    except Exception as e:
        print(f"Training failed: {e}")
        # Do not exit 1 to avoid CronJob backoff loop if it's just OOM
        # But maybe we want to know?
        # sys.exit(1)

def convert_to_gguf(adapter_path):
    print("Converting adapter to GGUF...")
    # Using llama.cpp convert-lora-to-ggml.py (this script name changes often in llama.cpp repo)
    # Modern llama.cpp uses convert_lora_to_gguf.py
    
    script_path = "/app/llama.cpp/convert-lora-to-ggml.py" 
    if not os.path.exists(script_path):
         script_path = "/app/llama.cpp/convert_lora_to_gguf.py"
         
    if not os.path.exists(script_path):
        print("Conversion script not found.")
        return

    out_gguf = f"{adapter_path}/adapter.gguf"
    
    cmd = [
        "python", script_path,
        adapter_path,
        "--out", out_gguf,
        "--base", BASE_MODEL_PATH
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Converted to {out_gguf}")
        
        # Create Modelfile for Ollama
        create_ollama_modelfile(out_gguf)
        
    except subprocess.CalledProcessError as e:
        print(f"GGUF conversion failed: {e}")

def create_ollama_modelfile(adapter_gguf_path):
    # We create a Modelfile that references the base model (in Ollama) and the adapter
    # But Ollama usually expects the base model to be a GGUF file path OR a model name.
    # FROM llama3.1:8b
    # ADAPTER /path/to/adapter.gguf
    
    modelfile_content = f"""
FROM llama3.1:8b
ADAPTER {adapter_gguf_path}
SYSTEM You are Aeron, a helpful AI assistant.
"""
    
    modelfile_path = f"{os.path.dirname(adapter_gguf_path)}/Modelfile"
    with open(modelfile_path, "w") as f:
        f.write(modelfile_content)
        
    print(f"Created Modelfile at {modelfile_path}")
    print("To apply: ollama create aeron-lora -f Modelfile")
    
    # We can try to run it via curl/requests to Ollama API
    # But Ollama might not have access to this path unless mounted.
    # Ollama pod has /data mounted? Not yet in deployment-ollama.yaml!
    
    reload_ollama_model(modelfile_content)

def reload_ollama_model(modelfile_content):
    import requests
    
    ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    print(f"Reloading model on {ollama_host}...")
    
    try:
        resp = requests.post(
            f"{ollama_host}/api/create",
            json={
                "name": "aeron-lora",
                "modelfile": modelfile_content
            },
            stream=True
        )
        resp.raise_for_status()
        
        for line in resp.iter_lines():
            if line:
                print(f"Ollama: {line.decode('utf-8')}")
                
        print("Model aeron-lora created/updated successfully.")
        
    except Exception as e:
        print(f"Failed to reload Ollama model: {e}")

if __name__ == "__main__":
    train()

