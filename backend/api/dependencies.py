"""
Shared dependencies and initialized services for the API
All engines, rate limiters, and services are initialized here
"""
import sys
import os
from typing import Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.config import settings
from core.logger import get_logger
from vision.ui_detector import VisionEngine, UISchema
from vision.pdf_processor import PDFProcessor
from planner.agent_planner import PlannerEngine, ActionPlan
from executor.browser_executor import BrowserExecutor, ExecutionResult
from memory.event_log import EventLogger
from core.error_handler import ErrorHandler
from core.resource_manager import ResourceManager
from core.encryption import ImageEncryption
from core.audit_logger import AuditLogger
from core.pii_redaction import PIIRedactor
from medication.prescription_extractor import PrescriptionExtractor, PrescriptionInfo
from medication.interaction_checker import InteractionChecker, Medication
from nutrition.diet_advisor import DietAdvisor
from nutrition.condition_advisor import ConditionAdvisor
from nutrition.food_scanner import FoodScanner
from api.rate_limiter import RateLimiter

logger = get_logger("api.dependencies")

# Optional scalability modules (graceful fallback if not available)
try:
    from core.rate_limiter_redis import RedisRateLimiter
    REDIS_RATE_LIMITER_AVAILABLE = True
except ImportError:
    REDIS_RATE_LIMITER_AVAILABLE = False
    RedisRateLimiter = None

try:
    from core.rate_limiter_db import DatabaseRateLimiter
    DATABASE_RATE_LIMITER_AVAILABLE = True
except ImportError:
    DATABASE_RATE_LIMITER_AVAILABLE = False
    DatabaseRateLimiter = None

try:
    from core.rate_limiter_token_bucket import TokenBucketRateLimiter
    TOKEN_BUCKET_AVAILABLE = True
except ImportError:
    TOKEN_BUCKET_AVAILABLE = False
    TokenBucketRateLimiter = None

try:
    from core.cache import cache_manager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    cache_manager = None

try:
    from core.circuit_breaker import CircuitBreaker
    gemini_circuit_breaker = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=60,
        name="gemini_api"
    )
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False
    # Create a simple pass-through wrapper
    class SimpleCircuitBreaker:
        def call(self, func, *args, **kwargs):
            return func(*args, **kwargs)
        async def call_async(self, func, *args, **kwargs):
            return await func(*args, **kwargs)
    gemini_circuit_breaker = SimpleCircuitBreaker()

# Initialize engines - Use combined analyzer if Gemini available, otherwise separate engines
USE_COMBINED_ANALYZER = False
combined_analyzer = None
vision_engine = None
planner_engine = None

# FORCE GEMINI ONLY - No OpenAI fallback
if not settings.gemini_api_key:
    raise ValueError("GEMINI_API_KEY is required. OpenAI has been removed. Please set GEMINI_API_KEY in your .env file.")

try:
    # Always initialize separate engines first (needed for fallback)
    from vision.gemini_detector import GeminiVisionEngine
    from planner.gemini_planner import GeminiPlannerEngine
    vision_engine = GeminiVisionEngine(api_key=settings.gemini_api_key)
    planner_engine = GeminiPlannerEngine(api_key=settings.gemini_api_key)
    logger.info("Initialized Gemini Vision and Planning engines")
    
    # Try combined analyzer (1 API call instead of 2) - OPTIMIZATION!
    try:
        from vision.combined_analyzer import CombinedAnalyzer
        combined_analyzer = CombinedAnalyzer(api_key=settings.gemini_api_key)
        USE_COMBINED_ANALYZER = True
        logger.info("✅ Using Combined Analyzer (Vision + Planning in 1 call) - 50% faster & cheaper!")
    except Exception as e:
        logger.warning(f"Combined analyzer failed: {e}, will use separate engines", exception=e)
        USE_COMBINED_ANALYZER = False
        logger.info("Using separate Gemini Vision and Planning engines (2 API calls)")
