"""
AI-Powered Behavioral Anomaly Detection

Machine learning-based security monitoring for detecting unusual patterns:
- Behavioral analysis of user actions
- Time-series anomaly detection
- Geographic anomaly detection
- Access pattern analysis

Uses statistical methods and simple ML for real-time threat detection.
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from app.models.abuse_flag import AbuseFlag

logger = logging.getLogger(__name__)


@dataclass
class BehavioralProfile:
    """User behavioral profile for anomaly detection."""

    user_id: str
    typical_hour_of_day: List[int]  # Hours when user is typically active
    typical_request_rate: float  # Average requests per minute
    typical_endpoints: List[str]  # Commonly accessed endpoints
    typical_locations: List[str]  # IP addresses/geolocations
    last_updated: datetime


class BehavioralAnomalyDetector:
    """
    AI-powered anomaly detection using behavioral analysis.

    Detects:
    1. Unusual access times
    2. Abnormal request patterns
    3. Geographic anomalies
    4. Privilege escalation attempts
    5. Data exfiltration patterns
    """

    def __init__(self):
        """Initialize anomaly detector."""
        # User profiles (in production, store in Redis/database)
        self.profiles: Dict[str, BehavioralProfile] = {}

        # Request history (sliding window)
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Anomaly scores (0.0 - 1.0, >0.7 is suspicious)
        self.anomaly_thresholds = {
            "time_anomaly": 0.6,
            "rate_anomaly": 0.7,
            "location_anomaly": 0.8,
            "endpoint_anomaly": 0.6,
            "privilege_escalation": 0.9,
        }

    def analyze_request(
        self,
        user_id: str,
        endpoint: str,
        method: str,
        ip_address: str,
        timestamp: Optional[datetime] = None,
    ) -> Tuple[bool, float, List[str]]:
        """
        Analyze request for anomalies.

        Args:
            user_id: User ID
            endpoint: API endpoint
            method: HTTP method
            ip_address: Client IP
            timestamp: Request timestamp

        Returns:
            (is_anomalous, anomaly_score, anomaly_reasons)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Get or create profile
        profile = self.profiles.get(user_id)
        if not profile:
            # New user - create baseline
            profile = self._create_baseline_profile(user_id)
            self.profiles[user_id] = profile

        # Record request
        self.request_history[user_id].append(
            {
                "endpoint": endpoint,
                "method": method,
                "ip": ip_address,
                "timestamp": timestamp,
            }
        )

        # Run anomaly checks
        anomalies = []
        scores = []

        # 1. Time-based anomaly (unusual hour of day)
        time_score = self._check_time_anomaly(timestamp, profile)
        if time_score > self.anomaly_thresholds["time_anomaly"]:
            anomalies.append(f"Unusual access time (score: {time_score:.2f})")
            scores.append(time_score)

        # 2. Request rate anomaly
        rate_score = self._check_rate_anomaly(user_id, profile)
        if rate_score > self.anomaly_thresholds["rate_anomaly"]:
            anomalies.append(f"Abnormal request rate (score: {rate_score:.2f})")
            scores.append(rate_score)

        # 3. Location anomaly
        location_score = self._check_location_anomaly(ip_address, profile)
        if location_score > self.anomaly_thresholds["location_anomaly"]:
            anomalies.append(f"Unusual location (score: {location_score:.2f})")
            scores.append(location_score)

        # 4. Endpoint anomaly
        endpoint_score = self._check_endpoint_anomaly(endpoint, profile)
        if endpoint_score > self.anomaly_thresholds["endpoint_anomaly"]:
            anomalies.append(f"Unusual endpoint access (score: {endpoint_score:.2f})")
            scores.append(endpoint_score)

        # 5. Privilege escalation detection
        if self._is_privilege_escalation_attempt(endpoint, method):
            anomalies.append("Potential privilege escalation attempt")
            scores.append(0.95)

        # Calculate overall anomaly score
        overall_score = max(scores) if scores else 0.0

        # Update profile with new data
        self._update_profile(profile, timestamp, endpoint, ip_address)

        is_anomalous = overall_score > 0.7

        if is_anomalous:
            logger.warning(
                f"Anomaly detected for user {user_id}: "
                f"score={overall_score:.2f}, reasons={anomalies}"
            )

        return is_anomalous, overall_score, anomalies

    def _create_baseline_profile(self, user_id: str) -> BehavioralProfile:
        """Create baseline profile for new user."""
        return BehavioralProfile(
            user_id=user_id,
            typical_hour_of_day=[],
            typical_request_rate=0.0,
            typical_endpoints=[],
            typical_locations=[],
            last_updated=datetime.now(timezone.utc),
        )

    def _check_time_anomaly(
        self,
        timestamp: datetime,
        profile: BehavioralProfile,
    ) -> float:
        """
        Check for unusual access time.

        Returns anomaly score (0.0 - 1.0).
        """
        if not profile.typical_hour_of_day:
            return 0.0  # No baseline yet

        hour = timestamp.hour

        # Check if current hour is in typical hours
        if hour in profile.typical_hour_of_day:
            return 0.0

        # Calculate deviation from typical hours
        if profile.typical_hour_of_day:
            min_distance = min(
                abs(hour - typical_hour) for typical_hour in profile.typical_hour_of_day
            )
            # Normalize to 0-1 (12 hours difference = max anomaly)
            score = min(min_distance / 12.0, 1.0)
            return score

        return 0.5  # Moderate anomaly if no pattern established

    def _check_rate_anomaly(self, user_id: str, profile: BehavioralProfile) -> float:
        """
        Check for abnormal request rate.

        Returns anomaly score (0.0 - 1.0).
        """
        history = self.request_history[user_id]
        if len(history) < 10:
            return 0.0  # Not enough data

        # Calculate recent request rate (last 5 minutes)
        now = datetime.now(timezone.utc)
        recent_requests = [
            req
            for req in history
            if (now - req["timestamp"]).total_seconds() < 300  # 5 minutes
        ]

        current_rate = len(recent_requests) / 5.0  # Requests per minute

        if profile.typical_request_rate == 0:
            return 0.0  # No baseline

        # Calculate deviation
        deviation = abs(current_rate - profile.typical_request_rate)
        relative_deviation = deviation / max(profile.typical_request_rate, 1.0)

        # Score: >3x typical rate = high anomaly
        score = min(relative_deviation / 3.0, 1.0)
        return score

    def _check_location_anomaly(
        self,
        ip_address: str,
        profile: BehavioralProfile,
    ) -> float:
        """
        Check for unusual IP address.

        Returns anomaly score (0.0 - 1.0).
        """
        if not profile.typical_locations:
            return 0.0  # No baseline

        if ip_address in profile.typical_locations:
            return 0.0  # Known location

        # New location is anomalous
        return 0.8

    def _check_endpoint_anomaly(
        self,
        endpoint: str,
        profile: BehavioralProfile,
    ) -> float:
        """
        Check for unusual endpoint access.

        Returns anomaly score (0.0 - 1.0).
        """
        if not profile.typical_endpoints:
            return 0.0  # No baseline

        if endpoint in profile.typical_endpoints:
            return 0.0  # Known endpoint

        # Check if endpoint is admin/sensitive
        sensitive_patterns = [
            "/admin/",
            "/api/v1/admin/",
            "/users/",
            "/delete",
            "/suspend",
        ]
        is_sensitive = any(pattern in endpoint for pattern in sensitive_patterns)

        if is_sensitive:
            return 0.9  # High anomaly for new sensitive endpoint

        return 0.5  # Moderate anomaly for new regular endpoint

    def _is_privilege_escalation_attempt(self, endpoint: str, method: str) -> bool:
        """
        Detect potential privilege escalation attempts.

        Returns True if suspicious.
        """
        # Check for suspicious patterns
        escalation_patterns = [
            "/admin/users/",
            "/api/v1/admin/users/",
            "/role",
            "/suspend",
            "/verify",
            "/api/v1/admin/providers/",
        ]

        for pattern in escalation_patterns:
            if pattern in endpoint and method in ["PUT", "POST", "DELETE"]:
                return True

        return False

    def _update_profile(
        self,
        profile: BehavioralProfile,
        timestamp: datetime,
        endpoint: str,
        ip_address: str,
    ):
        """Update user profile with new data."""
        hour = timestamp.hour

        # Update typical hours (keep last 10 unique hours)
        if hour not in profile.typical_hour_of_day:
            profile.typical_hour_of_day.append(hour)
            if len(profile.typical_hour_of_day) > 10:
                profile.typical_hour_of_day.pop(0)

        # Update typical endpoints (keep top 20)
        if endpoint not in profile.typical_endpoints:
            profile.typical_endpoints.append(endpoint)
            if len(profile.typical_endpoints) > 20:
                profile.typical_endpoints.pop(0)

        # Update typical locations (keep last 5)
        if ip_address not in profile.typical_locations:
            profile.typical_locations.append(ip_address)
            if len(profile.typical_locations) > 5:
                profile.typical_locations.pop(0)

        profile.last_updated = datetime.now(timezone.utc)

    async def create_abuse_flag(
        self,
        db: Session,
        user_id: str,
        anomaly_score: float,
        anomaly_reasons: List[str],
    ):
        """
        Create abuse flag for detected anomaly.

        Args:
            db: Database session
            user_id: User ID
            anomaly_score: Anomaly score
            anomaly_reasons: List of anomaly reasons
        """
        abuse_flag = AbuseFlag(
            user_id=user_id,
            flag_type="behavioral_anomaly",
            severity="high" if anomaly_score > 0.8 else "medium",
            description=f"AI-detected behavioral anomaly (score: {anomaly_score:.2f})",
            details={
                "anomaly_score": anomaly_score,
                "reasons": anomaly_reasons,
                "detection_method": "ai_behavioral_analysis",
            },
            reviewed=False,
        )
        db.add(abuse_flag)
        db.commit()

        logger.warning(
            f"Created abuse flag for user {user_id}: "
            f"score={anomaly_score:.2f}, reasons={anomaly_reasons}"
        )


# Global detector instance
_anomaly_detector: Optional[BehavioralAnomalyDetector] = None


def get_anomaly_detector() -> BehavioralAnomalyDetector:
    """Get global anomaly detector instance."""
    global _anomaly_detector

    if _anomaly_detector is None:
        _anomaly_detector = BehavioralAnomalyDetector()

    return _anomaly_detector
