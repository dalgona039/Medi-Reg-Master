"""
Conftest initialization - mock Google API first.
"""
import sys
from unittest.mock import MagicMock

google_mock = MagicMock()
google_mock.genai = MagicMock()
sys.modules['google'] = google_mock
sys.modules['google.genai'] = google_mock.genai
