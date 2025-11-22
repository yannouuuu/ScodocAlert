from cas_client import CASClient
from bs4 import BeautifulSoup
import urllib.parse

class GatewayClient:
    def __init__(self, gateway_url, username, password, verify_ssl=True):
        self.gateway_url = gateway_url.rstrip('/')
        self.cas_client = CASClient(gateway_url, username, password, verify_ssl=verify_ssl)
        self.session = self.cas_client.session

    def login(self):
        # The gateway requires hitting doAuth.php to start the session/CAS flow
        return self.cas_client.login(trigger_path="/services/doAuth.php")

    def get_initial_data(self):
        """
        Fetches the initial data (semesters, auth status) from the gateway.
        Corresponds to 'dataPremièreConnexion'.
        """
        url = f"{self.gateway_url}/services/data.php?q=dataPremièreConnexion"
        # The JS uses POST, so we should too.
        response = self.session.post(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch initial data: {response.status_code}")
        return response.json()

    def get_grades(self, semester_id):
        """
        Fetches the grades for a specific semester.
        Corresponds to 'relevéEtudiant&semestre=...'.
        """
        url = f"{self.gateway_url}/services/data.php?q=relevéEtudiant&semestre={semester_id}"
        response = self.session.post(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch grades: {response.status_code}")
        return response.json()
