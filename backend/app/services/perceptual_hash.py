import io
from PIL import Image
import numpy as np

def compute_dhash(image_bytes: bytes, hash_size: int = 8) -> str:
    """
    Computes a Difference Hash (dHash) for an image buffer.
    Returns a 16-character hex string representing a 64-bit perceptual hash.
    Returns None if the image cannot be decoded.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # Convert to grayscale and resize to (hash_size + 1, hash_size)
        # Using 9x8 for an 8x8 comparison grid
        grayscale = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
        pixels = np.array(grayscale, dtype=np.int16)
        
        # Calculate horizontal differences (pixel[x] > pixel[x+1])
        diff = pixels[:, :-1] > pixels[:, 1:]
        
        # Flatten and convert boolean array to integer
        flat_diff = diff.flatten()
        
        # Convert 64 booleans into a 64-bit integer
        hash_int = 0
        for bit in flat_diff:
            hash_int = (hash_int << 1) | int(bit)
            
        # Format as 16-character hex string
        return f"{hash_int:016x}"
    except Exception:
        return None

def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Calculates the Hamming distance between two hex-encoded perceptual hashes.
    A distance of 0 means visually identical.
    A distance <= 6 indicates high visual similarity (re-compressed, scaled, or minor edits).
    """
    if not hash1 or not hash2 or len(hash1) != len(hash2):
        return 64
    try:
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        # XOR to find differing bits, count bit set
        xor_val = val1 ^ val2
        return bin(xor_val).count("1")
    except ValueError:
        return 64
