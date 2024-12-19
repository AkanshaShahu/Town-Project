from pymongo import MongoClient
import bcrypt
from urllib.parse import quote_plus

# Database connection setup
username = quote_plus('AkanshaShahu')
password = quote_plus('Shahu@20')

try:
    client = MongoClient(f'mongodb+srv://{username}:{password}@cluster1.kwxj4.mongodb.net/town?retryWrites=true&w=majority')
    # Ping the database to check the connection
    client.admin.command('ping')
    print("MongoDB connection successful!")
except Exception as e:
    print("MongoDB connection failed!")
    print(f"Error: {e}")
    exit()

db = client["Town"]
resident_collection = db["Residents"]

def hash_password(password):
    """Hashes the given password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

def register_resident(name, resident_id, password, role, status):
    """Registers a new resident in the database."""
    try:
        # Check if the resident ID already exists
        existing_resident = resident_collection.find_one({"resident_id": resident_id})
        if existing_resident:
            return {"success": False, "message": "Resident ID already registered."}

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
    except Exception as e:
        return {"success": False, "message": f"Error occurred: {e}"}

def view_residents():
    """Fetches and returns all residents from the database."""
    try:
        residents = list(resident_collection.find({}, {"_id": 0}))  # Exclude MongoDB '_id' field
        return residents
    except Exception as e:
        print(f"Error fetching residents: {e}")
        return []

if __name__ == "__main__":
    while True:
        print("\nWelcome to the Town Hall System")
        print("1. Register Resident")
        print("2. View All Residents")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
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

        elif choice == "2":
            print("\nFetching all residents from MongoDB...")
            residents = view_residents()
            if residents:
                for resident in residents:
                    print(resident)
            else:
                print("No residents found in the database.")

        elif choice == "3":
            print("Exiting the system. Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")

