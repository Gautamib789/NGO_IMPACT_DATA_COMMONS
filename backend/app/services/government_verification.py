import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.ngo import NGODetail
from app.models.government import GovernmentRegistry
from app.models.audit import AuditLog

DEMO_REGISTRY_DISCLAIMER = "SIMULATED DEMO GOVERNMENT REGISTRY (FOR ACADEMIC / PROJECT DEMONSTRATION ONLY)"

DEMO_SEED_DATA = [
    {
        "registration_number": "REG-2024-001",
        "org_name": "Green Earth Foundation",
        "pan": "AAATG1234F",
        "eighty_g_info": "80G-VALID-2024",
        "fcra_info": "FCRA-VALID-2024",
        "gst_number": "29AAATG1234F1Z5",
        "organization_type": "Trust",
        "status": "ACTIVE",
        "registered_state": "Karnataka",
        "registered_district": "Bengaluru Urban"
    },
    {
        "registration_number": "REG-2024-002",
        "org_name": "Hope Care International",
        "pan": "AAATH5678K",
        "eighty_g_info": "80G-EXPIRED-2022",
        "fcra_info": "FCRA-SUSPENDED",
        "gst_number": "27AAATH5678K1Z2",
        "organization_type": "Society",
        "status": "ACTIVE",
        "registered_state": "Maharashtra",
        "registered_district": "Mumbai"
    },
    {
        "registration_number": "REG-2024-003",
        "org_name": "Rural Education Upliftment Trust",
        "pan": "AAATR9999P",
        "eighty_g_info": "80G-VALID-2025",
        "fcra_info": "NOT_APPLICABLE",
        "gst_number": "33AAATR9999P1Z9",
        "organization_type": "Trust",
        "status": "INACTIVE",
        "registered_state": "Tamil Nadu",
        "registered_district": "Chennai"
    },
    {
        "registration_number": "REG-2024-004",
        "org_name": "Child Welfare Action Network",
        "pan": "AAATC4321M",
        "eighty_g_info": "80G-VALID-2026",
        "fcra_info": "FCRA-VALID-2026",
        "gst_number": "07AAATC4321M1Z1",
        "organization_type": "Section 8 Company",
        "status": "ACTIVE",
        "registered_state": "Delhi",
        "registered_district": "New Delhi"
    }
]


