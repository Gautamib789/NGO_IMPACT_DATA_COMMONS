import re
import io
import json
import hashlib
import mimetypes
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List

import PIL.Image as Image
import PIL.ImageOps as ImageOps
import PIL.ImageEnhance as ImageEnhance
import PIL.ImageFilter as ImageFilter
import numpy as np

Image.MAX_IMAGE_PIXELS = 50_000_000

# Try importing local OCR engines
try:
    from rapidocr_onnxruntime import RapidOCR
    RAPID_OCR_ENGINE = RapidOCR()
except Exception:
    RAPID_OCR_ENGINE = None

try:
    import pytesseract
except Exception:
    pytesseract = None

EDITING_SOFTWARE_SIGNATURES = [
    "photoshop", "gimp", "canva", "paint.net", "mspaint", 
    "pixlr", "fotor", "affinity photo", "krita", "photopea", 
    "lightroom", "adobe acrobat", "coreldraw"
]

MAGIC_BYTE_MAP = [
    (b"%PDF-", "application/pdf", ".pdf"),
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"RIFF", "image/webp", ".webp"),
    (b"II*\x00", "image/tiff", ".tif"),
    (b"MM\x00*", "image/tiff", ".tif"),
    (b"BM", "image/bmp", ".bmp")
]


class DocumentTamperEngine:

    @staticmethod
    def compute_sha256(file_bytes: bytes) -> str:
        """Computes hex SHA-256 hash from raw file bytes."""
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def detect_mime_and_magic(file_bytes: bytes, filename: str) -> Tuple[str, bool]:
        """
        Validates magic bytes against file extension.
        Returns (detected_mime, is_extension_valid).
        """
        ext = (filename.lower().split(".")[-1] if "." in filename else "")
        detected_mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        
        magic_matched_mime = None
        for magic, mime, canonical_ext in MAGIC_BYTE_MAP:
            if file_bytes.startswith(magic):
                magic_matched_mime = mime
                break
        
        if magic_matched_mime:
            detected_mime = magic_matched_mime
            is_valid = True
            if ext == "pdf" and magic_matched_mime != "application/pdf":
                is_valid = False
            elif ext in ["jpg", "jpeg"] and magic_matched_mime != "image/jpeg":
                is_valid = False
            elif ext == "png" and magic_matched_mime != "image/png":
                is_valid = False
            return detected_mime, is_valid

        if ext in ["pdf", "jpg", "jpeg", "png", "webp", "tif", "tiff", "bmp"]:
            return detected_mime, False

        return detected_mime, True

    @staticmethod
    def extract_metadata_and_signatures(file_bytes: bytes) -> Tuple[list, list]:
        """
        Scans raw file bytes for editing software signatures, EXIF/XMP metadata attributes,
        and creation/modification timestamp inconsistencies.
        """
        detected_flags = []
        metadata_findings = []

        try:
            sample_header = file_bytes[:100000].decode("ascii", errors="ignore")
            sample_footer = file_bytes[-50000:].decode("ascii", errors="ignore")
            full_text_sample = (sample_header + sample_footer).lower()

            # 1. Check editing software signatures
            for sig in EDITING_SOFTWARE_SIGNATURES:
                if sig in full_text_sample:
                    detected_flags.append(f"EDITING_SOFTWARE_DETECTED: {sig.title()}")
                    metadata_findings.append(f"Editing software metadata detected: {sig.title()} found in header/metadata.")

            # 2. Check XMP Creation vs Modification Date inconsistency
            xmp_sample = sample_header + sample_footer
            if "<xmp:ModifyDate>" in xmp_sample or "<xmp:CreateDate>" in xmp_sample:
                modify_match = re.search(r"<xmp:ModifyDate>([^<]+)</xmp:ModifyDate>", xmp_sample)
                create_match = re.search(r"<xmp:CreateDate>([^<]+)</xmp:CreateDate>", xmp_sample)
                if modify_match:
                    metadata_findings.append(f"XMP Metadata: ModifyDate tag present ({modify_match.group(1).strip()}).")
                if create_match:
                    metadata_findings.append(f"XMP Metadata: CreateDate tag present ({create_match.group(1).strip()}).")

                if modify_match and create_match and modify_match.group(1).strip() != create_match.group(1).strip():
                    if any(sig in full_text_sample for sig in EDITING_SOFTWARE_SIGNATURES):
                        detected_flags.append("METADATA_TIMESTAMP_INCONSISTENCY")
                        metadata_findings.append("Creation/modification metadata inconsistency: Document modification timestamp updated via software tool.")

            # 3. Check for PDF or JPEG EOF payload anomalies
            if b"%PDF-" in file_bytes[:1024]:
                if not file_bytes.rstrip().endswith(b"%%EOF"):
                    last_eof = file_bytes.rfind(b"%%EOF")
                    if last_eof != -1 and (len(file_bytes) - last_eof) > 200:
                        detected_flags.append("FILE_PAYLOAD_ANOMALY: Trailing data detected after PDF %%EOF marker")
                        metadata_findings.append("Trailer anomaly: Extra payload appended after EOF.")

            elif file_bytes.startswith(b"\xff\xd8\xff"):
                last_eoi = file_bytes.rfind(b"\xff\xd9")
                if last_eoi != -1 and (len(file_bytes) - last_eoi) > 500:
                    detected_flags.append("FILE_PAYLOAD_ANOMALY: Trailing data detected after JPEG EOI marker")
                    metadata_findings.append("JPEG anomaly: Appended binary stream detected after EOI marker.")

        except Exception as e:
            metadata_findings.append(f"Metadata scan note: {str(e)}")

        return detected_flags, metadata_findings

    @staticmethod
    def extract_ocr_text(file_bytes: bytes, filename: str = "") -> str:
        """
        Performs real image pixel OCR for PNG/JPG/WebP/BMP documents using Pillow, NumPy & RapidOCR/pytesseract.
        Falls back to PDF stream extraction or safe raw text scanning for non-raster files.
        """
        if not file_bytes:
            return ""

        extracted_text = ""
        # 1. Try raster image OCR with Pillow + multi-pass preprocessing + RapidOCR / pytesseract
        try:
            img = Image.open(io.BytesIO(file_bytes))
            
            # EXIF Orientation Correction
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

            # Safe downsample if dimensions > 2048px
            if img.width > 2048 or img.height > 2048:
                img_copy = img.copy()
                img_copy.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
            else:
                img_copy = img.copy()

            # Preprocessing variants for multi-pass OCR
            passes = []
            
            # Pass A: Standard RGB
            passes.append(img_copy.convert("RGB"))
            
            # Pass B: High Contrast Grayscale
            gray = ImageOps.grayscale(img_copy)
            contrast_img = ImageEnhance.Contrast(gray).enhance(2.0)
            sharp_img = ImageEnhance.Sharpness(contrast_img).enhance(1.5)
            passes.append(sharp_img.convert("RGB"))

            # Execute multi-pass OCR
            for p_img in passes:
                if extracted_text and len(extracted_text) >= 15:
                    break

                # Try RapidOCR (high performance local ONNX OCR)
                if RAPID_OCR_ENGINE is not None:
                    try:
                        buf = io.BytesIO()
                        p_img.save(buf, format="PNG")
                        res, _ = RAPID_OCR_ENGINE(buf.getvalue())
                        if res:
                            lines = [item[1] for item in res if item and len(item) > 1 and item[1]]
                            text_found = " ".join(lines).strip()
                            if len(text_found) > len(extracted_text):
                                extracted_text = text_found
                    except Exception:
                        pass

                # Fallback to pytesseract if RapidOCR produced no text or was unavailable
                if (not extracted_text or len(extracted_text) < 10) and pytesseract is not None:
                    try:
                        tess_text = pytesseract.image_to_string(p_img).strip()
                        if len(tess_text) > len(extracted_text):
                            extracted_text = tess_text
                    except Exception:
                        pass

        except Exception:
            # Non-raster container (e.g., PDF)
            pass

        # 2. PDF / Container ASCII stream fallback if OCR returned empty
        if not extracted_text:
            try:
                is_raster = file_bytes.startswith(b"\x89PNG") or file_bytes.startswith(b"\xff\xd8\xff") or file_bytes.startswith(b"RIFF")
                if not is_raster:
                    sample_bytes = file_bytes[:2000000]
                    text_printable = re.findall(r"[\x20-\x7E\s]{4,}", sample_bytes.decode("ascii", errors="ignore"))
                    filtered = [t for t in text_printable if not re.match(r"^(IHDR|IDAT|IEND|sRGB|gAMA|pHYs|JFIF|Exif)", t.strip())]
                    combined_text = " ".join(filtered)
                    extracted_text = re.sub(r"\s+", " ", combined_text).strip()
            except Exception:
                extracted_text = ""

        return extracted_text[:4000]

    @staticmethod
    def normalize_identifier(text: str) -> str:
        """
        Normalizes OCR strings for robust matching:
        - Uppercase
        - Remove spaces, dashes, dots, underscores
        - Replace common OCR digit/letter confusions (O->0, I->1, L->1)
        """
        if not text:
            return ""
        s = text.upper()
        s = re.sub(r"[\s\-_.]", "", s)
        s = s.replace("O", "0").replace("I", "1").replace("L", "1")
        return s

    @staticmethod
    def normalize_organization_name(name: str) -> str:
        """
        Normalizes organization names for robust matching:
        - Uppercase
        - Remove punctuation, special characters
        - Normalize spaces
        - Handles harmless legal suffixes/descriptors like 'INDIA', 'TRUST', 'FOUNDATION', etc.
        """
        if not name:
            return ""
        s = name.upper()
        s = re.sub(r"[^\w\s]", " ", s)
        words = [w for w in s.split() if w]
        if len(words) > 1 and words[-1] in ["INDIA", "NATIONAL", "GLOBAL", "BHARAT"]:
            words.pop()
        return " ".join(words)

    @staticmethod
    def extract_organization_names(ocr_text: str) -> List[str]:
        """
        Extracts candidate organization / NGO names from OCR text.
        """
        if not ocr_text:
            return []
        
        candidates = []
        org_matches = re.findall(
            r"\b[A-Z0-9\s&]{3,40}\b\s+(?:FOUNDATION|TRUST|SOCIETY|ASSOCIATION|WELFARE|CHARITY|INSTITUTE|ORGANIZATION)\b",
            ocr_text,
            re.IGNORECASE
        )
        for m in org_matches:
            clean_m = re.sub(r"\s+", " ", m).strip()
            if len(clean_m) >= 5 and not clean_m.upper().startswith("THIS IS"):
                candidates.append(clean_m)
        
        label_matches = re.findall(
            r"(?:NAME OF NGO|NAME OF ORGANIZATION|NAME OF TRUST|ORGANIZATION NAME|INSTITUTION NAME|NAME)\s*[:\-]\s*([A-Z0-9\s&,.-]{4,50})",
            ocr_text,
            re.IGNORECASE
        )
        for lm in label_matches:
            clean_lm = re.sub(r"\s+", " ", lm).strip()
            if len(clean_lm) >= 4:
                candidates.append(clean_lm)

        return list(dict.fromkeys(candidates))

    @staticmethod
    def extract_document_identifiers(ocr_text: str) -> Dict[str, List[str]]:
        """
        Extracts registration numbers and PAN / Tax IDs from OCR text.
        """
        res = {"reg_numbers": [], "pans": []}
        if not ocr_text:
            return res

        # Registration patterns: REG-9999-999, REG-2024-001, REG/2024/001, 12A-12345, etc.
        reg_candidates = re.findall(r"\b(?:REG|12A|80G|FCRA)[-/\s_]*[A-Z0-9-]{3,15}\b", ocr_text, re.IGNORECASE)
        
        ignored_words = {"REGISTRATION", "REGISTERED", "REGISTRAR", "REGISTRATIONS", "REGISTRATIONNUMBER"}
        valid_regs = []
        for cand in reg_candidates:
            clean_cand = cand.strip().upper()
            if clean_cand not in ignored_words and not clean_cand.startswith("REGIST"):
                # Must contain at least one digit or non-alpha character to be a real registration ID
                if any(char.isdigit() or char in "-/" for char in cand):
                    valid_regs.append(cand.strip())

        pan_matches = re.findall(r"\b[A-Z]{5}\d{4}[A-Z]\b", ocr_text, re.IGNORECASE)

        res["reg_numbers"] = list(dict.fromkeys(valid_regs))
        res["pans"] = list(dict.fromkeys([p.strip() for p in pan_matches]))
        return res

    @staticmethod
    def analyze_image_forensics(
        file_bytes: bytes,
        filename: str,
        reference_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Performs visual image forensics using Pillow & NumPy:
        - Image container validation & readability
        - JPEG compression & quantization table analysis
        - Conservative local noise/texture anomaly detection (bounded max 1024px)
        - SSIM-style structural similarity comparison against trusted reference (if provided and reliable)
        """
        findings: List[str] = []
        risk_penalties: List[Tuple[str, float]] = []
        image_metadata: Dict[str, Any] = {}

        ext = (filename.lower().split(".")[-1] if "." in filename else "")
        try:
            img = Image.open(io.BytesIO(file_bytes))
            image_metadata["format"] = img.format
            image_metadata["mode"] = img.mode
            image_metadata["dimensions"] = f"{img.width}x{img.height}"
        except Exception as e:
            if ext in ["png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff"]:
                return {
                    "is_raster": True,
                    "valid": False,
                    "findings": [f"Corrupt or truncated raster image stream: {str(e)}"],
                    "risk_penalties": [("Corrupt or truncated image container", 25.0)],
                    "metadata": {}
                }
            return {
                "is_raster": False,
                "valid": True,
                "findings": ["Non-raster container (e.g. PDF/Binary format). Skipping visual pixel forensics."],
                "risk_penalties": [],
                "metadata": {}
            }

        # Validate readability & check truncated stream
        try:
            img_copy = img.copy()
        except Exception as e:
            findings.append(f"Image container warning: Corrupt or incomplete pixel stream ({str(e)}).")
            risk_penalties.append(("Corrupt image stream", 20.0))
            return {
                "is_raster": True,
                "valid": False,
                "findings": findings,
                "risk_penalties": risk_penalties,
                "metadata": image_metadata
            }

        # 1. JPEG Compression & Quantization Table Analysis
        if img.format in ["JPEG", "MPO"]:
            q_tables = getattr(img, "quantization", None)
            if q_tables and len(q_tables) >= 2:
                try:
                    lum_table = np.array(q_tables[0], dtype=np.float32)
                    chrom_table = np.array(q_tables[1], dtype=np.float32)
                    if len(lum_table) == 64 and len(chrom_table) == 64:
                        lum_mean = np.mean(lum_table)
                        chrom_mean = np.mean(chrom_table)
                        if lum_mean > 0 and (chrom_mean / lum_mean) > 3.8:
                            findings.append("JPEG compression characteristics show potential recompression or multi-stage encoding.")
                            risk_penalties.append(("JPEG compression anomaly", 10.0))
                except Exception:
                    pass

        # 2. Conservative Local Image Anomaly Detection (Bounded thumbnail max 1024px)
        try:
            img_analysis = img_copy.copy()
            if img_analysis.width > 1024 or img_analysis.height > 1024:
                img_analysis.thumbnail((1024, 1024), Image.Resampling.LANCZOS)

            gray_img = img_analysis.convert("L")
            arr = np.array(gray_img, dtype=np.float32)
            h, w = arr.shape

            if h >= 64 and w >= 64:
                block_size = 32
                bh, bw = h // block_size, w // block_size
                block_vars = []
                block_gradients = []

                for i in range(bh):
                    for j in range(bw):
                        blk = arr[i*block_size:(i+1)*block_size, j*block_size:(j+1)*block_size]
                        b_var = float(np.var(blk))
                        gx, gy = np.gradient(blk)
                        grad_norm = float(np.mean(np.hypot(gx, gy)))
                        block_vars.append(b_var)
                        block_gradients.append(grad_norm)

                block_vars_arr = np.array(block_vars)
                block_grads_arr = np.array(block_gradients)

                text_mask = block_grads_arr > 15.0
                flat_mask = block_vars_arr < 5.0
                bg_texture_mask = ~(text_mask | flat_mask)

                if np.sum(bg_texture_mask) >= 6:
                    bg_vars = block_vars_arr[bg_texture_mask]
                    bg_mean = float(np.mean(bg_vars))
                    bg_std = float(np.std(bg_vars))

                    if bg_std > 1.0:
                        outliers = int(np.sum(bg_vars > (bg_mean + 4.5 * bg_std)))
                        if 1 <= outliers <= 4 and (outliers / len(bg_vars)) < 0.15:
                            findings.append("Local image noise/texture anomaly detected in document region.")
                            risk_penalties.append(("Local image anomaly", 10.0))
        except Exception as e:
            findings.append(f"Local anomaly scan note: {str(e)}")

        # 3. Trusted Reference Image Comparison (SSIM with Aspect Ratio & Partial Crop Safety)
        if reference_bytes:
            try:
                ref_img = Image.open(io.BytesIO(reference_bytes))
                ref_w, ref_h = ref_img.width, ref_img.height
                img_w, img_h = img_copy.width, img_copy.height

                aspect_curr = img_w / float(img_h) if img_h > 0 else 1.0
                aspect_ref = ref_w / float(ref_h) if ref_h > 0 else 1.0
                aspect_diff = abs(aspect_curr - aspect_ref) / max(aspect_ref, 0.001)
                size_ratio = (img_w * img_h) / float(ref_w * ref_h) if (ref_w * ref_h) > 0 else 1.0

                if aspect_diff > 0.25 or size_ratio < 0.35 or size_ratio > 3.0:
                    findings.append("Partial/cropped document detected or reference comparison unavailable.")
                    image_metadata["reference_comparison_note"] = "Skipped due to dimension/aspect ratio mismatch"
                else:
                    target_size = (512, 512)
                    img1 = np.array(img_copy.convert("L").resize(target_size), dtype=np.float32)
                    img2 = np.array(ref_img.convert("L").resize(target_size), dtype=np.float32)

                    C1 = (0.01 * 255) ** 2
                    C2 = (0.03 * 255) ** 2

                    mu1 = float(np.mean(img1))
                    mu2 = float(np.mean(img2))
                    var1 = float(np.var(img1))
                    var2 = float(np.var(img2))
                    cov12 = float(np.mean((img1 - mu1) * (img2 - mu2)))

                    ssim_score = ((2 * mu1 * mu2 + C1) * (2 * cov12 + C2)) / ((mu1**2 + mu2**2 + C1) * (var1 + var2 + C2))
                    ssim_pct = float(ssim_score * 100.0)
                    image_metadata["ssim_similarity_score"] = round(ssim_pct, 2)

                    if ssim_score < 0.88:
                        diff_pct = (1.0 - ssim_score) * 100.0
                        penalty = min(25.0, max(10.0, diff_pct * 0.75))
                        findings.append(f"Visual difference detected compared with trusted reference document (Structural similarity: {ssim_pct:.1f}%).")
                        risk_penalties.append(("Visual reference divergence", penalty))
                    else:
                        findings.append(f"Visual similarity to trusted reference document verified ({ssim_pct:.1f}%).")
            except Exception as e:
                findings.append("Partial/cropped document detected or reference comparison unavailable.")

        return {
            "is_raster": True,
            "valid": True,
            "findings": findings,
            "risk_penalties": risk_penalties,
            "metadata": image_metadata
        }

    @classmethod
    def analyze_document(
        cls, 
        file_bytes: bytes, 
        filename: str, 
        document_type: str,
        ngo_profile: Optional[Any] = None,
        reference_bytes: Optional[bytes] = None,
        db_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Performs multi-layered document & image tamper risk analysis:
        - Hex SHA-256 calculation
        - Magic byte validation
        - Metadata/editing software signature inspection
        - Multi-pass Image OCR text extraction & document-type identity cross-validation
        - Pillow + NumPy visual image forensics (local anomaly, JPEG compression, SSIM reference comparison)
        - Synthesizes all evidence signals into a normalized 0-100 risk score and structured status (VERIFIED, NEEDS_ADMIN_REVIEW, REJECTED).
        """
        sha256_hash = cls.compute_sha256(file_bytes)
        file_size = len(file_bytes)
        mime_type, is_magic_valid = cls.detect_mime_and_magic(file_bytes, filename)

        flags, metadata_notes = cls.extract_metadata_and_signatures(file_bytes)
        ocr_text = cls.extract_ocr_text(file_bytes, filename)

        tamper_score = 0.0
        reasons = []

        if not is_magic_valid:
            tamper_score += 40.0
            reasons.append("MIME/Extension mismatch (Potential extension spoofing attempt).")

        for flag in flags:
            if "EDITING_SOFTWARE_DETECTED" in flag:
                tamper_score += 35.0
                software_name = flag.split(":")[-1].strip() if ":" in flag else "software"
                reasons.append(f"Editing software metadata detected: {software_name}")
            elif "METADATA_TIMESTAMP_INCONSISTENCY" in flag:
                tamper_score += 20.0
                reasons.append("Creation/modification metadata inconsistency tag present.")
            elif "FILE_PAYLOAD_ANOMALY" in flag:
                tamper_score += 30.0
                reasons.append(flag)

        # Document Type Applicability & Identity Validation Engine
        doc_type_upper = (document_type or "").upper()

        profile_org = ""
        profile_reg = ""
        profile_pan = ""

        if ngo_profile:
            profile_org = (getattr(ngo_profile, "org_name", None) or "").strip()
            profile_reg = (getattr(ngo_profile, "registration_number", None) or getattr(ngo_profile, "eighty_g_info", None) or getattr(ngo_profile, "fcra_info", None) or "").strip()
            profile_pan = (getattr(ngo_profile, "pan", None) or getattr(ngo_profile, "tax_id", None) or "").strip()

        # Applicability per document type
        is_org_applicable = bool(profile_org)
        is_reg_applicable = doc_type_upper not in ["PAN_CARD"]
        if doc_type_upper in ["AUDIT_REPORT", "TRUST_DEED", "OTHER"] and not profile_reg:
            is_reg_applicable = False

        is_pan_applicable = doc_type_upper not in ["FCRA_CERTIFICATE"]
        if doc_type_upper in ["AUDIT_REPORT", "TRUST_DEED", "OTHER"] and not profile_pan:
            is_pan_applicable = False

        org_check = {
            "detected_value": None,
            "expected_value": profile_org if is_org_applicable else None,
            "validation_state": "NOT_APPLICABLE" if not is_org_applicable else "NOT_DETECTED",
            "confidence": 100.0 if not is_org_applicable else 0.0
        }

        reg_check = {
            "detected_value": None,
            "expected_value": profile_reg if is_reg_applicable else None,
            "validation_state": "NOT_APPLICABLE" if not is_reg_applicable else "NOT_DETECTED",
            "confidence": 100.0 if not is_reg_applicable else 0.0
        }

        pan_check = {
            "detected_value": None,
            "expected_value": profile_pan if is_pan_applicable else None,
            "validation_state": "NOT_APPLICABLE" if not is_pan_applicable else "NOT_DETECTED",
            "confidence": 100.0 if not is_pan_applicable else 0.0
        }

        if ocr_text and len(ocr_text) >= 10:
            norm_ocr = cls.normalize_identifier(ocr_text)
            extracted_ids = cls.extract_document_identifiers(ocr_text)

            # 1. Organization Name Cross-Validation
            if is_org_applicable and profile_org:
                norm_exp_org = cls.normalize_organization_name(profile_org)
                org_first_word = norm_exp_org.split()[0] if norm_exp_org else ""
                
                if norm_exp_org and (norm_exp_org in cls.normalize_organization_name(ocr_text) or (len(org_first_word) >= 4 and org_first_word in ocr_text.upper())):
                    org_check["detected_value"] = profile_org
                    org_check["validation_state"] = "DETECTED_MATCH"
                    org_check["confidence"] = 98.0
                    metadata_notes.append(f"OCR Verification: Organization Name '{profile_org}' verified in document text.")
                else:
                    cand_orgs = cls.extract_organization_names(ocr_text)
                    conflicting_orgs = [c for c in cand_orgs if cls.normalize_organization_name(c) != norm_exp_org and org_first_word not in c.upper()]
                    if conflicting_orgs:
                        org_check["detected_value"] = conflicting_orgs[0]
                        org_check["validation_state"] = "DETECTED_MISMATCH"
                        org_check["confidence"] = 97.0
                        tamper_score += 35.0
                        reasons.append(f"Organization name mismatch detected. Document contains '{conflicting_orgs[0]}', while registered NGO profile contains '{profile_org}'.")
                        metadata_notes.append(f"Organization Name Mismatch: Found '{conflicting_orgs[0]}' in document text, expected '{profile_org}'.")
                    else:
                        org_check["detected_value"] = None
                        org_check["validation_state"] = "NOT_DETECTED"
                        org_check["confidence"] = 0.0
                        metadata_notes.append(f"Organization Note: Organization name '{profile_org}' not explicitly detected in OCR text.")

            # 2. Registration Number Cross-Validation
            if is_reg_applicable and profile_reg:
                norm_exp_reg = cls.normalize_identifier(profile_reg)
                if norm_exp_reg and norm_exp_reg in norm_ocr:
                    reg_check["detected_value"] = profile_reg
                    reg_check["validation_state"] = "DETECTED_MATCH"
                    reg_check["confidence"] = 98.0
                    metadata_notes.append(f"OCR Verification: Registration Number '{profile_reg}' verified in document text.")
                else:
                    conflicting_regs = [r for r in extracted_ids["reg_numbers"] if cls.normalize_identifier(r) != norm_exp_reg]
                    if conflicting_regs:
                        reg_check["detected_value"] = conflicting_regs[0]
                        reg_check["validation_state"] = "DETECTED_MISMATCH"
                        reg_check["confidence"] = 97.0
                        tamper_score += 35.0
                        reasons.append(f"Registration number mismatch detected. Document contains '{conflicting_regs[0]}', while registered NGO profile contains '{profile_reg}'.")
                        metadata_notes.append(f"Registration Number Mismatch: Found '{conflicting_regs[0]}' in document text, expected '{profile_reg}'.")
                    else:
                        reg_check["detected_value"] = None
                        reg_check["validation_state"] = "NOT_DETECTED"
                        reg_check["confidence"] = 0.0
                        metadata_notes.append(f"Registration Note: Registration number '{profile_reg}' not found in OCR text.")

            # 3. PAN / Tax ID Cross-Validation
            if is_pan_applicable and profile_pan:
                norm_exp_pan = cls.normalize_identifier(profile_pan)
                if norm_exp_pan and norm_exp_pan in norm_ocr:
                    pan_check["detected_value"] = profile_pan
                    pan_check["validation_state"] = "DETECTED_MATCH"
                    pan_check["confidence"] = 99.0
                    metadata_notes.append(f"OCR Verification: PAN '{profile_pan}' verified in document text.")
                else:
                    conflicting_pans = [p for p in extracted_ids["pans"] if cls.normalize_identifier(p) != norm_exp_pan]
                    if conflicting_pans:
                        pan_check["detected_value"] = conflicting_pans[0]
                        pan_check["validation_state"] = "DETECTED_MISMATCH"
                        pan_check["confidence"] = 97.0
                        tamper_score += 35.0
                        reasons.append(f"PAN mismatch detected. Document contains '{conflicting_pans[0]}', while registered NGO profile contains '{profile_pan}'.")
                        metadata_notes.append(f"PAN Mismatch: Found '{conflicting_pans[0]}' in document text, expected '{profile_pan}'.")
                    else:
                        pan_check["detected_value"] = None
                        pan_check["validation_state"] = "NOT_DETECTED"
                        pan_check["confidence"] = 0.0
                        metadata_notes.append(f"PAN Note: PAN '{profile_pan}' not found in OCR text.")

        else:
            if ngo_profile:
                if is_org_applicable and profile_org:
                    org_check["validation_state"] = "NOT_DETECTED"
                    org_check["confidence"] = 0.0
                if is_reg_applicable and profile_reg:
                    reg_check["validation_state"] = "NOT_DETECTED"
                    reg_check["confidence"] = 0.0
                if is_pan_applicable and profile_pan:
                    pan_check["validation_state"] = "NOT_DETECTED"
                    pan_check["confidence"] = 0.0
                metadata_notes.append("OCR Note: Document text unreadable or empty.")

        # 4. Simulated Government Registry Validation
        if db_session and profile_reg:
            try:
                from app.models.government import GovernmentRegistry
                gov_rec = db_session.query(GovernmentRegistry).filter(
                    GovernmentRegistry.registration_number == profile_reg
                ).first()
                if gov_rec:
                    if profile_pan and gov_rec.pan and cls.normalize_identifier(profile_pan) != cls.normalize_identifier(gov_rec.pan):
                        tamper_score += 40.0
                        reasons.append(f"Government registry mismatch: Profile PAN '{profile_pan}' conflicts with Government Registry record '{gov_rec.pan}'.")
                        metadata_notes.append("Government Registry Mismatch: PAN conflicts with central registry record.")
                    if reg_check["validation_state"] == "DETECTED_MISMATCH":
                        tamper_score += 40.0
                        reasons.append("Government registry mismatch: Extracted registration number conflicts with Government Registry database.")
                        metadata_notes.append("Government Registry Mismatch: Registration number conflicts with central registry.")
            except Exception:
                pass

        # Execute Visual Image Forensics Layer via Pillow + NumPy
        forensics = cls.analyze_image_forensics(file_bytes, filename, reference_bytes=reference_bytes)
        for finding in forensics["findings"]:
            metadata_notes.append(finding)
        for penalty_name, penalty_val in forensics["risk_penalties"]:
            tamper_score += penalty_val
            reasons.append(penalty_name)

        # Count Identity Mismatches
        has_org_mismatch = (org_check["validation_state"] == "DETECTED_MISMATCH")
        has_reg_mismatch = (reg_check["validation_state"] == "DETECTED_MISMATCH")
        has_pan_mismatch = (pan_check["validation_state"] == "DETECTED_MISMATCH")
        mismatch_count = sum([has_org_mismatch, has_reg_mismatch, has_pan_mismatch])

        has_identity_mismatch = mismatch_count > 0
        has_gov_mismatch = any("Government registry mismatch" in r for r in reasons)

        # Handle Unreadable Ownership State
        is_unreadable = (not ocr_text or len(ocr_text) < 10)
        requires_identity = (is_org_applicable or is_reg_applicable or is_pan_applicable)

        if is_unreadable and requires_identity and ngo_profile:
            reasons.append("Unreadable document: Ownership could not be automatically established via OCR.")

        # Score Normalization (0 - 100)
        tamper_score = min(100.0, max(0.0, tamper_score))

        # Strict Document Ownership & Verification Decision Logic
        # HARD RULE: Any detected identity mismatch MUST NEVER return VERIFIED or LOW risk.
        if mismatch_count >= 2 or (mismatch_count >= 1 and (tamper_score >= 50.0 or has_gov_mismatch)) or tamper_score >= 70.0:
            status = "REJECTED"
            level = "HIGH"
            tamper_score = max(tamper_score, 70.0)
            msg = f"Document Identity & Integrity Failure: High risk of identity mismatch or document tampering detected (Score: {tamper_score:.1f}%). Document Rejected. Reasons: {'; '.join(reasons)}"
        elif mismatch_count == 1 or tamper_score >= 30.0 or (is_unreadable and requires_identity):
            status = "NEEDS_ADMIN_REVIEW"
            level = "HIGH" if tamper_score >= 70.0 else "MEDIUM"
            if has_identity_mismatch:
                tamper_score = max(tamper_score, 35.0)
            elif is_unreadable and requires_identity:
                tamper_score = max(tamper_score, 30.0)
            msg = f"Document Verification Review Required: Ownership field mismatch or moderate risk detected (Score: {tamper_score:.1f}%). Admin Review Recommended. Reasons: {'; '.join(reasons)}"
        else:
            status = "VERIFIED"
            level = "LOW"
            msg = "Document Identity & Integrity Verified: Document details match authenticated NGO profile with low tamper risk."

        # Structured EXIF & Identity Metadata for Frontend UI
        exif_dict = {
            "summary": " | ".join(metadata_notes) if metadata_notes else "No editing tags found.",
            "tamper_risk_score": round(tamper_score, 1),
            "tamper_risk_level": level,
            "verification_status": status,
            "identity_checks": {
                "organization_name": org_check,
                "registration_number": reg_check,
                "pan": pan_check
            },
            "detected_org_name": org_check["detected_value"],
            "expected_org_name": org_check["expected_value"],
            "org_mismatch": org_check["validation_state"] == "DETECTED_MISMATCH",
            "detected_reg_number": reg_check["detected_value"],
            "expected_reg_number": reg_check["expected_value"],
            "reg_mismatch": reg_check["validation_state"] == "DETECTED_MISMATCH",
            "detected_pan": pan_check["detected_value"],
            "expected_pan": pan_check["expected_value"],
            "pan_mismatch": pan_check["validation_state"] == "DETECTED_MISMATCH",
            "reasons": reasons
        }

        return {
            "sha256_hash": sha256_hash,
            "mime_type": mime_type,
            "file_size": file_size,
            "tamper_risk_score": tamper_score,
            "tamper_risk_level": level,
            "verification_status": status,
            "verification_message": msg,
            "ocr_text": ocr_text,
            "exif_metadata": json.dumps(exif_dict)
        }

    @staticmethod
    def analyze_project_evidence(
        file_bytes: bytes,
        filename: str,
        evidence_type: str,
        project_id: int,
        ngo_profile: Any = None,
        db_session: Any = None
    ) -> Dict[str, Any]:
        """
        Performs comprehensive forensic analysis on project evidence files/photos.
        Includes magic byte validation, SHA-256 hashing, perceptual hashing (dHash),
        EXIF inspection, JPEG recompression analysis, DB duplicate detection, and OCR matching.
        """
        from app.services.perceptual_hash import compute_dhash, hamming_distance

        sha256_hash = DocumentTamperEngine.compute_sha256(file_bytes)
        mime_type, is_valid_ext = DocumentTamperEngine.detect_mime_and_magic(file_bytes, filename)
        p_hash = compute_dhash(file_bytes)

        # Dimensions & Pillow validation
        image_width = None
        image_height = None
        is_corrupt = False
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                image_width, image_height = img.size
                img.verify()
        except Exception:
            if not filename.lower().endswith(".pdf"):
                is_corrupt = True

        # Extract metadata & signatures
        flags, meta_findings = DocumentTamperEngine.extract_metadata_and_signatures(file_bytes)

        # JPEG noise & anomaly analysis
        forensics_res = DocumentTamperEngine.analyze_image_forensics(file_bytes, filename)
        forensics_score = sum(penalty for _, penalty in forensics_res.get("risk_penalties", []))
        forensics_reasons = forensics_res.get("findings", [])

        # OCR
        ocr_text = DocumentTamperEngine.extract_ocr_text(file_bytes)

        tamper_score = 0.0
        reasons = []

        if not is_valid_ext:
            tamper_score += 40.0
            reasons.append(f"Magic bytes mismatch: file extension '{filename}' does not match file format header.")

        if is_corrupt:
            tamper_score += 50.0
            reasons.append("Corrupt or damaged image container detected.")

        for flag in flags:
            if flag == "EDITING_SOFTWARE_DETECTED":
                tamper_score += 10.0
                reasons.append("Editing software metadata signature detected (Photoshop/Canva/GIMP/etc.).")
            elif flag == "TIMESTAMP_INCONSISTENCY":
                tamper_score += 15.0
                reasons.append("Creation/modification timestamp inconsistency in file metadata.")
            elif flag == "TRAILER_ANOMALY":
                tamper_score += 20.0
                reasons.append("Unexpected payload appended after EOF marker.")

        if forensics_score > 0:
            tamper_score += forensics_score
            reasons.extend(forensics_reasons)

        # Duplicate evidence check against DB (ProjectEvidence)
        if db_session:
            from app.models.project import ProjectEvidence

            # 1. Exact SHA-256 duplicate
            existing_exact = db_session.query(ProjectEvidence).filter(
                ProjectEvidence.sha256_hash == sha256_hash
            ).all()

            for ex in existing_exact:
                if ex.project_id == project_id:
                    tamper_score += 20.0
                    reasons.append("Exact duplicate evidence file uploaded in this project.")
                else:
                    tamper_score += 25.0
                    reasons.append(f"Reused evidence file detected (exact match with Evidence #{ex.id} in Project #{ex.project_id}).")

            # 2. Perceptual Hash near-duplicate (visually identical or re-scaled)
            if p_hash:
                all_phash_ev = db_session.query(ProjectEvidence).filter(
                    ProjectEvidence.p_hash.isnot(None),
                    ProjectEvidence.sha256_hash != sha256_hash
                ).all()
                for ex in all_phash_ev:
                    dist = hamming_distance(p_hash, ex.p_hash)
                    if dist <= 5: # High visual similarity threshold
                        if ex.project_id == project_id:
                            tamper_score += 15.0
                            reasons.append(f"Visually nearly identical evidence photo uploaded multiple times in this project (matches Evidence #{ex.id}).")
                        else:
                            tamper_score += 25.0
                            reasons.append(f"Potential reused visual evidence detected across projects (visually matches Evidence #{ex.id} in Project #{ex.project_id}).")

        # Identity cross-validation if OCR readable and ngo_profile provided
        if ngo_profile and ocr_text:
            extracted_names = DocumentTamperEngine.extract_organization_names(ocr_text)
            norm_profile_org = DocumentTamperEngine.normalize_organization_name(ngo_profile.org_name or "")
            if extracted_names and norm_profile_org:
                name_match = any(
                    norm_profile_org in name or name in norm_profile_org
                    for name in extracted_names
                )
                if not name_match:
                    for name in extracted_names:
                        if len(name) >= 5 and name != norm_profile_org:
                            tamper_score += 35.0
                            reasons.append(f"Document identity mismatch: Extracted Organization Name '{name}' conflicts with NGO Profile '{ngo_profile.org_name}'.")
                            break

        tamper_score = min(100.0, max(0.0, tamper_score))

        if tamper_score >= 70.0:
            status = "REJECTED"
            level = "HIGH"
        elif tamper_score >= 30.0:
            status = "NEEDS_ADMIN_REVIEW"
            level = "MEDIUM"
        else:
            status = "VERIFIED"
            level = "LOW"

        return {
            "sha256_hash": sha256_hash,
            "p_hash": p_hash,
            "mime_type": mime_type,
            "file_size": len(file_bytes),
            "image_width": image_width,
            "image_height": image_height,
            "ocr_text": ocr_text,
            "exif_metadata": json.dumps({"findings": meta_findings, "dimensions": [image_width, image_height] if image_width else None}),
            "tamper_risk_score": tamper_score,
            "tamper_risk_level": level,
            "verification_status": status,
            "evidence_findings": json.dumps(reasons)
        }




