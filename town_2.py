from pymongo import MongoClient
import bcrypt
from urllib.parse import quote_plus

username = quote_plus('AkanshaShahu')
password = quote_plus('Shahu@20')

client = MongoClient(f'mongodb+srv://{username}:{password}@cluster1.kwxj4.mongodb.net/town?retryWrites=true&w=majority')
db = client["town"]
resident_collection = db["resident"]


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

def register_resident(name, resident_id, password, role, status):
    if resident_collection.find_one({"resident_id": resident_id}):
        return {"success": False, "message": "Resident ID already exists."}

    hashed_password = hash_password(password)

    resident_data = {
        "name": name,
        "resident_id": resident_id,
        "password": hashed_password,
        "role": role,
        "status": status
    }

    resident_collection.insert_one(resident_data)
    return {"success": True, "message": "Resident registered successfully."}

def get_role_permissions(role):
    roles_permissions = {
        "Mayor": "Manage the entire town.",
        "Clerk": "Handle records.",
        "Citizen": "Access basic services."
    }
    return roles_permissions.get(role, "Invalid role.")

if __name__ == "__main__":
    print("Welcome to the Town Hall Registration System")

    name = input("Enter resident's name: ")
    resident_id = input("Enter resident ID: ")
    password = input("Enter password: ")
    role = input("Enter role (Mayor, Clerk, Citizen): ")
    status = input("Enter status (Active, Inactive): ")

    if role not in ["Mayor", "Clerk", "Citizen"]:
        print("Invalid role. Please enter 'Mayor', 'Clerk', or 'Citizen'.")
    else:
        result = register_resident(name, resident_id, password, role, status)
        print(result["message"])

        if result["success"]:
            print(f"Role Permissions: {get_role_permissions(role)}")