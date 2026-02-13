"""
Script to download Mamba-130m model from Hugging Face
Usage: python scripts/download_mamba.py
"""
import os
import sys
from transformers import MambaConfig, MambaModel, AutoTokenizer

def download_model():
    print("⬇️  Downloading Mamba-130m (State Spaces) from Hugging Face...")
    model_name = "state-spaces/mamba-130m-hf"
    cache_dir = os.path.join(os.getcwd(), "models", "mamba-130m")
    
    try:
        # Create directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Download Config
        print(f"   Fetching config to {cache_dir}...")
        config = MambaConfig.from_pretrained(model_name, cache_dir=cache_dir)
        config.save_pretrained(cache_dir)
        
        # Download Model (Weights)
        print(f"   Fetching model weights...")
        model = MambaModel.from_pretrained(model_name, cache_dir=cache_dir)
        model.save_pretrained(cache_dir)
        
        # Download Tokenizer (Essential for text, used here for consistency)
        print(f"   Fetching tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
        tokenizer.save_pretrained(cache_dir)
        
        print(f"\n✅ Mamba Model downloaded successfully to:\n   {cache_dir}")
        print("   Ready for Phase-0 Fusion Engine integration.")
        
    except Exception as e:
        print(f"\n❌ Error downloading model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_model()
