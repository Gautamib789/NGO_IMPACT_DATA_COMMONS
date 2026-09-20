import io
import time
import hashlib
from PIL import Image, ImageDraw
import numpy as np

from app.services.document_tamper_engine import DocumentTamperEngine
from app.models import NGODetail

def run_performance_tests():
    print("=== STARTING COMPREHENSIVE FILE TYPE PERFORMANCE & SAFEGUARD TESTS ===")
    
    # Create fake NGO profile for testing
    dummy_ngo = NGODetail(
        id=999,
        org_name="Benchmark NGO",
        registration_number="REG-BENCH-2026",
        tax_id="TAX-BENCH-2026",
        pan="AAATC1234F"
    )

    test_cases = []

    # 1. Small clean PNG
    buf1 = io.BytesIO()
    img1 = Image.new("RGB", (600, 400), color=(255, 255, 255))
    draw1 = ImageDraw.Draw(img1)
    draw1.text((30, 30), "Small Clean Certificate REG-BENCH-2026 PAN AAATC1234F", fill=(0, 0, 0))
    img1.save(buf1, format="PNG")
    bytes1 = buf1.getvalue()
    test_cases.append(("1. Small Clean PNG", "clean_small.png", bytes1, "REGISTRATION"))

    # 2. Small clean JPG
    buf2 = io.BytesIO()
    img1.save(buf2, format="JPEG", quality=90)
    bytes2 = buf2.getvalue()
    test_cases.append(("2. Small Clean JPG", "clean_small.jpg", bytes2, "REGISTRATION"))

    # 3. Screenshot of certificate
    buf3 = io.BytesIO()
    img3 = Image.new("RGB", (1920, 1080), color=(245, 245, 245))
    draw3 = ImageDraw.Draw(img3)
    draw3.text((50, 50), "Government Registry Certificate Screenshot REG-BENCH-2026 AAATC1234F", fill=(0, 0, 0))
    draw3.rectangle([(50, 100), (1870, 1000)], outline=(100, 100, 100), width=2)
    img3.save(buf3, format="PNG")
    bytes3 = buf3.getvalue()
    test_cases.append(("3. Certificate Screenshot", "screenshot.png", bytes3, "REGISTRATION"))

    # 4. Cropped/partial certificate
    buf4 = io.BytesIO()
    img4 = Image.new("RGB", (800, 200), color=(255, 255, 255)) # Different aspect ratio
    draw4 = ImageDraw.Draw(img4)
    draw4.text((20, 20), "Partial Certificate Header REG-BENCH-2026", fill=(0, 0, 0))
    img4.save(buf4, format="PNG")
    bytes4 = buf4.getvalue()
    test_cases.append(("4. Cropped/Partial Certificate", "cropped.png", bytes4, "REGISTRATION"))

    # 5. Large PNG (4000x4000)
    buf5 = io.BytesIO()
    img5 = Image.new("RGB", (4000, 4000), color=(250, 250, 250))
    draw5 = ImageDraw.Draw(img5)
    draw5.text((100, 100), "Large PNG Certificate REG-BENCH-2026 AAATC1234F", fill=(0, 0, 0))
    img5.save(buf5, format="PNG")
    bytes5 = buf5.getvalue()
    test_cases.append(("5. Large PNG (4000x4000)", "large_doc.png", bytes5, "REGISTRATION"))

    # 6. Large JPG (5000x3500)
    buf6 = io.BytesIO()
    img6 = Image.new("RGB", (5000, 3500), color=(250, 250, 250))
    draw6 = ImageDraw.Draw(img6)
    draw6.text((100, 100), "Large JPG Photo REG-BENCH-2026 AAATC1234F", fill=(0, 0, 0))
    img6.save(buf6, format="JPEG", quality=85)
    bytes6 = buf6.getvalue()
    test_cases.append(("6. Large JPG (5000x3500)", "large_photo.jpg", bytes6, "REGISTRATION"))

    # 7. Visually Modified Certificate (with reference divergence)
    buf7 = io.BytesIO()
    img7 = img1.copy()
    draw7 = ImageDraw.Draw(img7)
    draw7.rectangle([(100, 100), (400, 300)], fill=(0, 0, 0)) # Visually modified block
    img7.save(buf7, format="PNG")
    bytes7 = buf7.getvalue()
    test_cases.append(("7. Modified Certificate", "modified.png", bytes7, "REGISTRATION"))

    # 8. Corrupt image
    bytes8 = b"\x89PNG\r\n\x1a\nTRUNCATED_CORRUPT_BYTES_STREAM"
    test_cases.append(("8. Corrupt Image", "corrupt.png", bytes8, "REGISTRATION"))

    # 9. Unsupported file
    bytes9 = b"UNSUPPORTED_BINARY_EXE_FILE_DATA_HEADER"
    test_cases.append(("9. Unsupported File", "binary.exe", bytes9, "REGISTRATION"))

    results = []

    for name, filename, file_bytes, doc_type in test_cases:
        t0 = time.time()
        
        # Use clean small PNG as reference for case 7 and case 4
        ref = bytes1 if name in ["4. Cropped/Partial Certificate", "7. Modified Certificate"] else None

        analysis = DocumentTamperEngine.analyze_document(
            file_bytes=file_bytes,
            filename=filename,
            document_type=doc_type,
            ngo_profile=dummy_ngo,
            reference_bytes=ref
        )
        elapsed = time.time() - t0

        size_kb = len(file_bytes) / 1024.0
        dims = analysis.get("exif_metadata", "")
        # Extract dimensions if present
        dims_str = "N/A"
        try:
            img = Image.open(io.BytesIO(file_bytes))
            dims_str = f"{img.width}x{img.height}"
        except Exception:
            dims_str = "N/A"

        results.append({
            "name": name,
            "filename": filename,
            "size_kb": f"{size_kb:.1f} KB",
            "dimensions": dims_str,
            "time_sec": f"{elapsed:.4f}s",
            "score": f"{analysis['tamper_risk_score']:.1f}%",
            "status": analysis['verification_status'],
            "success": True if elapsed < 5.0 else False
        })

    print("\n" + "="*80)
    print(f"{'TEST CASE':<30} | {'SIZE':<10} | {'DIMS':<11} | {'TIME':<8} | {'SCORE':<7} | {'STATUS':<20}")
    print("="*80)
    for r in results:
        print(f"{r['name']:<30} | {r['size_kb']:<10} | {r['dimensions']:<11} | {r['time_sec']:<8} | {r['score']:<7} | {r['status']:<20}")
    print("="*80)

if __name__ == "__main__":
    run_performance_tests()
