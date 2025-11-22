import requests
from bs4 import BeautifulSoup
import urllib.parse

class CASClient:
    def __init__(self, scodoc_url, username, password, verify_ssl=True):
        self.scodoc_url = scodoc_url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def login(self, trigger_path="/auth/login"):
        """
        Performs the CAS login flow.
        1. Access a protected ScoDoc URL to trigger redirect to CAS.
        2. Parse the CAS login form (execution, lt, etc.).
        3. Submit credentials.
        4. Follow redirects back to ScoDoc.
        """
        # 1. Trigger redirect
        # Use the explicit login URL which should redirect to CAS
        target_url = f"{self.scodoc_url}{trigger_path}"
        print(f"Accessing {target_url} to trigger CAS...")
        response = self.session.get(target_url)
        
        if response.status_code == 404:
            print(f"Error: Target URL {target_url} returned 404. Check SCODOC_URL.")
            return False

        if "cas" not in response.url and "login" not in response.url:
            print(f"No CAS redirect detected.")
            print(f"URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            # print(f"Headers: {response.headers}") # Debug
            
            # Check if we are actually on ScoDoc (look for specific headers or content)
            if response.status_code == 200:
                 print("It seems we are already authenticated.")
                 return True
            return False

        cas_login_url = response.url
        print(f"Redirected to CAS: {cas_login_url}")

        # 2. Parse form
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', id='fm1') # Standard CAS form ID, might vary
        if not form:
            # Fallback for other CAS templates
            form = soup.find('form')
        
        if not form:
            raise Exception("Could not find login form on CAS page.")

        payload = {}
        for input_tag in form.find_all('input'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            if name:
                payload[name] = value

        payload['username'] = self.username
        payload['password'] = self.password
        
        # Some CAS implementations use 'submit' name for the button
        if 'submit' not in payload:
             payload['submit'] = 'SE CONNECTER' # Common default, might need adjustment

        action = form.get('action')
        if not action:
            post_url = cas_login_url
        elif action.startswith('http'):
            post_url = action
        else:
            parsed_url = urllib.parse.urlparse(cas_login_url)
            post_url = urllib.parse.urljoin(f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}", action)

        print(f"Submitting credentials to {post_url}...")
        
        # 3. Submit credentials
        # Important: Referer header is often checked
        self.session.headers.update({'Referer': cas_login_url})
        post_response = self.session.post(post_url, data=payload)

        # 4. Check result
        if "TGC" in self.session.cookies or "scodoc_session" in self.session.cookies:
             print("Login successful (Cookies found).")
             return True
        
        # Check if we are redirected back to service
        if self.scodoc_url in post_response.url:
            print("Login successful (Redirected back to service).")
            return True

        # Debug failure
        if "erreur" in post_response.text.lower() or "error" in post_response.text.lower() or "échec" in post_response.text.lower():
            print("Login failed: Error message found in response.")
            # print(post_response.text[:500]) # Debug
            return False
            
        print("Login status uncertain. Final URL:", post_response.url)
        return True # Optimistic return, API calls will fail if not actually logged in

    def get_session(self):
        return self.session
