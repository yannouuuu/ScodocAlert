import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gateway_client import GatewayClient


class TestGatewayClient:
    """Tests pour le module gateway_client."""
    
    @patch('gateway_client.CASClient')
    def test_initialization(self, mock_cas_client):
        """Vérifie l'initialisation du client gateway."""
        mock_cas_instance = Mock()
        mock_cas_instance.session = Mock()
        mock_cas_client.return_value = mock_cas_instance
        
        client = GatewayClient("https://gateway.test.com", "user", "pass", verify_ssl=False)
        
        assert client.gateway_url == "https://gateway.test.com"
        assert client.cas_client == mock_cas_instance
        assert client.session == mock_cas_instance.session
    
    @patch('gateway_client.CASClient')
    def test_url_normalization(self, mock_cas_client):
        """Vérifie que l'URL est normalisée."""
        mock_cas_instance = Mock()
        mock_cas_instance.session = Mock()
        mock_cas_client.return_value = mock_cas_instance
        
        client = GatewayClient("https://gateway.test.com/", "user", "pass")
        
        assert client.gateway_url == "https://gateway.test.com"
    
    @patch('gateway_client.CASClient')
    def test_login(self, mock_cas_client):
        """Vérifie que login appelle CASClient.login avec le bon path."""
        mock_cas_instance = Mock()
        mock_cas_instance.login = Mock(return_value=True)
        mock_cas_client.return_value = mock_cas_instance
        
        client = GatewayClient("https://gateway.test.com", "user", "pass")
        result = client.login()
        
        assert result is True
        mock_cas_instance.login.assert_called_once_with(trigger_path="/services/doAuth.php")
    
    @patch('gateway_client.CASClient')
    def test_get_initial_data_success(self, mock_cas_client):
        """Vérifie la récupération des données initiales."""
        mock_cas_instance = Mock()
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "semestres": [
                {"formsemestre_id": 1, "titre": "S1"},
                {"formsemestre_id": 2, "titre": "S2"}
            ]
        }
        mock_session.post.return_value = mock_response
        mock_cas_instance.session = mock_session
        mock_cas_client.return_value = mock_cas_instance
        
        client = GatewayClient("https://gateway.test.com", "user", "pass")
        data = client.get_initial_data()
        
        assert "semestres" in data
        assert len(data["semestres"]) == 2
        mock_session.post.assert_called_once_with(
            "https://gateway.test.com/services/data.php?q=dataPremièreConnexion"
        )
    
    @patch('gateway_client.CASClient')
    def test_get_initial_data_failure(self, mock_cas_client):
        """Vérifie la gestion d'erreur lors de la récupération des données."""
        mock_cas_instance = Mock()
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_session.post.return_value = mock_response
        mock_cas_instance.session = mock_session
        mock_cas_client.return_value = mock_cas_instance
        
        client = GatewayClient("https://gateway.test.com", "user", "pass")
        
        with pytest.raises(Exception, match="Failed to fetch initial data"):
            client.get_initial_data()
    
    @patch('gateway_client.CASClient')
    def test_get_grades_success(self, mock_cas_client):
        """Vérifie la récupération des notes pour un semestre."""
        mock_cas_instance = Mock()
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "relevé": {
                "ressources": {
                    "R1.01": {
                        "titre": "Initiation au développement",
                        "evaluations": []
                    }
                }
            }
        }
        mock_session.post.return_value = mock_response
        mock_cas_instance.session = mock_session
        mock_cas_client.return_value = mock_cas_instance
        
        client = GatewayClient("https://gateway.test.com", "user", "pass")
        data = client.get_grades(123)
        
        assert "relevé" in data
        assert "ressources" in data["relevé"]
        mock_session.post.assert_called_once_with(
            "https://gateway.test.com/services/data.php?q=relevéEtudiant&semestre=123"
        )
    
    @patch('gateway_client.CASClient')
    def test_get_grades_failure(self, mock_cas_client):
        """Vérifie la gestion d'erreur lors de la récupération des notes."""
        mock_cas_instance = Mock()
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_session.post.return_value = mock_response
        mock_cas_instance.session = mock_session
        mock_cas_client.return_value = mock_cas_instance
        
        client = GatewayClient("https://gateway.test.com", "user", "pass")
        
        with pytest.raises(Exception, match="Failed to fetch grades"):
            client.get_grades(123)

