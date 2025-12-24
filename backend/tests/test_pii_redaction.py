"""
Unit tests for PII redaction module
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pii_redaction import PIIRedactor


class TestPIIRedactor:
    """Test PIIRedactor class"""
    
    def test_detect_ssn(self):
        """Test SSN detection"""
        redactor = PIIRedactor()
        text = "Patient SSN: 123-45-6789"
        detected = redactor.detect_pii_in_text(text)
        
        ssn_found = any(pii["type"] == "SSN" for pii in detected)
        assert ssn_found, "SSN should be detected"
    
    def test_detect_phone(self):
        """Test phone number detection"""
        redactor = PIIRedactor()
        text = "Contact: (555) 123-4567"
        detected = redactor.detect_pii_in_text(text)
        
        phone_found = any(pii["type"] == "PHONE" for pii in detected)
        assert phone_found, "Phone number should be detected"
    
    def test_detect_email(self):
        """Test email detection"""
        redactor = PIIRedactor()
        text = "Email: patient@example.com"
        detected = redactor.detect_pii_in_text(text)
        
        email_found = any(pii["type"] == "EMAIL" for pii in detected)
        assert email_found, "Email should be detected"
    
    def test_detect_credit_card(self):
        """Test credit card detection"""
        redactor = PIIRedactor()
        text = "Card: 1234 5678 9012 3456"
        detected = redactor.detect_pii_in_text(text)
        
        cc_found = any(pii["type"] == "CREDIT_CARD" for pii in detected)
        assert cc_found, "Credit card should be detected"
    
    def test_detect_medical_record_number(self):
        """Test medical record number detection"""
        redactor = PIIRedactor()
        text = "MRN: 123456789"
        detected = redactor.detect_pii_in_text(text)
        
        mrn_found = any(pii["type"] == "MEDICAL_RECORD" for pii in detected)
        assert mrn_found, "Medical record number should be detected"
    
    def test_detect_date_of_birth(self):
        """Test date of birth detection"""
        redactor = PIIRedactor()
        text = "DOB: 01/15/1990"
        detected = redactor.detect_pii_in_text(text)
        
        dob_found = any(pii["type"] == "DOB" for pii in detected)
        assert dob_found, "Date of birth should be detected"
    
    def test_detect_patient_name_pattern1(self):
        """Test patient name detection - Pattern 1"""
        redactor = PIIRedactor()
        text = "Patient Name: John Doe"
        detected = redactor.detect_pii_in_text(text)
        
        name_found = any(pii["type"] == "PATIENT_NAME" for pii in detected)
        assert name_found, "Patient name should be detected"
    
    def test_detect_patient_name_pattern2(self):
        """Test patient name detection - Pattern 2"""
        redactor = PIIRedactor()
        text = "patient Jane Smith"
        detected = redactor.detect_pii_in_text(text)
        
        name_found = any(pii["type"] == "PATIENT_NAME" for pii in detected)
        assert name_found, "Patient name should be detected"
    
    def test_is_likely_name_valid(self):
        """Test name validation - valid names"""
        redactor = PIIRedactor()
        
        assert redactor._is_likely_name("John Doe") == True
        assert redactor._is_likely_name("Mary Jane Watson") == True
        assert redactor._is_likely_name("Dr. Smith") == True
    
    def test_is_likely_name_invalid(self):
        """Test name validation - invalid names"""
        redactor = PIIRedactor()
        
        assert redactor._is_likely_name("Tylenol") == False  # Medical term
        assert redactor._is_likely_name("John") == False  # Single word
        assert redactor._is_likely_name("A B C D E") == False  # Too many words
        assert redactor._is_likely_name("JOHN DOE") == False  # All caps (likely acronym)
    
    def test_redact_text(self):
        """Test text redaction"""
        redactor = PIIRedactor()
        text = "Patient: John Doe, SSN: 123-45-6789, Email: john@example.com"
        detected = redactor.detect_pii_in_text(text)
        redacted, count = redactor.redact_text(text, detected)
        
        assert count > 0, "Should redact PII"
        assert "123-45-6789" not in redacted
        assert "john@example.com" not in redacted
    
    def test_no_false_positives_medical_terms(self):
        """Test that medical terms are not detected as names"""
        redactor = PIIRedactor()
        text = "Prescription for Tylenol and Aspirin"
        detected = redactor.detect_pii_in_text(text)
        
        # Should not detect medical terms as names
        names = [pii for pii in detected if pii["type"] == "PATIENT_NAME"]
        medical_terms_in_names = any(
            any(term in pii["value"].lower() for term in ["tylenol", "aspirin"])
            for pii in names
        )
        assert not medical_terms_in_names, "Medical terms should not be detected as names"

