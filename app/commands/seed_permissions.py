from pathlib import Path
from app.db.session import SessionLocal
from app.models.permission import Permission

file_path = Path(__file__).resolve().parents[1]/"data"/"permissions.txt"

db = SessionLocal()

try:
    with open(file_path,"r") as p_file:
        permission = [
            line.strip()
            for line in p_file
            if line.strip()
        ]
    for name  in permission:
        p_exsisting = db.query(Permission).filter(Permission.name == name).first()

        if not p_exsisting:
            db.add(Permission(name = name))   
            print(f"Created {name}") 
        else:
            print(f"Already exists: {name}")    
    db.commit()
    print("All permissions processed successfully!")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")

finally:
    db.close()
