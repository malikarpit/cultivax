"""
Feature Flags Service

Runtime resolver for querying feature flags explicitly mapping environment namespaces.
"""

import time
from sqlalchemy.orm import Session
from app.models.feature_flag import FeatureFlag

# TTL Cache dictionary storing tuples (timestamp, boolean_result)
_FLAG_CACHE = {}
CACHE_TTL = 30  # 30 seconds

def _get_cache_key(flag_name: str, region: str = None, user_id: str = None) -> str:
    return f"{flag_name}:{region or 'none'}:{user_id or 'none'}"

def invalidate_cache(flag_name: str = None):
    """Clear cache entirely or for a specific flag namespace."""
    global _FLAG_CACHE
    if not flag_name:
        _FLAG_CACHE.clear()
    else:
        # Sweep all cached resolution paths bound to this global map
        keys_to_delete = [k for k in _FLAG_CACHE.keys() if k.startswith(f"{flag_name}:")]
        for k in keys_to_delete:
            del _FLAG_CACHE[k]

def is_enabled(db: Session, flag_name: str, user_id: str = None, region: str = None, default: bool = False) -> bool:
    """
    Resolve flag using Precedence Rules:
    1. per_user scope match
    2. per_region scope match
    3. global match
    4. default fallback
    """
    cache_key = _get_cache_key(flag_name, region, user_id)
    
    # Check cache TTL
    if cache_key in _FLAG_CACHE:
        timestamp, result = _FLAG_CACHE[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return result
            
    try:
        # Resolve via Database implicitly filtering scopes securely
        # Note: Since flag_name is NOT unique due to the implementation limits (option B), name spacing covers flags precisely.
        # i.e., `production.ml_kill_switch` acts as the explicit DB primary identifier bounding scoping uniquely.
        flags = db.query(FeatureFlag).filter(
            FeatureFlag.flag_name == flag_name,
            FeatureFlag.is_deleted == False
        ).all()
        
        if not flags:
            return default
            
        # Evaluate precedence
        # 1. User
        if user_id:
            user_flag = next((f for f in flags if f.scope == "per_user" and f.scope_value == str(user_id)), None)
            if user_flag:
                _FLAG_CACHE[cache_key] = (time.time(), user_flag.is_enabled)
                return user_flag.is_enabled
                
        # 2. Region
        if region:
            region_flag = next((f for f in flags if f.scope == "per_region" and f.scope_value == region), None)
            if region_flag:
                _FLAG_CACHE[cache_key] = (time.time(), region_flag.is_enabled)
                return region_flag.is_enabled
                
        # 3. Global
        global_flag = next((f for f in flags if f.scope == "global"), None)
        if global_flag:
            _FLAG_CACHE[cache_key] = (time.time(), global_flag.is_enabled)
            return global_flag.is_enabled
            
        return default
        
    except Exception as repr_err:
        import logging
        logging.error(f"Feature Flag Evaluation Error against [{flag_name}]: {repr_err}")
        return default
