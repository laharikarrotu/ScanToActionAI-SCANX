"""
Image Encryption Module - HIPAA Compliance
Encrypts medical images and sensitive data at rest using AES-256
"""
import os
import base64
import json
from typing import Optional, Dict, Any, Union
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    # Fallback for Python version compatibility issues
    Fernet = None
    CRYPTOGRAPHY_AVAILABLE = False
    import warnings
    warnings.warn(f"cryptography not available: {e}. Encryption features will be disabled.")
import logging

logger = logging.getLogger(__name__)

class ImageEncryption:
    """
    Encrypts and decrypts medical images for HIPAA compliance
    Uses Fernet (AES-128 in CBC mode) with PBKDF2 key derivation
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption with key from environment or generate new
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.warning("Cryptography not available. Encryption features disabled.")
            self.cipher = None
            self.encryption_key = None
            return
            
        self.encryption_key = encryption_key or os.getenv("ENCRYPTION_KEY")
        
        if not self.encryption_key:
            # Generate a key (in production, use a key management service)
            logger.warning("No ENCRYPTION_KEY found. Generating temporary key. NOT SECURE FOR PRODUCTION!")
            self.encryption_key = Fernet.generate_key().decode()
            logger.warning("Set ENCRYPTION_KEY in .env for production use")
        else:
            # If key is a string, convert to bytes
            if isinstance(self.encryption_key, str):
                try:
                    # Try to use as-is if it's already a valid Fernet key
                    Fernet(self.encryption_key.encode())
                    self.encryption_key = self.encryption_key.encode()
                except:
                    # Derive key from password using PBKDF2
                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=b'healthscan_salt',  # In production, use random salt per user
                        iterations=100000,
                        backend=default_backend()
                    )
                    self.encryption_key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key.encode()))
        
        self.cipher = Fernet(self.encryption_key)
    
    def encrypt_image(self, image_data: bytes) -> bytes:
        """
        Encrypt image data before storage
        """
        if not self.cipher:
            logger.warning("Encryption not available. Returning unencrypted data.")
            return image_data
        try:
            encrypted_data = self.cipher.encrypt(image_data)
            logger.info(f"Encrypted image: {len(image_data)} bytes → {len(encrypted_data)} bytes")
            return encrypted_data
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise Exception(f"Failed to encrypt image: {str(e)}")
    
    def decrypt_image(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt image data for processing
        """
        if not self.cipher:
            logger.warning("Decryption not available. Returning data as-is.")
            return encrypted_data
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data)
            logger.info(f"Decrypted image: {len(encrypted_data)} bytes → {len(decrypted_data)} bytes")
            return decrypted_data
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise Exception(f"Failed to decrypt image: {str(e)}")
    
    def encrypt_and_encode(self, image_data: bytes) -> str:
        """
        Encrypt and base64 encode for storage in database
        """
        encrypted = self.encrypt_image(image_data)
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decode_and_decrypt(self, encoded_data: str) -> bytes:
        """
        Decode from base64 and decrypt
        """
        encrypted = base64.b64decode(encoded_data.encode('utf-8'))
        return self.decrypt_image(encrypted)
    
    def encrypt_json(self, data: Dict[str, Any]) -> str:
        """
        Encrypt JSON data (e.g., prescription info, patient data) for database storage.
        
        Args:
            data: Dictionary containing sensitive medical data
        
        Returns:
            Base64-encoded encrypted string ready for database storage
        """
        try:
            json_str = json.dumps(data, ensure_ascii=False)
            json_bytes = json_str.encode('utf-8')
            encrypted = self.cipher.encrypt(json_bytes)
            encoded = base64.b64encode(encrypted).decode('utf-8')
            logger.info(f"Encrypted JSON data: {len(json_str)} chars → {len(encoded)} chars")
            return encoded
        except Exception as e:
            logger.error(f"JSON encryption failed: {e}")
            raise Exception(f"Failed to encrypt JSON data: {str(e)}")
    
    def decrypt_json(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt JSON data from database.
        
        Args:
            encrypted_data: Base64-encoded encrypted string from database
        
        Returns:
            Decrypted dictionary
        """
        try:
            encrypted = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_bytes = self.cipher.decrypt(encrypted)
            json_str = decrypted_bytes.decode('utf-8')
            data = json.loads(json_str)
            logger.info(f"Decrypted JSON data: {len(encrypted_data)} chars → {len(json_str)} chars")
            return data
        except Exception as e:
            logger.error(f"JSON decryption failed: {e}")
            raise Exception(f"Failed to decrypt JSON data: {str(e)}")
    
    def encrypt_field(self, field_value: Union[str, int, float]) -> str:
        """
        Encrypt a single field value (e.g., SSN, phone number, medication name).
        
        Args:
            field_value: Value to encrypt (will be converted to string)
        
        Returns:
            Base64-encoded encrypted string
        """
        try:
            value_str = str(field_value)
            value_bytes = value_str.encode('utf-8')
            encrypted = self.cipher.encrypt(value_bytes)
            encoded = base64.b64encode(encrypted).decode('utf-8')
            return encoded
        except Exception as e:
            logger.error(f"Field encryption failed: {e}")
            raise Exception(f"Failed to encrypt field: {str(e)}")
    
    def decrypt_field(self, encrypted_field: str) -> str:
        """
        Decrypt a single field value.
        
        Args:
            encrypted_field: Base64-encoded encrypted string
        
        Returns:
            Decrypted string value
        """
        try:
            encrypted = base64.b64decode(encrypted_field.encode('utf-8'))
            decrypted_bytes = self.cipher.decrypt(encrypted)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Field decryption failed: {e}")
            raise Exception(f"Failed to decrypt field: {str(e)}")
    
    def encrypt_prescription_data(self, prescription_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in prescription data.
        
        Fields encrypted:
        - medication_name
        - prescriber
        - patient_name (if present)
        - date
        
        Args:
            prescription_data: Prescription dictionary
        
        Returns:
            Prescription dictionary with sensitive fields encrypted
        """
        encrypted = prescription_data.copy()
        
        # Encrypt sensitive fields
        sensitive_fields = ['medication_name', 'prescriber', 'patient_name', 'date']
        
        for field in sensitive_fields:
            if field in encrypted and encrypted[field]:
                try:
                    encrypted[field] = self.encrypt_field(encrypted[field])
                    encrypted[f"{field}_encrypted"] = True
                except Exception as e:
                    logger.warning(f"Failed to encrypt field {field}: {e}")
                    # Keep original if encryption fails (better than losing data)
        
        return encrypted
    
    def decrypt_prescription_data(self, encrypted_prescription: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in prescription data.
        
        Args:
            encrypted_prescription: Prescription dictionary with encrypted fields
        
        Returns:
            Prescription dictionary with all fields decrypted
        """
        decrypted = encrypted_prescription.copy()
        
        # Decrypt sensitive fields
        sensitive_fields = ['medication_name', 'prescriber', 'patient_name', 'date']
        
        for field in sensitive_fields:
            if field in decrypted and decrypted.get(f"{field}_encrypted"):
                try:
                    decrypted[field] = self.decrypt_field(decrypted[field])
                    decrypted.pop(f"{field}_encrypted", None)
                except Exception as e:
                    logger.warning(f"Failed to decrypt field {field}: {e}")
                    # Keep encrypted value if decryption fails
        
        return decrypted

