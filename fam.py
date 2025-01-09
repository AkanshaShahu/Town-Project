from typing import List
from pydantic import Field
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from pymongo import MongoClient
import bcrypt
from urllib.parse import quote_plus
from typing import Optional


app = FastAPI()

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

# Pydantic models for family details
class FamilyMember(BaseModel):
    name: str
    age: int
    gender: str
    salary: int
    occupation: str

class FamilyDetails(BaseModel):
    resident_id: str
    num_members: int
    members: List[FamilyMember]


# Pydantic models
class Resident(BaseModel):
    name: str
    resident_id: str
    password: str
    role: str 
    status: str 
    Land_owned_in_sq_mtr: int


    @validator("resident_id")
    def validate_resident_id(cls, resident_id):
        if not re.fullmatch(r"RID\d{5}", resident_id):
            raise ValueError("resident_id must start with 'RID' followed by exactly 5 digits (e.g., RID04560).")
        return resident_id


class UpdateResident(BaseModel):
    name: str | None = None
    password: str | None = None
    role: str | None = None
    status: str | None = None
    Land_owned_in_sq_mtr: int | None = None
    num_of_members: int | None = None
    occupation: str | None = None
    Salary: int | None = None
    Age: int | None = None


class TaxPayment(BaseModel):
    employee_id: str
    resident_id: str
    amount_paid: Optional[float] # Amount the citizen pays
    
    @validator("employee_id")
    def validate_employee_id(cls, value):
        if not re.fullmatch(r"EID\d{5}", value):
            raise ValueError("Employee ID must start with 'EID' followed by exactly 5 digits.")
        return value

    @validator("resident_id")
    def validate_tax_resident_id(cls, resident_id):
        if not re.fullmatch(r"RID\d{5}", resident_id):
            raise ValueError("resident_id must start with 'RID' followed by exactly 5 digits (e.g., RID04560).")
        return resident_id


def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt)

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
            "doc_status": True,
            "Land_owned_in_sq_mtr": resident.Land_owned_in_sq_mtr,
            "tax_rate": 0.01,
            "tax_paid": False
        }
        resident_collection.insert_one(resident_data)
        return {"success": True, "message": "Resident registered successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {e}")

@app.get("/residents")
def view_residents():
    """Fetches all active residents."""
    try:
        residents = list(resident_collection.find({"doc_status": True}, {"_id": 0, "password": 0}))
        return residents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching residents: {e}")

@app.post("/residents/family")
def add_family_details(family_details: FamilyDetails):
    """
    Adds family details for a resident.
    """
    try:
        # Validate the resident
        resident = resident_collection.find_one({"resident_id": family_details.resident_id})
        if not resident:
            raise HTTPException(status_code=404, detail="Resident not found.")

        if resident.get("role") != "Citizen":
            raise HTTPException(
                status_code=400,
                detail="Family details can only be added for residents with the role 'Citizen'.",
            )

        # Ensure the number of members matches the provided data
        if family_details.num_members != len(family_details.members):
            raise HTTPException(
                status_code=400,
                detail="Number of members does not match the provided details.",
            )

        # Prepare data to store
        family_data = {
            "num_members": family_details.num_members,
            "members": [
                {
                    "name": member.name,
                    "age": member.age,
                    "gender": member.gender,
                    "salary": member.salary,
                    "occupation": member.occupation,
                }
                for member in family_details.members
            ],
        }

        # Update the resident document with family details
        resident_collection.update_one(
            {"resident_id": family_details.resident_id},
            {"$set": {"family_details": family_data}},
        )

        return {
            "success": True,
            "message": "Family details added successfully.",
            "resident_id": family_details.resident_id,
        }

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

@app.get("/tax/calculate/{resident_id}")
def calculate_tax(resident_id: str):
    """Calculates the tax for the resident."""
    resident = resident_collection.find_one({"resident_id": resident_id})
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found.")

    # Calculate the required tax based on land size and tax rate
    land_size = resident.get("Land_owned_in_sq_mtr", 0)
    tax_rate = resident.get("tax_rate", 0.01)
    required_tax = land_size * tax_rate

    return {
        "resident_id": resident_id,
        "land_size": land_size,
        "tax_rate": tax_rate,
        "required_tax": required_tax,
        "message": "Tax calculated. Please enter the amount you have paid."
    }


@app.put("/tax/update")
def update_tax_status(tax_payment: TaxPayment):
    """Updates the tax payment status after receiving the amount paid."""
    resident = resident_collection.find_one({"resident_id": tax_payment.resident_id})
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found.")

    # Calculate required tax
    land_size = resident.get("Land_owned_in_sq_mtr", 0)
    tax_rate = resident.get("tax_rate", 0.01)
    required_tax = land_size * tax_rate

    # Update tax payment
    if tax_payment.amount_paid is None:
        raise HTTPException(status_code=400, detail="Amount paid cannot be None.")

    amount_paid = tax_payment.amount_paid
    if amount_paid >= required_tax:
        payment_status = "Fully Paid"
    elif 0 < amount_paid < required_tax:
        payment_status = "Partially Paid"
    else:
        payment_status = "Not Paid"

    resident_collection.update_one(
        {"resident_id": tax_payment.resident_id},
        {"$set": {"tax_paid": payment_status, "amount_paid": amount_paid}}
    )

    return {
        "success": True,
        "message": f"Tax status updated to '{payment_status}' for Resident ID: {tax_payment.resident_id}",
        "amount_paid": amount_paid,
        "required_tax": required_tax
    }
