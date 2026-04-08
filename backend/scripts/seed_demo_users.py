import asyncio
from app.database import SessionLocal
from app.models.user import User
from app.security.auth import hash_password

def seed():
    db = SessionLocal()
    
    users = [
        {"role": "admin", "phone": "+919999999991", "full_name": "Demo Admin"},
        {"role": "farmer", "phone": "+919999999992", "full_name": "Demo Farmer"},
        {"role": "provider", "phone": "+919999999993", "full_name": "Demo Provider"},
    ]
    
    for u in users:
        existing = db.query(User).filter(User.phone == u["phone"]).first()
        if not existing:
            new_user = User(
                full_name=u["full_name"],
                phone=u["phone"],
                role=u["role"],
                password_hash=hash_password("password123"),
                region="Maharashtra",
                preferred_language="en",
            )
            db.add(new_user)
            print(f"Adding {u['role']} with phone {u['phone']} and password password123")
        else:
            print(f"{u['role']} {u['phone']} already exists")
    
    db.commit()
    db.close()

if __name__ == "__main__":
    seed()
