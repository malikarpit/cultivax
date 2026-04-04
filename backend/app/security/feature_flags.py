from fastapi import HTTPException, status, Request
from app.config import settings

def require_feature_flag(flag_name: str, enabled_by_default: bool = False):
    """
    Dependency generator that checks if a feature flag is enabled.
    In environments where settings don't explicitly have the flag, it falls back to enabled_by_default.
    """
    def _dependency(request: Request):
        # We can look up feature flags from settings, or from a cache/DB.
        # For now, we simulate by checking settings.
        
        # E.g. ML features might be under settings.ENABLE_ML_FEATURES
        # If the property doesn't exist, use default
        is_enabled = getattr(settings, f"ENABLE_{flag_name.upper()}_FEATURES", enabled_by_default)
        
        if not is_enabled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature '{flag_name}' is currently disabled."
            )
            
    return _dependency
