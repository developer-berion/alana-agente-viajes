import unittest
import sys
import os
import uuid
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can safely import because _get_db handles lazy loading
from persistence import repository

class TestPersistence(unittest.TestCase):
    
    def setUp(self):
        # Reset the global _db to None before each test
        repository._db = None

    def test_validate_uuid_valid(self):
        valid_uuid = str(uuid.uuid4())
        
        # Mock _get_db to return a MagicMock client
        mock_db = MagicMock()
        with patch('persistence.repository._get_db', return_value=mock_db):
            try:
                repository.save_message(valid_uuid, {"role": "user", "content": "hello"})
            except ValueError as e:
                 if "UUID" in str(e):
                     self.fail(f"raised ValueError unexpectedly for valid UUID: {e}")

    def test_validate_uuid_invalid(self):
        invalid_uuid = "not-a-uuid"
        # Validation checks happen before DB access, but just in case, mock it
        with patch('persistence.repository._get_db', return_value=MagicMock()):
            with self.assertRaises(ValueError):
                repository.save_message(invalid_uuid, {"role": "user", "content": "hi"})
            
    def test_save_message_structure(self):
        valid_uuid = str(uuid.uuid4())
        msg = {"role": "user", "content": "test"}
        
        mock_db = MagicMock()
        # Mock chain
        start_doc = MagicMock()
        start_doc.get.return_value.exists = False # Simulate new session
        
        mock_db.collection.return_value.document.return_value = start_doc
        start_doc.collection.return_value.document.return_value = MagicMock()

        with patch('persistence.repository._get_db', return_value=mock_db):
            repository.save_message(valid_uuid, msg)
            
            # Verify call structure
            # Should access sessions -> doc(uuid)
            mock_db.collection.assert_any_call("sessions")
            # We could do more specific asserts, but specific call args on chains are verbose.
            # Verifying it runs without error and calls collection is good for smoke test.

if __name__ == '__main__':
    unittest.main()
