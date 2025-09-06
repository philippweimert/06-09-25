import asyncio
import sys
from pathlib import Path
import os
import sqlalchemy

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from backend.server import save_contact_submission, ContactForm, database, contact_submissions, metadata

async def run_test():
    """
    Tests the contact form submission logic by directly calling the
    save_contact_submission function and verifying the data in the database.
    """
    print("Starting test...")
    try:
        # Connect to the database and create the table
        print("Connecting to database...")
        await database.connect()
        print("Creating table...")
        engine = sqlalchemy.create_engine(str(database.url))
        metadata.create_all(engine)
        print("Table created.")


        # Create a test contact form data object
        print("Creating test data...")
        test_data = ContactForm(
            name="Test User",
            email="test@example.com",
            company="Test Inc.",
            phone="1234567890",
            message="This is a test message."
        )

        # Call the save_contact_submission function
        print("Saving contact submission...")
        await save_contact_submission(test_data)
        print("Contact submission saved.")

        # Verify that the data was inserted correctly
        print("Verifying data...")
        query = contact_submissions.select()
        results = await database.fetch_all(query)

        assert len(results) == 1
        assert results[0]["name"] == "Test User"
        assert results[0]["email"] == "test@example.com"
        assert results[0]["company"] == "Test Inc."
        assert results[0]["phone"] == "1234567890"
        assert results[0]["message"] == "This is a test message."

        print("Test passed successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Disconnect from the database
        print("Disconnecting from database...")
        await database.disconnect()

        # Clean up the test database
        if os.path.exists("./test.db"):
            os.remove("./test.db")
        print("Test finished.")

if __name__ == "__main__":
    asyncio.run(run_test())
