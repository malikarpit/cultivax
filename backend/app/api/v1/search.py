from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/")
def global_search(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Global search endpoint.
    Currently returns intelligent mock recommendations based on the query string.
    """
    query = q.lower()
    results = []

    # Simple contextual regex recommendations based on user query
    if "rice" in query or "wheat" in query or "crop" in query:
        results.append({"type": "crop", "title": f"View {q.capitalize()} Crop", "url": "/crops", "icon": "Sprout"})
    if "weather" in query or "rain" in query or "sun" in query:
        results.append({"type": "insight", "title": "Check Weather Advisory", "url": "/weather", "icon": "CloudSun"})
    if "service" in query or "plow" in query or "drone" in query or "hire" in query:
        results.append({"type": "service", "title": "Hire Service Provider", "url": "/services", "icon": "ShoppingBag"})
    if "alert" in query or "notif" in query:
        results.append({"type": "alert", "title": "View Pending Alerts", "url": "/alerts", "icon": "Bell"})
        
    # Always provide at least a few context-aware default results if no match
    if not results:
        results.extend([
            {"type": "action", "title": f"Log action for '{q}'", "url": "/dashboard", "icon": "Activity"},
            {"type": "service", "title": f"Search marketplace for '{q}'", "url": "/services", "icon": "Search"},
            {"type": "crop", "title": "Add new crop", "url": "/crops/new", "icon": "Plus"}
        ])

    return {"query": q, "results": results[:4]}
