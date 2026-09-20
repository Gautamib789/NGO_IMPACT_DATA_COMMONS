from sqlalchemy.orm import Session
from app.models.ngo import NGODetail
from app.models.fraud import FraudFlag


class FraudDetectionEngine:

    @classmethod
    def scan_ngo(cls, db: Session, ngo_id: int) -> list:
        ngo = db.query(NGODetail).filter(NGODetail.id == ngo_id).first()
        if not ngo:
            return []

        flags_generated = []

        # Rule 1: Expenses significantly exceed donations
        if ngo.total_donations_received > 0 and ngo.total_expenses > (ngo.total_donations_received * 1.25):
            excess_pct = round(((ngo.total_expenses - ngo.total_donations_received) / ngo.total_donations_received) * 100, 1)
            flag = cls._create_flag_if_not_exists(
                db, ngo_id,
                severity="HIGH",
                rule_code="EXPENSE_OVER_DONATIONS",
                description=f"Total expenses (₹{ngo.total_expenses:,.2f}) exceed total received donations (₹{ngo.total_donations_received:,.2f}) by {excess_pct}%."
            )
            if flag:
                flags_generated.append(flag)

        # Rule 2: Document Completeness Gap
        if ngo.doc_completeness_score < 60.0:
            flag = cls._create_flag_if_not_exists(
                db, ngo_id,
                severity="MEDIUM",
                rule_code="DOC_INCOMPLETE",
                description=f"Compliance document completion is low ({ngo.doc_completeness_score:.1f}%). Required audit reports or tax filings are missing."
            )
            if flag:
                flags_generated.append(flag)

        # Rule 3: High Expense with Zero/Low Beneficiaries
        if ngo.total_expenses > 5000 and ngo.beneficiary_count < 5:
            flag = cls._create_flag_if_not_exists(
                db, ngo_id,
                severity="HIGH",
                rule_code="BENEFICIARY_MISMATCH",
                description=f"High expense footprint (₹{ngo.total_expenses:,.2f}) recorded with low beneficiary impact ({ngo.beneficiary_count} reported)."
            )
            if flag:
                flags_generated.append(flag)

        # Rule 4: Duplicate Tax/Reg ID across NGOs
        duplicate_ngo = db.query(NGODetail).filter(
            NGODetail.id != ngo.id,
            (NGODetail.registration_number == ngo.registration_number) | (NGODetail.tax_id == ngo.tax_id)
        ).first()

        if duplicate_ngo:
            flag = cls._create_flag_if_not_exists(
                db, ngo_id,
                severity="CRITICAL",
                rule_code="DUPLICATE_REGISTRATION",
                description=f"Registration or Tax ID matches another existing NGO entity ({duplicate_ngo.org_name})."
            )
            if flag:
                flags_generated.append(flag)

        # Re-evaluate NGO transparency score based on documents & flags
        cls._recalculate_transparency_score(db, ngo)

        return flags_generated

    @classmethod
    def _create_flag_if_not_exists(cls, db: Session, ngo_id: int, severity: str, rule_code: str, description: str):
        existing = db.query(FraudFlag).filter(
            FraudFlag.ngo_id == ngo_id,
            FraudFlag.rule_code == rule_code,
            FraudFlag.status == "OPEN"
        ).first()

        if not existing:
            new_flag = FraudFlag(
                ngo_id=ngo_id,
                severity=severity,
                rule_code=rule_code,
                description=description,
                status="OPEN"
            )
            db.add(new_flag)
            db.commit()
            db.refresh(new_flag)
            return new_flag
        return None

    @classmethod
    def _recalculate_transparency_score(cls, db: Session, ngo: NGODetail):
        # Base score starts with doc completeness weight (60%) + donation activity (40%)
        open_flags = db.query(FraudFlag).filter(
            FraudFlag.ngo_id == ngo.id,
            FraudFlag.status == "OPEN"
        ).all()

        penalty = 0.0
        for f in open_flags:
            if f.severity == "CRITICAL":
                penalty += 40.0
            elif f.severity == "HIGH":
                penalty += 20.0
            elif f.severity == "MEDIUM":
                penalty += 10.0
            elif f.severity == "LOW":
                penalty += 5.0

        activity_score = 40.0 if ngo.total_donations_received > 0 else 20.0
        doc_score = (ngo.doc_completeness_score / 100.0) * 60.0

        computed = doc_score + activity_score - penalty
        ngo.transparency_score = max(0.0, min(100.0, round(computed, 1)))
        db.commit()
