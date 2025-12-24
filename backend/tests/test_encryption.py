"""
Unit tests for encryption module

This test suite verifies the ImageEncryption class which provides:
- Image encryption/decryption (AES-256)
- Field-level encryption (for database storage)
- Prescription data encryption (selective field encryption)
- Key isolation (data encrypted with one key cannot be decrypted with another)

Each test function is documented with:
- Purpose: What it tests and why it's critical for HIPAA compliance
- What it verifies: Encryption algorithms, data integrity, security properties
- Why it matters: HIPAA requires encryption at rest for PHI
- What to modify: Guidance if encryption algorithms or key management changes
"""
import pytest
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Import directly from module to avoid FastAPI dependency chain in core/__init__.py
from core.encryption import ImageEncryption


class TestImageEncryption:
    """Test ImageEncryption class"""
    
    def test_encrypt_decrypt_roundtrip(self):
        """
        Test that encryption and decryption work correctly.
        
        CRITICAL: This test REQUIRES cryptography library.
        Encryption is mandatory for HIPAA compliance - if this fails, 
        the core business logic is broken.
        """
        # REQUIRE cryptography - fail if not available (it's in requirements.txt)
        try:
            from cryptography.fernet import Fernet
        except ImportError as e:
            pytest.fail(
                f"CRITICAL: cryptography library is required but not installed. "
                f"This is a core dependency for HIPAA compliance. "
                f"Install with: pip install cryptography>=41.0.0. "
                f"Error: {e}"
            )
        
        # Use test key (not production)
        test_key = "test-encryption-key-for-unit-tests-only"
        # Check if require_encryption parameter exists
        import inspect
        sig = inspect.signature(ImageEncryption.__init__)
        if 'require_encryption' in sig.parameters:
            encryption = ImageEncryption(encryption_key=test_key, require_encryption=False)
        else:
            encryption = ImageEncryption(encryption_key=test_key)
        
        # Encryption MUST be available - fail if not
        if encryption.cipher is None:
            pytest.fail(
                "CRITICAL: Encryption cipher is None. "
                "Encryption is mandatory for medical data. "
                "Check that cryptography library is properly installed."
            )
        
        original_data = b"test image data for encryption"
        encrypted = encryption.encrypt_image(original_data)
        decrypted = encryption.decrypt_image(encrypted)
        
        assert decrypted == original_data, "Decrypted data should match original"
        assert encrypted != original_data, "Encrypted data should be different"
    
    def test_encryption_produces_different_output(self):
        """
        Test that same input produces different encrypted output (due to IV).
        
        CRITICAL: This test REQUIRES cryptography library.
        """
        try:
            from cryptography.fernet import Fernet
        except ImportError as e:
            pytest.fail(f"CRITICAL: cryptography library required. Error: {e}")
        
        test_key = "test-encryption-key-for-unit-tests-only"
        import inspect
        sig = inspect.signature(ImageEncryption.__init__)
        if 'require_encryption' in sig.parameters:
            encryption = ImageEncryption(encryption_key=test_key, require_encryption=False)
        else:
            encryption = ImageEncryption(encryption_key=test_key)
        
        if encryption.cipher is None:
            pytest.fail("CRITICAL: Encryption cipher is None")
        
        original_data = b"test data"
        encrypted1 = encryption.encrypt_image(original_data)
        encrypted2 = encryption.encrypt_image(original_data)
        
        # Encrypted outputs should be different (due to random IV)
        assert encrypted1 != encrypted2
    
    def test_encrypt_field(self):
        """
        Test field encryption.
        
        CRITICAL: This test REQUIRES cryptography library.
        """
        try:
            from cryptography.fernet import Fernet
        except ImportError as e:
            pytest.fail(f"CRITICAL: cryptography library required. Error: {e}")
        
        test_key = "test-encryption-key-for-unit-tests-only"
        import inspect
        sig = inspect.signature(ImageEncryption.__init__)
        if 'require_encryption' in sig.parameters:
            encryption = ImageEncryption(encryption_key=test_key, require_encryption=False)
        else:
            encryption = ImageEncryption(encryption_key=test_key)
        
        if encryption.cipher is None:
            pytest.fail("CRITICAL: Encryption cipher is None")
        
        original = "sensitive field data"
        encrypted = encryption.encrypt_field(original)
        decrypted = encryption.decrypt_field(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_prescription_data(self):
        """
        Test prescription data encryption.
        
        CRITICAL: This test REQUIRES cryptography library.
        Prescription data encryption is mandatory for HIPAA compliance.
        """
        try:
            from cryptography.fernet import Fernet
        except ImportError as e:
            pytest.fail(f"CRITICAL: cryptography library required. Error: {e}")
        
        test_key = "test-encryption-key-for-unit-tests-only"
        import inspect
        sig = inspect.signature(ImageEncryption.__init__)
        if 'require_encryption' in sig.parameters:
            encryption = ImageEncryption(encryption_key=test_key, require_encryption=False)
        else:
            encryption = ImageEncryption(encryption_key=test_key)
        
        if encryption.cipher is None:
            pytest.fail("CRITICAL: Encryption cipher is None")
        
        prescription = {
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "patient_name": "John Doe",
            "prescriber": "Dr. Smith",
            "date": "2024-01-15"
        }
        
        encrypted = encryption.encrypt_prescription_data(prescription)
        
        # Verify actual encrypted values (base64 encoded strings, not original)
        assert encrypted["medication_name"] != prescription["medication_name"]
        assert encrypted["patient_name"] != prescription["patient_name"]
        assert encrypted["prescriber"] != prescription["prescriber"]
        assert encrypted["date"] != prescription["date"]
        
        # Verify encrypted fields are base64 strings (actual format)
        import base64
        for field in ["medication_name", "patient_name", "prescriber", "date"]:
            encrypted_value = encrypted[field]
            assert isinstance(encrypted_value, str), f"{field} should be encrypted string, got {type(encrypted_value)}"
            # Verify it's valid base64 (actual encrypted format)
            try:
                base64.b64decode(encrypted_value)
            except Exception as e:
                pytest.fail(f"{field} encrypted value is not valid base64: {e}")
        
        # Verify actual encryption flags are set (real boolean values)
        assert encrypted.get("medication_name_encrypted") == True
        assert encrypted.get("patient_name_encrypted") == True
        assert encrypted.get("prescriber_encrypted") == True
        assert encrypted.get("date_encrypted") == True
        
        # Verify non-sensitive field is unchanged (actual value check)
        assert encrypted["dosage"] == prescription["dosage"], "Dosage should not be encrypted"
    
    def test_decrypt_prescription_data(self):
        """
        Test prescription data decryption.
        
        CRITICAL: This test REQUIRES cryptography library.
        """
        try:
            from cryptography.fernet import Fernet
        except ImportError as e:
            pytest.fail(f"CRITICAL: cryptography library required. Error: {e}")
        
        test_key = "test-encryption-key-for-unit-tests-only"
        import inspect
        sig = inspect.signature(ImageEncryption.__init__)
        if 'require_encryption' in sig.parameters:
            encryption = ImageEncryption(encryption_key=test_key, require_encryption=False)
        else:
            encryption = ImageEncryption(encryption_key=test_key)
        
        if encryption.cipher is None:
            pytest.fail("CRITICAL: Encryption cipher is None")
        
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
        """
        Test that decryption with wrong key fails.
        
        CRITICAL: This test REQUIRES cryptography library.
        This verifies encryption security - if this fails, encryption is broken.
        """
        try:
            from cryptography.fernet import Fernet
        except ImportError as e:
            pytest.fail(f"CRITICAL: cryptography library required. Error: {e}")
        
        import inspect
        sig = inspect.signature(ImageEncryption.__init__)
        if 'require_encryption' in sig.parameters:
            encryption1 = ImageEncryption(encryption_key="key1", require_encryption=False)
            encryption2 = ImageEncryption(encryption_key="key2", require_encryption=False)
        else:
            encryption1 = ImageEncryption(encryption_key="key1")
            encryption2 = ImageEncryption(encryption_key="key2")
        
        if encryption1.cipher is None or encryption2.cipher is None:
            pytest.fail("CRITICAL: Encryption cipher is None")
        
        original_data = b"test data"
        encrypted = encryption1.encrypt_image(original_data)
        
        # Decryption with wrong key should fail (different key = different salt = different derived key)
        with pytest.raises(Exception):
            encryption2.decrypt_image(encrypted)