class GovernmentVerificationService:

    @staticmethod
    def seed_demo_registry(db: Session) -> int:
        """
        Populates the GovernmentRegistry table with realistic fictional test records.
        Ensures missing demo seed records are added. Returns total count of records.
        """
        seeded_new = 0
        for data in DEMO_SEED_DATA:
            existing = db.query(GovernmentRegistry).filter(
                GovernmentRegistry.registration_number == data["registration_number"]
            ).first()
            if not existing:
                reg_entry = GovernmentRegistry(
                    registration_number=data["registration_number"],
                    org_name=data["org_name"],
                    pan=data["pan"],
                    eighty_g_info=data["eighty_g_info"],
                    fcra_info=data["fcra_info"],
                    gst_number=data["gst_number"],
                    organization_type=data["organization_type"],
                    status=data["status"],
                    registered_state=data["registered_state"],
                    registered_district=data["registered_district"]
                )
                db.add(reg_entry)
                seeded_new += 1
        
        if seeded_new > 0:
            db.commit()
            
        return db.query(GovernmentRegistry).count()

    @staticmethod
    def verify_ngo(db: Session, ngo: NGODetail) -> Dict[str, Any]:
        """
        Compares NGO fields against the simulated GovernmentRegistry.
        Computes match score, field breakdowns, updates verification status,
        and logs the audit event.
        """
        # Ensure demo registry has data
        GovernmentVerificationService.seed_demo_registry(db)

        # Lookup by registration number (normalized)
        reg_num = (ngo.registration_number or "").strip()
        gov_record = db.query(GovernmentRegistry).filter(
            GovernmentRegistry.registration_number == reg_num
        ).first()

        now = datetime.utcnow()

        if not gov_record:
            ngo.government_verification_status = "NOT_VERIFIED"
            db.commit()

            result = {
                "disclaimer": DEMO_REGISTRY_DISCLAIMER,
                "verified_at": now.isoformat(),
                "registration_number": reg_num,
                "verification_status": "NOT_VERIFIED",
                "government_match_score": 0.0,
                "matched_registry_org_name": None,
                "matched_registry_state": None,
                "field_matches": {
                    "registration_number": False,
                    "org_name": False,
                    "pan": False,
                    "eighty_g_info": False,
                    "fcra_info": False,
                    "gst_number": False
                },
                "verification_notes": f"No record found in Simulated Demo Government Registry for Registration Number '{reg_num}'."
            }

            # Create Audit Log
            audit = AuditLog(
                actor_user_id=ngo.user_id,
                ngo_id=ngo.id,
                action="GOVERNMENT_VERIFICATION",
                entity_type="NGO",
                entity_id=ngo.id,
                metadata_json=json.dumps(result)
            )
            db.add(audit)
            db.commit()
            return result

        # Check if record in government database is INACTIVE / SUSPENDED
        if gov_record.status.upper() in ["INACTIVE", "SUSPENDED"]:
            ngo.government_verification_status = "INACTIVE"
            db.commit()

            result = {
                "disclaimer": DEMO_REGISTRY_DISCLAIMER,
                "verified_at": now.isoformat(),
                "registration_number": reg_num,
                "verification_status": "INACTIVE",
                "government_match_score": 0.0,
                "matched_registry_org_name": gov_record.org_name,
                "matched_registry_state": gov_record.registered_state,
                "field_matches": {
                    "registration_number": True,
                    "org_name": False,
                    "pan": False,
                    "eighty_g_info": False,
                    "fcra_info": False,
                    "gst_number": False
                },
                "verification_notes": f"Registry match found ('{gov_record.org_name}'), but registration is marked as {gov_record.status.upper()} in government records."
            }

            audit = AuditLog(
                actor_user_id=ngo.user_id,
                ngo_id=ngo.id,
                action="GOVERNMENT_VERIFICATION",
                entity_type="NGO",
                entity_id=ngo.id,
                metadata_json=json.dumps(result)
            )
            db.add(audit)
            db.commit()
            return result

        # Field matching logic & score calculation
        def norm(val: Optional[str]) -> str:
            return (val or "").strip().lower()

        reg_match = norm(ngo.registration_number) == norm(gov_record.registration_number)
        
        # Name match: exact or clean substring match
        ngo_name_norm = norm(ngo.org_name)
        gov_name_norm = norm(gov_record.org_name)
        name_match = (ngo_name_norm == gov_name_norm) or (ngo_name_norm in gov_name_norm) or (gov_name_norm in ngo_name_norm)
        
        pan_match = norm(ngo.pan) == norm(gov_record.pan) if (ngo.pan or gov_record.pan) else True
        eighty_g_match = norm(ngo.eighty_g_info) == norm(gov_record.eighty_g_info) if (ngo.eighty_g_info or gov_record.eighty_g_info) else True
        fcra_match = norm(ngo.fcra_info) == norm(gov_record.fcra_info) if (ngo.fcra_info or gov_record.fcra_info) else True
        gst_match = norm(ngo.gst_number) == norm(gov_record.gst_number) if (ngo.gst_number or gov_record.gst_number) else True

        # Weights: Reg (30), Name (30), PAN (15), 80G (10), FCRA (10), GST (5)
        score = 0.0
        if reg_match: score += 30.0
        if name_match: score += 30.0
        if pan_match: score += 15.0
        if eighty_g_match: score += 10.0
        if fcra_match: score += 10.0
        if gst_match: score += 5.0

        if score >= 90.0:
            status = "VERIFIED"
            notes = "All primary government registration details verified successfully against simulated registry."
        elif score >= 50.0:
            status = "PARTIALLY_MATCHED"
            notes = f"Registration number matched, but minor discrepancies detected in name or tax parameters (Match score: {score:.1f}%)."
        else:
            status = "NOT_VERIFIED"
            notes = f"Significant discrepancies found between profile data and registry records (Match score: {score:.1f}%)."

        ngo.government_verification_status = status
        db.commit()

        result = {
            "disclaimer": DEMO_REGISTRY_DISCLAIMER,
            "verified_at": now.isoformat(),
            "registration_number": reg_num,
            "verification_status": status,
            "government_match_score": round(score, 1),
            "matched_registry_org_name": gov_record.org_name,
            "matched_registry_state": gov_record.registered_state,
            "field_matches": {
                "registration_number": reg_match,
                "org_name": name_match,
                "pan": pan_match,
                "eighty_g_info": eighty_g_match,
                "fcra_info": fcra_match,
                "gst_number": gst_match
            },
            "verification_notes": notes
        }

        # Log Audit
        audit = AuditLog(
            actor_user_id=ngo.user_id,
            ngo_id=ngo.id,
            action="GOVERNMENT_VERIFICATION",
            entity_type="NGO",
            entity_id=ngo.id,
            metadata_json=json.dumps(result)
        )
        db.add(audit)
        db.commit()

        return result
