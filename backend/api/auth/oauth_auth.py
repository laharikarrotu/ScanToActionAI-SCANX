"""
OAuth Authentication with Auth0 and Google Sign-In
Supports both Auth0 (recommended) and direct Google OAuth
"""
from typing import Optional, Dict
from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from jose.constants import ALGORITHMS
import httpx
from api.config import settings
from core.logger import get_logger

logger = get_logger("api.oauth_auth")
security = HTTPBearer()

class Auth0Verifier:
    """Verify Auth0 JWT tokens"""
    
    def __init__(self, domain: str, audience: Optional[str] = None):
        self.domain = domain
        self.audience = audience
        self.jwks_url = f"https://{domain}/.well-known/jwks.json"
        self._jwks_cache: Optional[Dict] = None
    
    def get_jwks(self) -> Dict:
        """Get JSON Web Key Set from Auth0"""
        if self._jwks_cache:
            return self._jwks_cache
        
        try:
            response = httpx.get(self.jwks_url, timeout=5.0)
            response.raise_for_status()
            self._jwks_cache = response.json()
            return self._jwks_cache
        except Exception as e:
            logger.error(f"Failed to fetch JWKS from Auth0: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
    
    def verify_token(self, token: str) -> Dict:
        """Verify Auth0 JWT token"""
        try:
            jwks = self.get_jwks()
            unverified_header = jwt.get_unverified_header(token)
            
            # Find the key
            rsa_key = {}
            for key in jwks.get("keys", []):
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
                    break
            
            if not rsa_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find appropriate key"
                )
            
            # Verify token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS.RSA,
                audience=self.audience,
                issuer=f"https://{self.domain}/"
            )
            return payload
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

class GoogleOAuthVerifier:
    """Verify Google OAuth tokens"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
    
    def verify_token(self, token: str) -> Dict:
        """Verify Google OAuth token"""
        try:
            # Verify token with Google
            response = httpx.get(
                f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}",
                timeout=5.0
            )
            response.raise_for_status()
            token_info = response.json()
            
            if token_info.get("audience") != self.client_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token audience mismatch"
                )
            
            return token_info
        except httpx.HTTPError as e:
            logger.error(f"Google token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token"
            )

# Global verifiers
auth0_verifier: Optional[Auth0Verifier] = None
google_verifier: Optional[GoogleOAuthVerifier] = None

if settings.auth0_domain:
    auth0_verifier = Auth0Verifier(
        domain=settings.auth0_domain,
        audience=settings.auth0_audience
    )

if settings.google_client_id:
    google_verifier = GoogleOAuthVerifier(
        client_id=settings.google_client_id
    )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Get current user from OAuth token (Auth0 or Google)"""
    token = credentials.credentials
    
    # Try Auth0 first
    if auth0_verifier:
        try:
            return auth0_verifier.verify_token(token)
        except HTTPException:
            pass
    
    # Try Google
    if google_verifier:
        try:
            return google_verifier.verify_token(token)
        except HTTPException:
            pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials"
    )

def verify_oauth_token(token: str) -> Dict:
    """Verify OAuth token (Auth0 or Google)"""
    # Try Auth0 first
    if auth0_verifier:
        try:
            return auth0_verifier.verify_token(token)
        except HTTPException:
            pass
    
    # Try Google
    if google_verifier:
        try:
            return google_verifier.verify_token(token)
        except HTTPException:
            pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid OAuth token"
    )

