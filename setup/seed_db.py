import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
from flask import Flask
from flask_bcrypt import Bcrypt
import urllib.parse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Flask App Context for Bcrypt ---
app = Flask(__name__)
bcrypt = Bcrypt(app)

def seed_database():
    """Seed the database with initial employee data"""
    load_dotenv(dotenv_path='../.env')

    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        print("ERROR: MONGO_URI is not set in the .env file.")
        return False

    print("Connecting to MongoDB Atlas...")
    try:
        # MongoDB Atlas connection with explicit database name
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas")
        
        # Get database - Atlas URI should include database name
        # If no database name in URI, specify explicitly
        if MONGO_URI.count('/') >= 3 and '?' in MONGO_URI:
            # Database name is in URI
            db = client.get_database()
        else:
            # Fallback to explicit database name
            db = client["HRAgent"]
            
        employees_collection = db["employees"]
        
        # Test collection access
        test_count = employees_collection.count_documents({})
        print(f"✅ Collection accessible. Current employee count: {test_count}")
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("1. Check if your IP address is whitelisted in Atlas")
        print("2. Verify username and password are correct")
        print("3. Ensure database name is included in URI")
        print("4. Check if cluster is running")
        return False

    # --- Enhanced employee dataset with proper role distribution ---
    initial_employees = [
        # HR Staff
        {
            "employee_id": "E001", "balance": 18, "history": ["2024-12-25", "2025-01-01"], 
            "name": "Kalhar Dasanayaka", "department": "HR",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "HR"
        },
        {
            "employee_id": "E002", "balance": 20, "history": [], 
            "name": "Anjana Perera", "department": "HR",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "HR"
        },
        
        # IT Department
        {
            "employee_id": "E003", "balance": 15, "history": ["2025-02-14", "2025-03-15", "2025-04-10", "2025-05-20", "2025-06-25"], 
            "name": "Ravindu Cooray", "department": "IT",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E004", "balance": 18, "history": ["2025-01-15"], 
            "name": "Hasitha Pathum", "department": "IT",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E005", "balance": 16, "history": ["2025-03-01", "2025-04-22"], 
            "name": "Banula Lavindu", "department": "IT",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E006", "balance": 19, "history": ["2025-02-28"], 
            "name": "Kolitha Bhanu", "department": "IT",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E007", "balance": 14, "history": ["2025-01-10", "2025-02-15", "2025-03-20", "2025-04-25", "2025-05-30", "2025-06-15"], 
            "name": "Tharinda Hasaranga", "department": "IT",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E008", "balance": 17, "history": ["2025-04-01", "2025-05-15", "2025-06-10"], 
            "name": "Veenath Mihisara", "department": "IT",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E009", "balance": 12, "history": ["2025-01-05", "2025-02-12", "2025-03-18", "2025-04-22", "2025-05-28", "2025-06-30", "2025-07-15", "2025-07-20"], 
            "name": "Pinil Dissanayaka", "department": "IT",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E010", "balance": 20, "history": [], 
            "name": "Lakshith Bandara", "department": "IT",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E011", "balance": 13, "history": ["2025-02-01", "2025-03-05", "2025-04-12", "2025-05-18", "2025-06-22", "2025-07-08", "2025-07-25"], 
            "name": "Thisal Thulnith", "department": "IT",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        
        # Marketing Department
        {
            "employee_id": "E012", "balance": 18, "history": ["2025-03-10", "2025-05-15"], 
            "name": "Nipuni Virajitha", "department": "Marketing",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E013", "balance": 16, "history": ["2025-01-20", "2025-04-05", "2025-06-18", "2025-07-02"], 
            "name": "Sachini Fernando", "department": "Marketing",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E014", "balance": 19, "history": ["2025-05-01"], 
            "name": "Danushka Silva", "department": "Marketing",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        
        # Games Department
        {
            "employee_id": "E015", "balance": 15, "history": ["2025-02-14", "2025-04-18", "2025-06-12", "2025-07-20", "2025-07-28"], 
            "name": "Malindu Rashmika", "department": "Games",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E016", "balance": 17, "history": ["2025-03-22", "2025-05-08", "2025-07-12"], 
            "name": "Yasiru Tamsisi", "department": "Games",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E017", "balance": 11, "history": ["2025-01-08", "2025-02-20", "2025-03-25", "2025-04-30", "2025-05-22", "2025-06-28", "2025-07-15", "2025-07-30"], 
            "name": "Chamindu Ganganath", "department": "Games",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E018", "balance": 20, "history": [], 
            "name": "Lahiru Prasanga", "department": "Games",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E019", "balance": 14, "history": ["2025-01-25", "2025-03-15", "2025-05-10", "2025-06-20", "2025-07-05", "2025-07-18"], 
            "name": "Prabath Megha", "department": "Games",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E020", "balance": 16, "history": ["2025-02-05", "2025-04-28", "2025-06-15", "2025-07-22"], 
            "name": "Kasun Rajitha", "department": "Games",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        
        # Finance Department
        {
            "employee_id": "E021", "balance": 18, "history": ["2025-03-08", "2025-06-12"], 
            "name": "Priyanka Jayasinghe", "department": "Finance",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E022", "balance": 19, "history": ["2025-05-20"], 
            "name": "Ruwan Kumara", "department": "Finance",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        
        # Operations Department
        {
            "employee_id": "E023", "balance": 15, "history": ["2025-01-12", "2025-03-18", "2025-05-25", "2025-07-08", "2025-07-26"], 
            "name": "Amali Wickramasinghe", "department": "Operations",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E024", "balance": 17, "history": ["2025-02-28", "2025-04-15", "2025-06-30"], 
            "name": "Chaminda Rathnayake", "department": "Operations",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        },
        {
            "employee_id": "E025", "balance": 20, "history": [], 
            "name": "Sanduni Perera", "department": "Operations",
            "password": bcrypt.generate_password_hash("pw123").decode('utf-8'),
            "role": "Employee"
        }
    ]

    print(f"Seeding database with {len(initial_employees)} employees...")
    
    try:
        # Clear existing data
        result = employees_collection.delete_many({})
        print(f"✅ Cleared {result.deleted_count} existing records")
        
        # Insert new data
        insert_result = employees_collection.insert_many(initial_employees)
        print(f"✅ Inserted {len(insert_result.inserted_ids)} new records")
        
        final_count = employees_collection.count_documents({})
        print(f"✅ Seeding complete! Total employees in database: {final_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        return False
    

def create_indexes():
    """Create database indexes for better performance"""
    try:
        load_dotenv(dotenv_path='../.env')
        MONGO_URI = os.getenv("MONGO_URI")
        
        client = MongoClient(MONGO_URI)
        db = client.get_database()
        employees_collection = db["employees"]
        
        # Create indexes
        employees_collection.create_index("employee_id", unique=True)
        employees_collection.create_index("department")
        employees_collection.create_index("role")
        employees_collection.create_index("balance")
        
        print("✅ Database indexes created successfully")
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")

if __name__ == "__main__":
    print("🚀 Starting HR Multi-Agent System Database Setup")
    print("=" * 50)
    
    # Seed the database
    success = seed_database()
    
    if success:
        # Create indexes for performance
        create_indexes()
        
        print("\n🎉 Database setup completed successfully!")
        print("\nDefault login credentials:")
        print("HR Users:")
        print("  E001 / pw123 (Kalhar Dasanayaka)")
        print("  E002 / pw123 (Anjana Perera)")
        print("\nEmployee Users:")
        print("  E003 / pw123 (Ravindu Cooray)")
        print("  E004 / pw123 (Hasitha Pathum)")
        print("  ... and many more!")
        print("\n🚀 Ready to start the multi-agent HR system!")
    else:
        print("\n❌ Database setup failed. Please check the errors above.")