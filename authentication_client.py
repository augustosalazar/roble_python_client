import requests

class AuthenticationClient:
    """
    Cliente para autenticar usando el servicio de Roble.
    """
    def __init__(self, base_url: str, contract: str):
        self.auth_url = f"{base_url}/auth/{contract}".rstrip('/')
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def login(self) -> bool:
        url = f"{self.auth_url}/login"
        email = input("Email del nuevo usuario: ")
        password = input("Password del nuevo usuario: ")
        resp = self.session.post(url, json={'email': email, 'password': password})
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            print(f"Login error {resp.status_code}: {resp.text}")
            return False
        data = resp.json()
        self.access_token = data.get('accessToken')
        self.refresh_token = data.get('refreshToken')
        self.session.headers.update({'Authorization': f'Bearer {self.access_token}'})
        print("Login exitoso.")
        return True

    def logout(self) -> bool:
        url = f"{self.auth_url}/logout"
        resp = self.session.post(url)
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            print(f"Logout error {resp.status_code}: {resp.text}")
            return False
        self.session.headers.pop('Authorization', None)
        self.access_token = None
        self.refresh_token = None
        print("Logout exitoso.")
        return True

    def signup(self) -> bool:
        url = f"{self.auth_url}/signup-direct"
        new_email = input("Email del nuevo usuario: ")
        new_password = input("Password del nuevo usuario: ")
        nombre = input("Nombre del nuevo usuario: ")
        resp = requests.post(url, json={'email': new_email, 'password': new_password, 'name': nombre})
        if resp.status_code in (200, 201):
            print("Usuario creado exitosamente.")
            return True
        else:
            print(f"Error al crear usuario {resp.status_code}: {resp.text}")
            return False

    def refresh(self) -> bool:
        if not self.refresh_token:
            print("No hay refresh token para renovar.")
            return False
        url = f"{self.auth_url}/refresh-token"
        headers = {'Content-Type': 'application/json'}
        payload = {'refreshToken': self.refresh_token}
        print(f"Enviando refresh-token a {url} con payload: {payload}")
        resp = self.session.post(url, json=payload, headers=headers)
        if resp.status_code not in (200, 201):
            print(f"Error al refrescar token {resp.status_code}: {resp.text}")
            return False
        try:
            data = resp.json()
        except ValueError:
            print(f"Respuesta no es JSON: {resp.text}")
            return False
        self.access_token = data.get('accessToken')
        if not self.access_token:
            print(f"No se recibió accessToken: {data}")
            return False
        self.session.headers.update({'Authorization': f'Bearer {self.access_token}'})
        print("Token renovado exitosamente.")
        return True

    def show_tokens(self) -> None:
        print(f"Access Token: {self.access_token}")
        print(f"Refresh Token: {self.refresh_token}")