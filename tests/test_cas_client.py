import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cas_client import CASClient


class TestCASClient:
    """Tests pour le module cas_client."""
    
    def test_initialization(self):
        """Vérifie l'initialisation du client CAS."""
        client = CASClient("https://scodoc.test.com", "user", "pass", verify_ssl=False)
        
        assert client.scodoc_url == "https://scodoc.test.com"
        assert client.username == "user"
        assert client.password == "pass"
        assert client.verify_ssl is False
        assert client.session is not None
    
    def test_url_normalization(self):
        """Vérifie que l'URL est normalisée (sans slash final)."""
        client = CASClient("https://scodoc.test.com/", "user", "pass")
        
        assert client.scodoc_url == "https://scodoc.test.com"
    
    @patch('cas_client.requests.Session')
    def test_session_headers(self, mock_session_class):
        """Vérifie que les headers sont correctement configurés."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        client = CASClient("https://scodoc.test.com", "user", "pass")
        
        # Vérifier que update a été appelé avec User-Agent
        calls = mock_session.headers.update.call_args_list
        assert any('User-Agent' in str(call) for call in calls)
    
    @patch('cas_client.requests.Session.get')
    def test_login_already_authenticated(self, mock_get):
        """Vérifie le cas où l'utilisateur est déjà authentifié."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://scodoc.test.com/some/page"
        mock_response.text = "Welcome"
        mock_get.return_value = mock_response
        
        client = CASClient("https://scodoc.test.com", "user", "pass")
        result = client.login()
        
        assert result is True
    
    @patch('cas_client.requests.Session.get')
    def test_login_404_error(self, mock_get):
        """Vérifie la gestion d'une erreur 404."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        client = CASClient("https://scodoc.test.com", "user", "pass")
        result = client.login()
        
        assert result is False
    
    @patch('cas_client.requests.Session.post')
    @patch('cas_client.requests.Session.get')
    def test_login_successful_with_cas(self, mock_get, mock_post):
        """Vérifie le login réussi avec redirection CAS."""
        # Mock de la redirection vers CAS
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.url = "https://cas.test.com/login?service=..."
        mock_get_response.text = '''
        <form id="fm1" action="/cas/login">
            <input name="execution" value="e1s1" />
            <input name="username" />
            <input name="password" />
        </form>
        '''
        mock_get.return_value = mock_get_response
        
        # Mock de la réponse POST (soumission du formulaire)
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.url = "https://scodoc.test.com/authenticated"
        mock_post_response.text = "Success"
        mock_post.return_value = mock_post_response
        
        client = CASClient("https://scodoc.test.com", "user", "pass")
        result = client.login()
        
        assert result is True
        assert mock_post.called
    
    @patch('cas_client.requests.Session.post')
    @patch('cas_client.requests.Session.get')
    def test_login_with_cookies(self, mock_get, mock_post):
        """Vérifie la détection de login réussi via cookies."""
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.url = "https://cas.test.com/login"
        mock_get_response.text = '<form id="fm1"><input name="username"/><input name="password"/></form>'
        mock_get.return_value = mock_get_response
        
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.url = "https://cas.test.com/success"
        mock_post.return_value = mock_post_response
        
        client = CASClient("https://scodoc.test.com", "user", "pass")
        client.session.cookies = {"TGC": "some_ticket"}
        
        result = client.login()
        
        assert result is True
    
    def test_get_session(self):
        """Vérifie que get_session retourne la session."""
        client = CASClient("https://scodoc.test.com", "user", "pass")
        session = client.get_session()
        
        assert session is not None
        assert session == client.session

    @patch('cas_client.requests.Session.post')
    @patch('cas_client.requests.Session.get')
    def test_login_extracts_cas_error_message(self, mock_get, mock_post):
        """Vérifie qu'un vrai message d'erreur CAS est détecté."""
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.url = "https://cas.test.com/login"
        mock_get_response.text = '<form id="fm1"><input name="username"/><input name="password"/></form>'
        mock_get.return_value = mock_get_response

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.url = "https://cas.test.com/login"
        mock_post_response.text = '''
        <html>
            <body>
                <div class="alert alert-danger">Identifiants invalides.</div>
                <form id="fm1"></form>
            </body>
        </html>
        '''
        mock_post.return_value = mock_post_response

        client = CASClient("https://scodoc.test.com", "user", "pass")
        result = client.login()

        assert result is False

    @patch('cas_client.requests.Session.post')
    @patch('cas_client.requests.Session.get')
    def test_login_does_not_fail_on_generic_error_word(self, mock_get, mock_post):
        """Vérifie qu'un mot générique comme 'error' ne provoque pas un faux négatif."""
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.url = "https://cas.test.com/login?service=..."
        mock_get_response.text = '''
        <form id="fm1" action="/cas/login">
            <input name="execution" value="e1s1" />
            <input name="username" />
            <input name="password" />
        </form>
        '''
        mock_get.return_value = mock_get_response

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.url = "https://scodoc.test.com/authenticated"
        mock_post_response.text = '<script>const errorLevel = "none";</script>'
        mock_post.return_value = mock_post_response

        client = CASClient("https://scodoc.test.com", "user", "pass")
        result = client.login()

        assert result is True
