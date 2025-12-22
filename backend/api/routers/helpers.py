"""
Shared helper functions for routers
"""
from vision.ui_detector import UISchema
from medication.prescription_extractor import PrescriptionExtractor
from core.logger import get_logger

async def extract_prescription_if_applicable(
    image_data: bytes,
    ui_schema: UISchema,
    intent_lower: str,
    prescription_extractor: PrescriptionExtractor,
    logger_instance
) -> dict:
    """Extract prescription data if the document is a prescription."""
    structured_data = {}
    page_type = ui_schema.page_type or ""
    if "prescription" in page_type.lower() or "medication" in intent_lower:
        try:
            prescription = prescription_extractor.extract_from_image(image_data)
            if prescription and prescription.medication_name != "Unknown":
                structured_data = {
                    "medications": [{
                        "medication_name": prescription.medication_name,
                        "dosage": prescription.dosage,
                        "frequency": prescription.frequency,
                        "quantity": prescription.quantity,
                        "refills": prescription.refills,
                        "instructions": prescription.instructions
                    }],
                    "prescriber": prescription.prescriber,
                    "pharmacy": prescription.pharmacy if hasattr(prescription, 'pharmacy') else None,
                    "date": prescription.date,
                    "instructions": prescription.instructions
                }
        except Exception as e:
            logger_instance.warning(f"Prescription extraction failed: {e}", exception=e, context={"step": "prescription_extraction"})
    return structured_data

