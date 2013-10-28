import sys
import os
import unittest
import mock

sys.path.append(os.path.realpath('.'))
from uniqueds.mongo_store import MongoStore

class TestMongoService(unittest.TestCase):
    def setUp(self):
        mock_db = mock.Mock()
        self.service = MongoStore(mock_db)

    def test_self(self):
        self.assertFalse(False)

    def test_init(self):
        self.assertIsNotNone( self.service )

    def test_call(self):
        #Arrange
        #Act
        #Assert
        pass
