
print("Importing numpy...")
import numpy as np
print("Importing VisualProcessor...")
try:
    from processors.visual_processor import VisualProcessor
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
except KeyboardInterrupt:
    print("Caught KeyboardInterrupt")
