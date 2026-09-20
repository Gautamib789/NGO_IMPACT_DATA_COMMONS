import json
import re
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.project import (
    Project, ProjectEvidence, ProjectExpense, ProjectRiskAnalysis,
    ProjectFinding, AdminNotification
)
from app.models.ngo import NGODetail
from app.services.perceptual_hash import hamming_distance
from app.services.document_tamper_engine import DocumentTamperEngine

class ProjectIntegrityEngine:

    @staticmethod
    def analyze_project(db: Session, project_id: int) -> Dict[str, Any]:
        """
        Runs comprehensive AI risk analysis on a project, including photo tamper detection,
        perceptual hash duplicate checks, financial inconsistency detection, and OCR cross-validation.
        Updates ProjectRiskAnalysis and Project database status.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "Project not found"}

        ngo = db.query(NGODetail).filter(NGODetail.id == project.ngo_id).first()
        evidence_list = db.query(ProjectEvidence).filter(ProjectEvidence.project_id == project_id).all()
        expense_list = db.query(ProjectExpense).filter(ProjectExpense.project_id == project_id).all()

        findings = []
        
        photo_risk = 0.0
        financial_risk = 0.0
        identity_risk = 0.0
        consistency_risk = 0.0
        
        has_identity_mismatch = False

        # ==================================================
        # 1. PHOTOForensics & DUPLICATE / RELATIONSHIP ANALYSIS
        # ==================================================
        before_photos = [e for e in evidence_list if e.evidence_type == "BEFORE_PHOTO"]
        after_photos = [e for e in evidence_list if e.evidence_type == "AFTER_PHOTO"]

        # Check before/after identical photo reuse
        for b_img in before_photos:
            for a_img in after_photos:
                if b_img.sha256_hash == a_img.sha256_hash or (b_img.p_hash and a_img.p_hash and hamming_distance(b_img.p_hash, a_img.p_hash) <= 5):
                    photo_risk += 25.0
                    findings.append({
                        "category": "EVIDENCE_CONSISTENCY",
                        "risk_level": "HIGH",
                        "score_impact": 25.0,
                        "message": f"Identical or visually near-duplicate photo reused as both BEFORE ({b_img.file_name}) and AFTER ({a_img.file_name}) project evidence.",
                        "evidence_id": b_img.id
                    })

        # Process photo evidence findings
        for ev in evidence_list:
            if ev.tamper_risk_score > 0:
                photo_risk += min(20.0, ev.tamper_risk_score * 0.3)
                ev_reasons = []
                if ev.evidence_findings:
                    try:
                        ev_reasons = json.loads(ev.evidence_findings)
                    except Exception:
                        pass
                for r in ev_reasons:
                    findings.append({
                        "category": "PHOTO_TAMPER",
                        "risk_level": ev.tamper_risk_level,
                        "score_impact": 10.0,
                        "message": f"File '{ev.file_name}': {r}",
                        "evidence_id": ev.id
                    })

        # ==================================================
        # 2. FINANCIAL FRAUD & INVOICE CROSS-VALIDATION
        # ==================================================
        total_expenses_recorded = sum(e.amount for e in expense_list)
        
        # A. Budget overrun check
        if project.total_budget > 0 and total_expenses_recorded > project.total_budget:
            overrun = total_expenses_recorded - project.total_budget
            financial_risk += 25.0
            findings.append({
                "category": "FINANCIAL_FRAUD",
                "risk_level": "HIGH",
                "score_impact": 25.0,
                "message": f"Financial discrepancy detected: total expenses (₹{total_expenses_recorded:,.2f}) exceed declared project budget (₹{project.total_budget:,.2f}) by ₹{overrun:,.2f}.",
                "evidence_id": None
            })

        # B. Duplicate invoice numbers check
        inv_numbers = [e.invoice_number.strip().upper() for e in expense_list if e.invoice_number]
        duplicate_invs = set([inv for inv in inv_numbers if inv_numbers.count(inv) > 1])
        if duplicate_invs:
            financial_risk += 20.0
            findings.append({
                "category": "FINANCIAL_FRAUD",
                "risk_level": "MEDIUM",
                "score_impact": 20.0,
                "message": f"Duplicate invoice numbers detected within project expenses: {', '.join(duplicate_invs)}.",
                "evidence_id": None
            })

        # C. Invoice OCR vs Entered Amount Mismatch
        for exp in expense_list:
            if exp.evidence_id:
                ev_doc = next((e for e in evidence_list if e.id == exp.evidence_id), None)
                if ev_doc and ev_doc.ocr_text:
                    # Look for currency numbers in OCR text
                    amounts_found = re.findall(r'₹?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)', ev_doc.ocr_text)
                    parsed_amounts = []
                    for raw_amt in amounts_found:
                        try:
                            val = float(raw_amt.replace(',', ''))
                            if val > 0:
                                parsed_amounts.append(val)
                        except ValueError:
                            pass
                    
                    if parsed_amounts:
                        # Check if entered expense amount matches any parsed amount or differs significantly
                        best_match = min(parsed_amounts, key=lambda x: abs(x - exp.amount))
                        exp.ocr_amount = best_match
                        diff_ratio = abs(best_match - exp.amount) / max(exp.amount, 1.0)
                        if diff_ratio > 0.15 and abs(best_match - exp.amount) >= 100: # >15% difference and >= ₹100
                            exp.is_ocr_matched = False
                            exp.discrepancy_note = f"Entered amount ₹{exp.amount:,.2f} differs from OCR detected amount ₹{best_match:,.2f}."
                            financial_risk += 25.0
                            findings.append({
                                "category": "FINANCIAL_FRAUD",
                                "risk_level": "HIGH",
                                "score_impact": 25.0,
                                "message": f"Invoice OCR discrepancy: Entered expense amount (₹{exp.amount:,.2f}) differs from extracted invoice amount (₹{best_match:,.2f}) for Invoice '{exp.invoice_number or 'Receipt'}'.",
                                "evidence_id": exp.evidence_id
                            })
                        else:
                            exp.is_ocr_matched = True

        # D. Expense date outside project dates
        if project.start_date or project.end_date:
            for exp in expense_list:
                if exp.expense_date:
                    if project.start_date and exp.expense_date < project.start_date:
                        financial_risk += 15.0
                        findings.append({
                            "category": "FINANCIAL_FRAUD",
                            "risk_level": "MEDIUM",
                            "score_impact": 15.0,
                            "message": f"Expense date ({exp.expense_date.strftime('%Y-%m-%d')}) precedes project start date ({project.start_date.strftime('%Y-%m-%d')}).",
                            "evidence_id": exp.evidence_id
                        })
                    elif project.end_date and exp.expense_date > project.end_date:
                        financial_risk += 15.0
                        findings.append({
                            "category": "FINANCIAL_FRAUD",
                            "risk_level": "MEDIUM",
                            "score_impact": 15.0,
                            "message": f"Expense date ({exp.expense_date.strftime('%Y-%m-%d')}) is logged after project end date ({project.end_date.strftime('%Y-%m-%d')}).",
                            "evidence_id": exp.evidence_id
                        })

        # ==================================================
        # 3. IDENTITY & OCR CROSS-VALIDATION
        # ==================================================
        if ngo:
            norm_ngo_org = DocumentTamperEngine.normalize_organization_name(ngo.org_name or "")
            for ev in evidence_list:
                if ev.ocr_text:
                    ocr_orgs = DocumentTamperEngine.extract_organization_names(ev.ocr_text)
                    for o_name in ocr_orgs:
                        if len(o_name) >= 5 and norm_ngo_org and norm_ngo_org not in o_name and o_name not in norm_ngo_org:
                            has_identity_mismatch = True
                            identity_risk += 35.0
                            findings.append({
                                "category": "DOCUMENT_IDENTITY",
                                "risk_level": "HIGH",
                                "score_impact": 35.0,
                                "message": f"Identity conflict: Evidence '{ev.file_name}' contains Organization Name '{o_name}' which conflicts with authenticated NGO '{ngo.org_name}'.",
                                "evidence_id": ev.id
                            })
                            break

        # ==================================================
        # 4. OVERALL RISK CALCULATION & SAFEGUARDS
        # ==================================================
        total_risk_score = min(100.0, photo_risk + financial_risk + identity_risk + consistency_risk)
        
        # Mandatory Safeguards
        if has_identity_mismatch:
            total_risk_score = max(total_risk_score, 35.0)

        if total_risk_score >= 70.0:
            status = "REJECTED"
            risk_level = "HIGH"
        elif total_risk_score >= 30.0:
            status = "NEEDS_ADMIN_REVIEW"
            risk_level = "MEDIUM"
        else:
            status = "VERIFIED"
            risk_level = "LOW"

        # If identity mismatch occurred, it must NEVER return VERIFIED
        if has_identity_mismatch and status == "VERIFIED":
            status = "NEEDS_ADMIN_REVIEW"
            risk_level = "MEDIUM"
            total_risk_score = max(total_risk_score, 35.0)

        # Update Project table summary
        project.integrity_status = status
        project.risk_score = round(total_risk_score, 1)
        project.risk_level = risk_level
        project.amount_spent = total_expenses_recorded
        project.remaining_amount = max(0.0, project.total_budget - total_expenses_recorded)
        
        # Generate structured recommendation
        if status == "VERIFIED":
            recommendation = "Project evidence, photo forensics, and financial records match declared project information with low risk."
        elif status == "NEEDS_ADMIN_REVIEW":
            recommendation = "Potential evidence anomalies or financial discrepancies detected requiring administrative review."
        else:
            recommendation = "High risk indicators or severe evidence contradictions detected. Administrative rejection or formal audit recommended."

        # Clear existing findings and write updated ones
        db.query(ProjectFinding).filter(ProjectFinding.project_id == project_id).delete()
        for f in findings:
            pf = ProjectFinding(
                project_id=project_id,
                evidence_id=f["evidence_id"],
                category=f["category"],
                risk_level=f["risk_level"],
                score_impact=f["score_impact"],
                message=f["message"]
            )
            db.add(pf)

        # Save or update ProjectRiskAnalysis
        risk_analysis = db.query(ProjectRiskAnalysis).filter(ProjectRiskAnalysis.project_id == project_id).first()
        if not risk_analysis:
            risk_analysis = ProjectRiskAnalysis(project_id=project_id)
            db.add(risk_analysis)
            
        risk_analysis.risk_score = round(total_risk_score, 1)
        risk_analysis.risk_level = risk_level
        risk_analysis.status = status
        risk_analysis.document_identity_risk = round(identity_risk, 1)
        risk_analysis.photo_integrity_risk = round(photo_risk, 1)
        risk_analysis.financial_integrity_risk = round(financial_risk, 1)
        risk_analysis.evidence_consistency_risk = round(consistency_risk, 1)
        risk_analysis.findings_json = json.dumps(findings)
        risk_analysis.recommendation = recommendation

        # Notify Admin if review is required
        if status in ["NEEDS_ADMIN_REVIEW", "REJECTED"]:
            existing_notif = db.query(AdminNotification).filter(
                AdminNotification.project_id == project_id,
                AdminNotification.is_read == False
            ).first()
            if not existing_notif:
                notif = AdminNotification(
                    project_id=project_id,
                    ngo_id=project.ngo_id,
                    title="Project Integrity Review Required",
                    message=f"Project '{project.project_name}' flagged for review (Risk: {total_risk_score:.1f}%, Status: {status}).",
                    risk_score=round(total_risk_score, 1),
                    risk_level=risk_level
                )
                db.add(notif)

        db.commit()
        db.refresh(project)

        return {
            "project_id": project.id,
            "project_name": project.project_name,
            "risk_score": project.risk_score,
            "risk_level": project.risk_level,
            "status": project.integrity_status,
            "recommendation": recommendation,
            "category_breakdown": {
                "document_identity_risk": round(identity_risk, 1),
                "photo_integrity_risk": round(photo_risk, 1),
                "financial_integrity_risk": round(financial_risk, 1),
                "evidence_consistency_risk": round(consistency_risk, 1)
            },
            "findings": findings
        }
