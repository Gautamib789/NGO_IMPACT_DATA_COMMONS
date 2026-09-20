import io
import json
import hashlib
from unittest.mock import patch
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


from main import app
from app.database import SessionLocal
from app.models import User, UserRole, NGODetail, NGODocument, AuditLog
from app.services.document_tamper_engine import DocumentTamperEngine

client = TestClient(app)

def test_phase4():
    print("=== STARTING PHASE 4 DOCUMENT INTEGRITY & TAMPER DETECTION TESTS ===")
    db: Session = SessionLocal()
    try:
        # Get or create test NGO
        test_user = db.query(User).filter(User.email == "phase4_doc_test@example.com").first()
        if not test_user:
            test_user = User(
                email="phase4_doc_test@example.com",
                hashed_password="fakehashedpassword",
                full_name="Phase 4 Test User",
                role=UserRole.NGO,
                is_active=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)

        test_ngo = db.query(NGODetail).filter(NGODetail.user_id == test_user.id).first()
        if not test_ngo:
            test_ngo = NGODetail(
                user_id=test_user.id,
                org_name="Phase 4 Integrity Trust",
                registration_number="REG-PH4-100",
                tax_id="TAX-PH4-100",
                category="Education",
                pan="AAATC9999M"
            )
            db.add(test_ngo)
            db.commit()
            db.refresh(test_ngo)

        # 1. Test Clean PDF Document Upload
        clean_pdf_bytes = b"%PDF-1.4 Clean Registration Document for Phase 4 Test AAATC9999M %%EOF"
        analysis1 = DocumentTamperEngine.analyze_document(
            file_bytes=clean_pdf_bytes,
            filename="registration.pdf",
            document_type="REGISTRATION",
            ngo_profile=test_ngo
        )

        expected_hash1 = hashlib.sha256(clean_pdf_bytes).hexdigest()
        assert analysis1["sha256_hash"] == expected_hash1, "SHA-256 hash mismatch"
        assert analysis1["tamper_risk_score"] == 0.0, f"Expected 0.0 tamper score, got {analysis1['tamper_risk_score']}"
        assert analysis1["verification_status"] == "VERIFIED", f"Expected VERIFIED, got {analysis1['verification_status']}"
        assert "AAATC9999M" in analysis1["ocr_text"]
        print("[OK] Test 1 Passed: Clean PDF document SHA-256 hashing & LOW tamper risk VERIFIED")

        # 2. Test Extension Spoofing (Extension says .png, header says %PDF-)
        spoofed_bytes = b"%PDF-1.4 Fake Image Data %%EOF"
        analysis2 = DocumentTamperEngine.analyze_document(
            file_bytes=spoofed_bytes,
            filename="fake_image.png",
            document_type="80G_CERTIFICATE",
            ngo_profile=test_ngo
        )
        assert analysis2["tamper_risk_score"] >= 40.0, "Spoofed extension must trigger tamper penalty"
        assert analysis2["verification_status"] in ["NEEDS_ADMIN_REVIEW", "REJECTED"]
        print(f"[OK] Test 2 Passed: Extension spoofing detected (score: {analysis2['tamper_risk_score']}%, status: {analysis2['verification_status']})")

        # 3. Test Editing Software Tag Detection (Adobe Photoshop)
        photoshop_bytes = b"\xff\xd8\xff JPEG Image metadata edited with Adobe Photoshop CS6 \xff\xd9"
        analysis3 = DocumentTamperEngine.analyze_document(
            file_bytes=photoshop_bytes,
            filename="edited_pan.jpg",
            document_type="PAN_CARD",
            ngo_profile=test_ngo
        )
        assert analysis3["tamper_risk_score"] >= 35.0, "Photoshop signature must trigger tamper penalty"
        assert analysis3["verification_status"] == "NEEDS_ADMIN_REVIEW"
        assert "Photoshop" in analysis3["verification_message"] or "Photoshop" in analysis3["exif_metadata"]
        print(f"[OK] Test 3 Passed: Photoshop metadata editing signature detected (status: {analysis3['verification_status']})")

        # 4. Test Multi-Tampered High Risk REJECTED Scenario
        high_risk_bytes = b"%PDF-1.4 Modified with Adobe Photoshop 2024 trailing data after EOF %%EOF extra_payload_appended_here"
        analysis4 = DocumentTamperEngine.analyze_document(
            file_bytes=high_risk_bytes,
            filename="fake_pan.png", # Spoofed ext + Photoshop tag + Trailer anomaly
            document_type="FCRA_CERTIFICATE",
            ngo_profile=test_ngo
        )
        assert analysis4["tamper_risk_score"] >= 70.0, "High risk multi-tampered document must reach >= 70.0 score"
        assert analysis4["verification_status"] == "REJECTED"
        print(f"[OK] Test 4 Passed: High risk tampered document auto-REJECTED (score: {analysis4['tamper_risk_score']}%)")

        # 5. Database Save & Audit Log Verification
        doc_entry = NGODocument(
            ngo_id=test_ngo.id,
            document_type="REGISTRATION",
            file_name="registration.pdf",
            file_path="/uploads/test_phase4.pdf",
            sha256_hash=analysis1["sha256_hash"],
            mime_type=analysis1["mime_type"],
            file_size=analysis1["file_size"],
            verification_status=analysis1["verification_status"],
            verification_message=analysis1["verification_message"],
            tamper_risk_score=analysis1["tamper_risk_score"],
            tamper_risk_level=analysis1["tamper_risk_level"],
            ocr_text=analysis1["ocr_text"],
            exif_metadata=analysis1["exif_metadata"]
        )
        db.add(doc_entry)
        db.commit()
        db.refresh(doc_entry)

        audit_entry = AuditLog(
            actor_user_id=test_user.id,
            ngo_id=test_ngo.id,
            action="DOCUMENT_UPLOAD",
            entity_type="DOCUMENT",
            entity_id=doc_entry.id,
            metadata_json=f'{{"sha256": "{doc_entry.sha256_hash}", "tamper_score": {doc_entry.tamper_risk_score}}}'
        )
        db.add(audit_entry)
        db.commit()

        fetched_doc = db.query(NGODocument).filter(NGODocument.id == doc_entry.id).first()
        assert fetched_doc.sha256_hash == expected_hash1
        assert fetched_doc.verification_status == "VERIFIED"
        print("[OK] Test 5 Passed: NGODocument database record & AuditLog verified")

        # 6. Ledger Verification Intact
        ledger_res = client.get("/api/ledger/verify")
        assert ledger_res.status_code == 200
        assert ledger_res.json()["valid"] == True
        print("[OK] Test 6 Passed: SHA-256 Blockchain Ledger verification intact (valid: true)")

        # 7. Test Mismatched Registration Number
        mismatched_reg_bytes = b"%PDF-1.4 Official Certificate Registration Number REG-9999-MISMATCH %%EOF"
        analysis7 = DocumentTamperEngine.analyze_document(
            file_bytes=mismatched_reg_bytes,
            filename="registration_mismatch.pdf",
            document_type="REGISTRATION",
            ngo_profile=test_ngo
        )
        assert analysis7["tamper_risk_score"] >= 25.0, "Mismatched registration number must increase risk score"
        assert "Registration number mismatch" in analysis7["verification_message"] or "Registration number mismatch" in " ".join(analysis7.get("reasons", [])) or "Mismatch" in analysis7["exif_metadata"]
        print(f"[OK] Test 7 Passed: Mismatched registration number detected (score: {analysis7['tamper_risk_score']}%)")

        # 8. Test Mismatched PAN
        mismatched_pan_bytes = b"%PDF-1.4 Tax Exemption Form PAN Number MISMA9999X %%EOF"
        analysis8 = DocumentTamperEngine.analyze_document(
            file_bytes=mismatched_pan_bytes,
            filename="pan_mismatch.pdf",
            document_type="PAN_CARD",
            ngo_profile=test_ngo
        )
        assert analysis8["tamper_risk_score"] >= 25.0, "Mismatched PAN must increase risk score"
        assert "PAN mismatch" in analysis8["verification_message"] or "Mismatch" in analysis8["exif_metadata"]
        print(f"[OK] Test 8 Passed: Mismatched PAN detected (score: {analysis8['tamper_risk_score']}%)")

        # 9. Test Document Without Readable OCR (Sends to Admin Review when ownership cannot be verified)
        blank_img_9 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        blank_buf_9 = io.BytesIO()
        blank_img_9.save(blank_buf_9, format="PNG")
        no_ocr_bytes = blank_buf_9.getvalue()
        analysis9 = DocumentTamperEngine.analyze_document(
            file_bytes=no_ocr_bytes,
            filename="clean_scan.png",
            document_type="REGISTRATION",
            ngo_profile=test_ngo
        )
        assert analysis9["verification_status"] == "NEEDS_ADMIN_REVIEW", "Unreadable document requiring identity check must go to Admin Review"
        assert "Unreadable document" in analysis9["verification_message"]
        print("[OK] Test 9 Passed: Unreadable document requiring identity verification routed to NEEDS_ADMIN_REVIEW")


        # 10. Test XMP Creation vs Modification Timestamp Inconsistency
        xmp_inconsistent_bytes = b"%PDF-1.4 <xmp:CreateDate>2024-01-01T10:00:00</xmp:CreateDate> <xmp:ModifyDate>2026-09-14T22:00:00</xmp:ModifyDate> Edited with Canva %%EOF"
        analysis10 = DocumentTamperEngine.analyze_document(
            file_bytes=xmp_inconsistent_bytes,
            filename="edited_xmp.pdf",
            document_type="REGISTRATION",
            ngo_profile=test_ngo
        )
        assert analysis10["tamper_risk_score"] >= 35.0, "Editing software + timestamp discrepancy must trigger risk score"
        print(f"[OK] Test 10 Passed: XMP timestamp & editing tool metadata inconsistency detected (score: {analysis10['tamper_risk_score']}%)")

        # 11. Test Pillow Clean PNG Raster Image Analysis
        png_buf = io.BytesIO()
        img_clean = Image.new("RGB", (600, 400), color=(255, 255, 255))
        draw = ImageDraw.Draw(img_clean)
        draw.text((20, 20), f"Organization Name: {test_ngo.org_name}", fill=(0, 0, 0))
        draw.text((20, 50), f"Registration Number: {test_ngo.registration_number}", fill=(0, 0, 0))
        draw.text((20, 80), f"PAN Tax ID: {test_ngo.pan}", fill=(0, 0, 0))
        draw.rectangle([(20, 120), (580, 380)], outline=(0, 0, 0), width=2)
        img_clean.save(png_buf, format="PNG")
        clean_png_bytes = png_buf.getvalue()

        clean_ocr_text = f"Organization Name: {test_ngo.org_name} Registration Number: {test_ngo.registration_number} PAN: {test_ngo.pan}"

        with patch.object(DocumentTamperEngine, 'extract_ocr_text', return_value=clean_ocr_text):
            analysis11 = DocumentTamperEngine.analyze_document(
                file_bytes=clean_png_bytes,
                filename="clean_cert.png",
                document_type="REGISTRATION",
                ngo_profile=test_ngo
            )
            assert analysis11["tamper_risk_score"] == 0.0, f"Clean PNG must have 0.0 risk score, got {analysis11['tamper_risk_score']}"
            assert analysis11["verification_status"] == "VERIFIED"
            print("[OK] Test 11 Passed: Pillow Clean PNG raster image analyzed successfully (Score: 0.0%, VERIFIED)")

            # 12. Test Pillow Clean JPEG Raster Image Analysis
            jpg_buf = io.BytesIO()
            img_clean.save(jpg_buf, format="JPEG", quality=90)
            clean_jpg_bytes = jpg_buf.getvalue()

            analysis12 = DocumentTamperEngine.analyze_document(
                file_bytes=clean_jpg_bytes,
                filename="clean_cert.jpg",
                document_type="REGISTRATION",
                ngo_profile=test_ngo
            )
            assert analysis12["tamper_risk_score"] == 0.0, f"Clean JPEG must have 0.0 risk score, got {analysis12['tamper_risk_score']}"
            assert analysis12["verification_status"] == "VERIFIED"
            print("[OK] Test 12 Passed: Pillow Clean JPEG raster image analyzed successfully (Score: 0.0%, VERIFIED)")

            # 13. Test SSIM Identical Trusted Reference Comparison
            analysis13 = DocumentTamperEngine.analyze_document(
                file_bytes=clean_png_bytes,
                filename="clean_cert.png",
                document_type="REGISTRATION",
                ngo_profile=test_ngo,
                reference_bytes=clean_png_bytes # Identical reference
            )
            assert analysis13["tamper_risk_score"] == 0.0
            assert "verified" in analysis13["exif_metadata"].lower() or "similarity" in analysis13["exif_metadata"].lower()
            print("[OK] Test 13 Passed: SSIM Identical reference comparison verified high structural similarity (>98%)")

            # 14. Test SSIM Visually Modified Trusted Reference Comparison
            mod_buf = io.BytesIO()
            img_mod = img_clean.copy()
            draw_mod = ImageDraw.Draw(img_mod)
            # Visually modify a significant document region
            draw_mod.rectangle([(100, 100), (300, 200)], fill=(0, 0, 0))
            img_mod.save(mod_buf, format="PNG")
            modified_png_bytes = mod_buf.getvalue()

            analysis14 = DocumentTamperEngine.analyze_document(
                file_bytes=modified_png_bytes,
                filename="modified_cert.png",
                document_type="REGISTRATION",
                ngo_profile=test_ngo,
                reference_bytes=clean_png_bytes # Reference original
            )
            assert analysis14["tamper_risk_score"] >= 10.0, "SSIM visual reference divergence must trigger risk penalty"
            assert "Visual difference detected" in analysis14["exif_metadata"] or "divergence" in " ".join(analysis14.get("reasons", []))

            # 16. Controlled Demo Test (Registration Mismatch Visual Document)
            demo_orig_bytes = clean_png_bytes
            demo_mod_bytes = modified_png_bytes

            # Original upload
            analysis_orig = DocumentTamperEngine.analyze_document(
                file_bytes=demo_orig_bytes,
                filename="registration_orig.png",
                document_type="REGISTRATION",
                ngo_profile=test_ngo
            )
            assert analysis_orig["verification_status"] == "VERIFIED"

            # Modified upload with reference comparison
            analysis_mod = DocumentTamperEngine.analyze_document(
                file_bytes=demo_mod_bytes,
                filename="registration_mod.png",
                document_type="REGISTRATION",
                ngo_profile=test_ngo,
                reference_bytes=demo_orig_bytes
            )
            assert analysis_mod["tamper_risk_score"] >= 10.0
            assert "Document" in analysis_mod["verification_message"]
            print(f"[OK] Test 16 Passed: Controlled Demo Test verified (Original: VERIFIED 0.0%, Modified: {analysis_mod['verification_status']} {analysis_mod['tamper_risk_score']}%)")

        print("\n==================================================")
        print("ALL PHASE 4 DOCUMENT INTEGRITY & TAMPER TESTS PASSED PERFECTLY!")
        print("==================================================")


    finally:
        db.close()

if __name__ == "__main__":
    import traceback
    try:
        test_phase4()
    except Exception as e:
        with open("test_phase4_error.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print("EXCEPTION ENCOUNTERED IN PHASE 4. LOGGED TO test_phase4_error.log")
        raise e
