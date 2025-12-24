"""
Unit tests for encryption module
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.encryption import ImageEncryption


class TestImageEncryption:
    """Test ImageEncryption class"""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly"""
        # Use test key (not production)
        test_key = "test-encryption-key-for-unit-tests-only"
        encryption = ImageEncryption(encryption_key=test_key, require_encryption=False)
        
        original_data = b"test image data for encryption"
        encrypted = encryption.encrypt_image(original_data)
        decrypted = encryption.decrypt_image(encrypted)
        
        assert decrypted == original_data, "Decrypted data should match original"
        assert encrypted != original_data, "Encrypted data should be different"
    
    def test_encryption_produces_different_output(self):
        """Test that same input produces different encrypted output (due to IV)"""
        test_key = "test-encryption-key-for-unit-tests-only"
        encryption = ImageEncryption(encryption_key=test_key, require_encryption=False)
        
        original_data = b"test data"
        encrypted1 = encryption.encrypt_image(original_data)
        encrypted2 = encryption.encrypt_image(original_data)
        
        # Encrypted outputs should be different (due to random IV)
        assert encrypted1 != encrypted2
    
    def test_encrypt_field(self):
        """Test field encryption"""
        test_key = "test-encryption-key-for-unit-tests-only"
        encryption = ImageEncryption(encryption_key=test_key, require_encryption=False)
        
        original = "sensitive field data"
        encrypted = encryption.encrypt_field(original)
        decrypted = encryption.decrypt_field(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_prescription_data(self):
        """Test prescription data encryption"""
        test_key = "test-encryption-key-for-unit-tests-only"
        encryption = ImageEncryption(encryption_key=test_key, require_encryption=False)
        
        prescription = {
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "patient_name": "John Doe",
            "prescriber": "Dr. Smith",
            "date": "2024-01-15"
        }
        
        encrypted = encryption.encrypt_prescription_data(prescription)
        
        # Sensitive fields should be encrypted (different from original)
        assert encrypted["medication_name"] != prescription["medication_name"]
        assert encrypted["patient_name"] != prescription["patient_name"]
        assert encrypted["prescriber"] != prescription["prescriber"]
        
        # Non-sensitive fields should remain the same
        assert encrypted["date"] == prescription["date"]
    
    def test_decrypt_prescription_data(self):
        """Test prescription data decryption"""
        test_key = "test-encryption-key-for-unit-tests-only"
        encryption = ImageEncryption(encryption_key=test_key, require_encryption=False)
        
        prescription = {
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "patient_name": "John Doe",
            "prescriber": "Dr. Smith",
            "date": "2024-01-15"
        }
        
        encrypted = encryption.encrypt_prescription_data(prescription)
        decrypted = encryption.decrypt_prescription_data(encrypted)
        
        assert decrypted["medication_name"] == prescription["medication_name"]
        assert decrypted["patient_name"] == prescription["patient_name"]
        assert decrypted["prescriber"] == prescription["prescriber"]
        assert decrypted["date"] == prescription["date"]
    
    def test_wrong_key_fails(self):
        """Test that decryption with wrong key fails"""
        encryption1 = ImageEncryption(encryption_key="key1", require_encryption=False)
        encryption2 = ImageEncryption(encryption_key="key2", require_encryption=False)
        
        original_data = b"test data"
        encrypted = encryption1.encrypt_image(original_data)
        
        # Decryption with wrong key should fail
        with pytest.raises(Exception):
            encryption2.decrypt_image(encrypted)

