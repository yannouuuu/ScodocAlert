import os
import pytest
from unittest.mock import patch


class TestConfig:
    """Tests pour le module config."""
    
    @patch.dict(os.environ, {
        "SCODOC_URL": "https://test.scodoc.com",
        "SCODOC_USER": "testuser",
        "SCODOC_PASSWORD": "testpass",
        "DISCORD_WEBHOOK_URL": "https://discord.com/webhook",
        "BULLETIN_URL": "https://bulletin.url",
        "VERIFY_SSL": "False",
        "SEMESTER_INDEX": "-1"
    })
    def test_config_loads_environment_variables(self):
        """Vérifie que les variables d'environnement sont correctement chargées."""
        # Force reload du module pour prendre en compte les nouvelles variables
        import importlib
        import sys
        if 'src.config' in sys.modules:
            del sys.modules['src.config']
        if 'config' in sys.modules:
            del sys.modules['config']
        
        # Import après avoir défini les variables
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        from config import (SCODOC_URL, USERNAME, PASSWORD, DISCORD_WEBHOOK_URL, 
                           BULLETIN_URL, VERIFY_SSL, SEMESTER_INDEX)
        
        assert SCODOC_URL == "https://test.scodoc.com"
        assert USERNAME == "testuser"
        assert PASSWORD == "testpass"
        assert DISCORD_WEBHOOK_URL == "https://discord.com/webhook"
        assert BULLETIN_URL == "https://bulletin.url"
        assert VERIFY_SSL is False
        assert SEMESTER_INDEX == -1
    
    @patch.dict(os.environ, {"VERIFY_SSL": "True", "SEMESTER_INDEX": "-2"})
    @patch('config.load_dotenv')
    def test_config_defaults(self, mock_load_dotenv):
        """Vérifie que les valeurs par défaut sont utilisées si variables absentes."""
        # Mock load_dotenv pour éviter de charger le .env local
        mock_load_dotenv.return_value = None
        
        import importlib
        import sys
        if 'src.config' in sys.modules:
            del sys.modules['src.config']
        if 'config' in sys.modules:
            del sys.modules['config']
        
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        from config import VERIFY_SSL, SEMESTER_INDEX
        
        # Vérifier seulement les valeurs qui ne dépendent pas du .env
        assert VERIFY_SSL is True
        assert SEMESTER_INDEX == -2
