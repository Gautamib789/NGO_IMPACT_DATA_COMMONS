import sys
import os
import json
import unittest
from io import BytesIO
from unittest.mock import patch

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.services.document_tamper_engine import DocumentTamperEngine
from PIL import Image, ImageDraw

class DummyNGOProfile:
    def __init__(self, org_name="ASHAKIRAN FOUNDATION", registration_number="REG-2024-001", pan="DEMOP1234X"):
        self.org_name = org_name
        self.registration_number = registration_number
        self.pan = pan
        self.tax_id = pan

class TestOCRDocumentVerificationSystem(unittest.TestCase):

    def create_test_image(self, text_lines, filename="test_doc.png"):
        img = Image.new('RGB', (400, 300), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        y = 15
        for line in text_lines:
            d.text((15, y), line, fill=(0, 0, 0))
            y += 25
        scaled = img.resize((1600, 1200), Image.Resampling.NEAREST)
        buf = BytesIO()
        scaled.save(buf, format='PNG')
        return buf.getvalue()

    def test_scenario_1_valid_unaltered_document(self):
        """TEST 1: Correct certificate for authenticated NGO (VERIFIED, LOW risk)"""
        profile = DummyNGOProfile(org_name="ASHAKIRAN FOUNDATION", registration_number="REG-2024-001", pan="DEMOP1234X")
        text_lines = [
            "CERTIFICATE OF REGISTRATION",
            "Organization Name: ASHAKIRAN FOUNDATION",
            "Registration Number: REG-2024-001",
            "PAN / Tax ID: DEMOP1234X",
            "Issued by Government Authority"
        ]
        img_bytes = self.create_test_image(text_lines)

        with patch.object(DocumentTamperEngine, 'extract_ocr_text', return_value=" ".join(text_lines)):
            result = DocumentTamperEngine.analyze_document(
                file_bytes=img_bytes,
                filename="certificate.png",
                document_type="12A_REGISTRATION",
                ngo_profile=profile
            )
            exif = json.loads(result["exif_metadata"])
            org_check = exif["identity_checks"]["organization_name"]
            reg_check = exif["identity_checks"]["registration_number"]
            pan_check = exif["identity_checks"]["pan"]

            self.assertEqual(org_check["validation_state"], "DETECTED_MATCH")
            self.assertEqual(reg_check["validation_state"], "DETECTED_MATCH")
            self.assertEqual(pan_check["validation_state"], "DETECTED_MATCH")
            self.assertLess(result["tamper_risk_score"], 30.0)
            self.assertEqual(result["verification_status"], "VERIFIED")

    def test_scenario_2_certificate_from_another_ngo(self):
        """TEST 2: Certificate from another NGO (Never VERIFIED)"""
        profile = DummyNGOProfile(org_name="ASHAKIRAN FOUNDATION", registration_number="REG-2024-001", pan="DEMOP1234X")
        text_lines = [
            "CERTIFICATE OF REGISTRATION",
            "Organization Name: ABC FOUNDATION",
            "Registration Number: REG-2024-001",
            "PAN / Tax ID: DEMOP1234X"
        ]
        img_bytes = self.create_test_image(text_lines)

        with patch.object(DocumentTamperEngine, 'extract_ocr_text', return_value=" ".join(text_lines)):
            result = DocumentTamperEngine.analyze_document(
                file_bytes=img_bytes,
                filename="abc_cert.png",
                document_type="12A_REGISTRATION",
                ngo_profile=profile
            )
            self.assertNotEqual(result["verification_status"], "VERIFIED")
            self.assertIn(result["verification_status"], ["NEEDS_ADMIN_REVIEW", "REJECTED"])

    def test_scenario_3_another_ngo_all_mismatches(self):
        """TEST 3: Another NGO certificate with wrong Org + Reg + PAN (REJECTED, HIGH risk >= 70%)"""
        profile = DummyNGOProfile(org_name="ASHAKIRAN FOUNDATION", registration_number="REG-2024-001", pan="DEMOP1234X")
        text_lines = [
            "CERTIFICATE OF REGISTRATION",
            "Organization Name: ABC FOUNDATION",
            "Registration Number: REG-8888",
            "PAN / Tax ID: ABCDE1234F"
        ]
        img_bytes = self.create_test_image(text_lines)

        with patch.object(DocumentTamperEngine, 'extract_ocr_text', return_value=" ".join(text_lines)):
            result = DocumentTamperEngine.analyze_document(
                file_bytes=img_bytes,
                filename="other_ngo_full.png",
                document_type="12A_REGISTRATION",
                ngo_profile=profile
            )
            exif = json.loads(result["exif_metadata"])
            self.assertEqual(exif["identity_checks"]["organization_name"]["validation_state"], "DETECTED_MISMATCH")
            self.assertEqual(exif["identity_checks"]["registration_number"]["validation_state"], "DETECTED_MISMATCH")
            self.assertEqual(exif["identity_checks"]["pan"]["validation_state"], "DETECTED_MISMATCH")

            self.assertEqual(result["verification_status"], "REJECTED")
            self.assertEqual(result["tamper_risk_level"], "HIGH")
            self.assertGreaterEqual(result["tamper_risk_score"], 70.0)

    def test_scenario_4_unreadable_field_ocr(self):
        """TEST 4: Correct certificate but OCR cannot detect one field (NOT_DETECTED, do not auto reject)"""
        profile = DummyNGOProfile(org_name="ASHAKIRAN FOUNDATION", registration_number="REG-2024-001", pan="DEMOP1234X")
        text_lines = [
            "CERTIFICATE OF REGISTRATION",
            "Organization Name: ASHAKIRAN FOUNDATION",
            "PAN / Tax ID: DEMOP1234X"
        ]
        img_bytes = self.create_test_image(text_lines)

        with patch.object(DocumentTamperEngine, 'extract_ocr_text', return_value=" ".join(text_lines)):
            result = DocumentTamperEngine.analyze_document(
                file_bytes=img_bytes,
                filename="missing_reg.png",
                document_type="12A_REGISTRATION",
                ngo_profile=profile
            )
            exif = json.loads(result["exif_metadata"])
            self.assertEqual(exif["identity_checks"]["registration_number"]["validation_state"], "NOT_DETECTED")
            self.assertEqual(exif["identity_checks"]["organization_name"]["validation_state"], "DETECTED_MATCH")

    def test_scenario_5_minor_visual_difference(self):
        """TEST 5: Correct certificate with minor visual difference"""
        profile = DummyNGOProfile(org_name="ASHAKIRAN FOUNDATION", registration_number="REG-2024-001", pan="DEMOP1234X")
        ref_bytes = self.create_test_image(["ASHAKIRAN FOUNDATION", "REG-2024-001", "DEMOP1234X"])
        img_bytes = self.create_test_image(["ASHAKIRAN FOUNDATION", "REG-2024-001", "DEMOP1234X", "STAMP"])

        with patch.object(DocumentTamperEngine, 'extract_ocr_text', return_value="ASHAKIRAN FOUNDATION REG-2024-001 DEMOP1234X"):
            result = DocumentTamperEngine.analyze_document(
                file_bytes=img_bytes,
                filename="minor_diff.png",
                document_type="12A_REGISTRATION",
                ngo_profile=profile,
                reference_bytes=ref_bytes
            )
            self.assertIn(result["verification_status"], ["VERIFIED", "NEEDS_ADMIN_REVIEW"])

    def test_scenario_6_modified_registration_number(self):
        """TEST 6: Modified certificate with wrong registration (Never VERIFIED)"""
        profile = DummyNGOProfile(org_name="ASHAKIRAN FOUNDATION", registration_number="REG-2024-001", pan="DEMOP1234X")
        text_lines = [
            "Organization Name: ASHAKIRAN FOUNDATION",
            "Registration Number: REG-9999-999",
            "PAN: DEMOP1234X"
        ]
        img_bytes = self.create_test_image(text_lines)

        with patch.object(DocumentTamperEngine, 'extract_ocr_text', return_value=" ".join(text_lines)):
            result = DocumentTamperEngine.analyze_document(
                file_bytes=img_bytes,
                filename="reg_modified.png",
                document_type="12A_REGISTRATION",
                ngo_profile=profile
            )
            self.assertNotEqual(result["verification_status"], "VERIFIED")
            self.assertIn(result["verification_status"], ["NEEDS_ADMIN_REVIEW", "REJECTED"])

    def test_scenario_7_modified_pan(self):
        """TEST 7: Modified certificate with wrong PAN (Never VERIFIED)"""
        profile = DummyNGOProfile(org_name="ASHAKIRAN FOUNDATION", registration_number="REG-2024-001", pan="DEMOP1234X")
        text_lines = [
            "Organization Name: ASHAKIRAN FOUNDATION",
            "Registration Number: REG-2024-001",
            "PAN: ABCDE1234F"
        ]
        img_bytes = self.create_test_image(text_lines)

        with patch.object(DocumentTamperEngine, 'extract_ocr_text', return_value=" ".join(text_lines)):
            result = DocumentTamperEngine.analyze_document(
                file_bytes=img_bytes,
                filename="pan_modified.png",
                document_type="PAN_CARD",
                ngo_profile=profile
            )
            self.assertNotEqual(result["verification_status"], "VERIFIED")

    def test_scenario_8_corrupted_image(self):
        """TEST 8: Corrupted image stream (HIGH risk, REJECTED or ADMIN REVIEW)"""
        corrupt_bytes = b"CORRUPT_PNG_HEADER_DATA_12345"
        result = DocumentTamperEngine.analyze_document(
            file_bytes=corrupt_bytes,
            filename="corrupt.png",
            document_type="12A_REGISTRATION",
            ngo_profile=DummyNGOProfile()
        )
        self.assertGreaterEqual(result["tamper_risk_score"], 30.0)
        self.assertIn(result["verification_status"], ["NEEDS_ADMIN_REVIEW", "REJECTED"])

    def test_scenario_9_screenshot_of_correct_certificate(self):
        """TEST 9: Screenshot of correct certificate (Not auto rejected if identity matches)"""
        profile = DummyNGOProfile(org_name="ASHAKIRAN FOUNDATION", registration_number="REG-2024-001", pan="DEMOP1234X")
        text_lines = [
            "ASHAKIRAN FOUNDATION",
            "REG-2024-001",
            "DEMOP1234X"
        ]
        img_bytes = self.create_test_image(text_lines)

        with patch.object(DocumentTamperEngine, 'extract_ocr_text', return_value=" ".join(text_lines)):
            result = DocumentTamperEngine.analyze_document(
                file_bytes=img_bytes,
                filename="screenshot.png",
                document_type="12A_REGISTRATION",
                ngo_profile=profile
            )
            self.assertEqual(result["verification_status"], "VERIFIED")

    def test_scenario_10_ngo_b_uploads_own_valid_certificate(self):
        """TEST 10: NGO B uploads a valid certificate belonging to NGO B (VERIFIED against NGO B)"""
        ngo_b_profile = DummyNGOProfile(org_name="SMILE FOUNDATION", registration_number="REG-7777", pan="SMILE1234Y")
        text_lines = [
            "Organization Name: SMILE FOUNDATION",
            "Registration Number: REG-7777",
            "PAN: SMILE1234Y"
        ]
        img_bytes = self.create_test_image(text_lines)

        with patch.object(DocumentTamperEngine, 'extract_ocr_text', return_value=" ".join(text_lines)):
            result = DocumentTamperEngine.analyze_document(
                file_bytes=img_bytes,
                filename="ngo_b_cert.png",
                document_type="12A_REGISTRATION",
                ngo_profile=ngo_b_profile
            )
            self.assertEqual(result["verification_status"], "VERIFIED")

    def test_scenario_11_ngo_a_attempts_to_upload_ngo_b_certificate(self):
        """TEST 11: NGO A attempts to upload NGO B's certificate (Identity mismatch, Never VERIFIED)"""
        ngo_a_profile = DummyNGOProfile(org_name="ASHAKIRAN FOUNDATION", registration_number="REG-2024-001", pan="DEMOP1234X")
        ngo_b_lines = [
            "Organization Name: SMILE FOUNDATION",
            "Registration Number: REG-7777",
            "PAN: SMILE1234Y"
        ]
        img_bytes = self.create_test_image(ngo_b_lines)

        with patch.object(DocumentTamperEngine, 'extract_ocr_text', return_value=" ".join(ngo_b_lines)):
            result = DocumentTamperEngine.analyze_document(
                file_bytes=img_bytes,
                filename="ngo_b_uploaded_by_ngo_a.png",
                document_type="12A_REGISTRATION",
                ngo_profile=ngo_a_profile
            )
            self.assertNotEqual(result["verification_status"], "VERIFIED")
            self.assertEqual(result["verification_status"], "REJECTED")

    def test_scenario_12_different_document_types_applicability(self):
        """TEST 12: Different document types (Only applicable identity fields validated)"""
        profile = DummyNGOProfile(org_name="ASHAKIRAN FOUNDATION", registration_number="REG-2024-001", pan="DEMOP1234X")
        text_lines = [
            "INCOME TAX DEPARTMENT",
            "PAN CARD",
            "PAN: DEMOP1234X"
        ]
        img_bytes = self.create_test_image(text_lines)

        with patch.object(DocumentTamperEngine, 'extract_ocr_text', return_value=" ".join(text_lines)):
            result = DocumentTamperEngine.analyze_document(
                file_bytes=img_bytes,
                filename="pan_card.png",
                document_type="PAN_CARD",
                ngo_profile=profile
            )
            exif = json.loads(result["exif_metadata"])
            self.assertEqual(exif["identity_checks"]["registration_number"]["validation_state"], "NOT_APPLICABLE")
            self.assertEqual(exif["identity_checks"]["pan"]["validation_state"], "DETECTED_MATCH")

if __name__ == "__main__":
    unittest.main()