except Exception as e:
    logger.error(f"Gemini setup failed: {e}. GEMINI_API_KEY is required.", exception=e)
    raise ValueError(f"Failed to initialize Gemini engines: {e}. Please check your GEMINI_API_KEY.")

# Initialize services
event_logger = EventLogger()
error_handler = ErrorHandler(max_retries=3, retry_delay=1.0)
resource_manager = ResourceManager(default_timeout=30.0)
image_encryption = ImageEncryption()
audit_logger = AuditLogger()
pii_redactor = PIIRedactor(redaction_mode="blur")

logger.info("Initializing HealthScan API", context={"version": "1.0.0"})

# FORCE GEMINI ONLY for prescription extraction
prescription_extractor = PrescriptionExtractor(
    api_key=None,
    gemini_api_key=settings.gemini_api_key,
    use_gemini=True
)
logger.info("Prescription Extractor using Gemini Pro 1.5")

interaction_checker = InteractionChecker()
pdf_processor = PDFProcessor()

# FORCE GEMINI ONLY for diet advisor
# DietAdvisor reads GEMINI_API_KEY from environment, so ensure it's set
import os
os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
diet_advisor = DietAdvisor(api_key=None, use_gemini=True)
logger.info("Diet Advisor using Gemini Pro 1.5")

condition_advisor = ConditionAdvisor()
food_scanner = FoodScanner(api_key=None, use_gemini=True)
logger.info("Food Scanner using Gemini Pro 1.5")

# Rate limiter selection (priority: Redis > Database > Token Bucket > In-Memory)
rate_limiter: Optional[RateLimiter] = None

if REDIS_RATE_LIMITER_AVAILABLE and RedisRateLimiter:
    try:
        rate_limiter = RedisRateLimiter()
        logger.info("Using Redis rate limiter")
    except Exception as e:
        logger.warning(f"Redis rate limiter failed: {e}, trying database...", exception=e)
        rate_limiter = None

if not rate_limiter and DATABASE_RATE_LIMITER_AVAILABLE and DatabaseRateLimiter and settings.database_url:
    try:
        rate_limiter = DatabaseRateLimiter()
        logger.info("Using Database rate limiter (free, multi-instance)")
    except Exception as e:
        logger.warning(f"Database rate limiter failed: {e}, trying token bucket...", exception=e)
        rate_limiter = None

if not rate_limiter and TOKEN_BUCKET_AVAILABLE and TokenBucketRateLimiter:
    try:
        rate_limiter = TokenBucketRateLimiter()
        logger.info("Using Token Bucket rate limiter (free, better algorithm)")
    except Exception as e:
        logger.warning(f"Token bucket rate limiter failed: {e}, using in-memory...", exception=e)
        rate_limiter = None

if not rate_limiter:
    rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
    logger.info("Using in-memory rate limiter (free, single instance)")

# Initialize browser executor (shared instance for better resource management)
# Note: Each request creates its own executor, but we export the class for consistency
browser_executor_class = BrowserExecutor

# Export monitoring functions for routers
from core.monitoring import (
    track_llm_api_call, track_vision_analysis,
    track_prescription_extraction, track_browser_execution,
    track_cache_hit, track_cache_miss
)

# Export ErrorHandler for routers
__all__ = [
    # Engines
    "USE_COMBINED_ANALYZER",
    "combined_analyzer",
    "vision_engine",
    "planner_engine",
    "browser_executor_class",
    # Services
    "rate_limiter",
    "pdf_processor",
    "audit_logger",
    "event_logger",
    "prescription_extractor",
    "interaction_checker",
    "diet_advisor",
    "condition_advisor",
    "food_scanner",
    "error_handler",
    "resource_manager",
    "image_encryption",
    "pii_redactor",
    # Cache
    "CACHE_AVAILABLE",
    "cache_manager",
    # Circuit breaker
    "CIRCUIT_BREAKER_AVAILABLE",
    "gemini_circuit_breaker",
    # Monitoring
    "track_llm_api_call",
    "track_vision_analysis",
    "track_prescription_extraction",
    "track_browser_execution",
    "track_cache_hit",
    "track_cache_miss",
]

