from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import bcrypt
from urllib.parse import quote_plus

app = FastAPI()

# Database connection setup
username = quote_plus("AkanshaShahu")
password = quote_plus("Shahu@20")
try:
    client = MongoClient(f"mongodb+srv://{username}:{password}@cluster1.kwxj4.mongodb.net/town?retryWrites=true&w=majority")
    client.admin.command("ping")
    print("MongoDB connection successful!")
except Exception as e:
    print("MongoDB connection failed!")
    print(f"Error: {e}")
    exit()

db = client["Town"]
resident_collection = db["Residents"]

# Pydantic models
class Resident(BaseModel):
    name: str
    resident_id: str
    password: str
    role: str
    status: str

class UpdateResident(BaseModel):
    name: str | None = None
    password: str | None = None
    role: str | None = None
    status: str | None = None

def hash_password(password):
    """Hashes the given password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed

@app.post("/residents")
def register_resident(resident: Resident):
    """Registers a new resident."""
    try:
        existing_resident = resident_collection.find_one({"resident_id": resident.resident_id})
        if existing_resident:
            raise HTTPException(status_code=400, detail="Resident ID already registered.")

        hashed_password = hash_password(resident.password)

        resident_data = {
            "name": resident.name,
            "resident_id": resident.resident_id,
            "password": hashed_password,
            "role": resident.role,
            "status": resident.status,
            "doc_status": True
        }

        resident_collection.insert_one(resident_data)
        return {"success": True, "message": "Resident registered successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {e}")

@app.put("/residents/{resident_id}")
def update_resident_details(resident_id: str, update_data: UpdateResident):
    """Updates a resident's details."""
    try:
        existing_resident = resident_collection.find_one({"resident_id": resident_id})
        if not existing_resident:
            raise HTTPException(status_code=404, detail="Resident ID not found.")

        update_fields = {}
        if update_data.name:
            update_fields["name"] = update_data.name
        if update_data.password:
            update_fields["password"] = hash_password(update_data.password)
        if update_data.role:
            if update_data.role not in ["Mayor", "Clerk", "Citizen"]:
                raise HTTPException(status_code=400, detail="Invalid role. Must be 'Mayor', 'Clerk', or 'Citizen'.")
            update_fields["role"] = update_data.role
        if update_data.status:
            if update_data.status not in ["Active", "Inactive"]:
                raise HTTPException(status_code=400, detail="Invalid status. Must be 'Active' or 'Inactive'.")
            update_fields["status"] = update_data.status

        if update_fields:
            resident_collection.update_one({"resident_id": resident_id}, {"$set": update_fields})
            return {"success": True, "message": "Resident details updated successfully."}
        else:
            raise HTTPException(status_code=400, detail="No fields to update.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {e}")

@app.get("/residents")
def view_residents():
    """Fetches all active residents."""
    try:
        residents = list(resident_collection.find({"doc_status": True}, {"_id": 0}))
        return residents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching residents: {e}")

@app.delete("/residents/{resident_id}")
def soft_delete_resident(resident_id: str):
    """Soft deletes a resident."""
    try:
        existing_resident = resident_collection.find_one({"resident_id": resident_id})
        if not existing_resident:
            raise HTTPException(status_code=404, detail="Resident ID not found.")

        if existing_resident.get("doc_status"):
            resident_collection.update_one({"resident_id": resident_id}, {"$set": {"doc_status": False}})
            return {"success": True, "message": "Resident soft deleted successfully."}
        else:
            raise HTTPException(status_code=400, detail="Resident is already soft deleted.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {e}")
