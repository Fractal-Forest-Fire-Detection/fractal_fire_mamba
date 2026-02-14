
import os
import sys

def check_paths():
    print(f"CWD: {os.getcwd()}")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Base Dir: {base_dir}")
    
    target_dir = os.path.join(base_dir, "data/real/images")
    print(f"Target Dir: {target_dir}")
    
    if os.path.exists(target_dir):
        print("✅ Target dir exists.")
        files = os.listdir(target_dir)
        print(f"Files found: {files}")
        
        test_file = "Fire-scaled.jpg"
        full_path = os.path.join(target_dir, test_file)
        print(f"Testing access to: {full_path}")
        if os.path.exists(full_path):
            print("✅ File exists!")
        else:
            print("❌ File NOT found at expected path.")
    else:
        print("❌ Target dir NOT found.")

if __name__ == "__main__":
    check_paths()
