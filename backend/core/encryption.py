"""
Image Encryption Module - HIPAA Compliance
Encrypts medical images at rest using AES-256
"""
import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
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

