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
        self.audience = audience  # Optional - if None, won't validate audience
        self.jwks_url = f"https://{domain}/.well-known/jwks.json"
        self._jwks_cache = None
    
    async def get_jwks(self) -> Dict:
        """Get JSON Web Key Set from Auth0"""
        if self._jwks_cache is None:
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(self.jwks_url, timeout=5.0)
                    response.raise_for_status()
                    self._jwks_cache = response.json()
                except Exception as e:
                    logger.error(f"Failed to fetch JWKS: {e}")
                    raise HTTPException(
                        status_code=503,
                        detail="Authentication service unavailable"
                    )
        return self._jwks_cache
    
    def get_signing_key(self, token: str, jwks: Dict) -> Optional[str]:
        """Get the signing key for a token"""
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    return key
        except Exception as e:
            logger.error(f"Error getting signing key: {e}")
        return None
    
    async def verify_token(self, token: str) -> Dict:
        """Verify Auth0 JWT token"""
        jwks = await self.get_jwks()
        signing_key = self.get_signing_key(token, jwks)
        
        if not signing_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
        
        try:
            # Construct the public key
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(signing_key)
            
            # Verify and decode the token
            # Audience is optional - if not set, skip audience validation
            decode_options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True
            }
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[ALGORITHMS.RS256],
                audience=self.audience if self.audience else None,
                issuer=f"https://{self.domain}/",
                options=decode_options
            )
            return payload
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )

class GoogleOAuthVerifier:
    """Verify Google OAuth tokens (direct Google Sign-In)"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.google_issuers = [
            "https://accounts.google.com",
            "accounts.google.com"
        ]
    
    async def verify_token(self, token: str) -> Dict:
        """Verify Google OAuth token"""
        try:
            # Get token info from Google
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo",
                    params={"id_token": token},
                    timeout=5.0
                )
                response.raise_for_status()
                token_info = response.json()
            
            # Verify the token
            if token_info.get("aud") != self.client_id:
                raise HTTPException(
                    status_code=401,
                    detail="Token audience mismatch"
                )
            
            if token_info.get("iss") not in self.google_issuers:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token issuer"
                )
            
            # Extract user info
            return {
                "sub": token_info.get("sub"),
                "email": token_info.get("email"),
                "name": token_info.get("name"),
                "picture": token_info.get("picture"),
                "email_verified": token_info.get("email_verified", False),
                "iss": token_info.get("iss"),
                "aud": token_info.get("aud")
            }
        except httpx.HTTPError as e:
            logger.error(f"Failed to verify Google token: {e}")
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )

# Initialize auth verifiers (if configured)
auth0_verifier: Optional[Auth0Verifier] = None
google_verifier: Optional[GoogleOAuthVerifier] = None

if hasattr(settings, 'auth0_domain') and settings.auth0_domain:
    auth0_verifier = Auth0Verifier(
        domain=settings.auth0_domain,
        audience=settings.auth0_audience if settings.auth0_audience else None
    )
    if settings.auth0_audience:
        logger.info(f"Auth0 authentication enabled with API audience: {settings.auth0_audience}")
    else:
        logger.info("Auth0 authentication enabled (no custom API - using default)")
        logger.warning("⚠️  For production, create a custom API in Auth0 and set AUTH0_AUDIENCE")

if hasattr(settings, 'google_client_id') and settings.google_client_id:
    google_verifier = GoogleOAuthVerifier(
        client_id=settings.google_client_id
    )
    logger.info("Google OAuth authentication enabled")

async def verify_oauth_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Verify OAuth token (Auth0 or Google)
    Supports both Auth0 and direct Google OAuth
    """
    token = credentials.credentials
    
    # Try Auth0 first (if configured)
    if auth0_verifier:
        try:
            payload = await auth0_verifier.verify_token(token)
            payload["auth_provider"] = "auth0"
            return payload
        except HTTPException:
            # If Auth0 fails, try Google (if configured)
            pass
    
    # Try Google OAuth (if configured)
    if google_verifier:
        try:
            payload = await google_verifier.verify_token(token)
            payload["auth_provider"] = "google"
            return payload
        except HTTPException:
            pass
    
    # If both fail or neither is configured, raise error
    raise HTTPException(
        status_code=401,
        detail="Invalid authentication token. Please sign in again.",
        headers={"WWW-Authenticate": "Bearer"}
    )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Get current authenticated user from OAuth token
    Use this as a dependency to protect routes
    """
    return await verify_oauth_token(credentials)

