import os
import requests
import random
import string
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()  # Carga variables de entorno desde .env

class AuthenticationClient:
    """
    Cliente para autenticar usando el servicio de Roble.
    """
    def __init__(self, auth_url: str):
        self.auth_url = auth_url.rstrip('/')
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
        print("URL de signup:", url)
        new_email = input("Email del nuevo usuario: ")
        new_password = input("Password del nuevo usuario: ")
        nombre = input("Nombre del nuevo usuario: ")
        header = {'Content-Type': 'application/json'}
        resp = requests.post(url, json={'email': new_email, 'password': new_password, 'name': nombre}, headers=header)
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

class ProductClient:
    """
    Cliente para operar CRUD sobre productos en Roble,
    con manejo automático de refresh en 401.
    """
    def __init__(self, base_host: str, contract: str, auth_client: AuthenticationClient):
        self.base_host = base_host.rstrip('/')
        self.contract = contract
        self.auth_client = auth_client
        self.session = auth_client.session
        self.table = 'Product'

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        resp = self.session.request(method, url, **kwargs)
        if resp.status_code == 401:
            print("401 detectado, intentando renovar token...")
            if self.auth_client.refresh():
                resp = self.session.request(method, url, **kwargs)
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            print(f"Request error {resp.status_code}: {resp.text}")
            raise
        return resp

    def get_products(self) -> List[Dict]:
        url = f"https://{self.base_host}/database/{self.contract}/read"
        resp = self._request('GET', url, params={'tableName': self.table})
        products = resp.json()
        print(f"Encontrados {len(products)} productos.")
        return products

    def add_product(self, product: Dict) -> bool:
        url = f"https://{self.base_host}/database/{self.contract}/insert"
        resp = self._request('POST', url, json={'tableName': self.table, 'records': [product]})
        print(f"Producto '{product.get('name')}' agregado.")
        return True

    def update_product(self, product_id: str, updates: Dict) -> bool:
        url = f"https://{self.base_host}/database/{self.contract}/update"
        body = {'tableName': self.table, 'idColumn': '_id', 'idValue': product_id, 'updates': updates}
        resp = self._request('PUT', url, json=body)
        print(f"Producto con ID {product_id} actualizado.")
        return True

    def delete_product(self, product_id: str) -> bool:
        url = f"https://{self.base_host}/database/{self.contract}/delete"
        body = {'tableName': self.table, 'idColumn': '_id', 'idValue': product_id}
        resp = self._request('DELETE', url, json=body)
        print(f"Producto con ID {product_id} eliminado.")
        return True

    def delete_all_products(self) -> None:
        products = self.get_products()
        for p in products:
            pid = p.get('_id')
            if pid:
                self.delete_product(pid)
        print("Todos los productos han sido eliminados.")

    def add_random_products(self, n: int = 30) -> List[str]:
        added_names = []
        for _ in range(n):
            name = 'Producto-' + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            description = 'Descripción ' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            quantity = random.randint(1, 100)
            product = {'name': name, 'description': description, 'quantity': quantity}
            self.add_product(product)
            added_names.append(name)
        print(f"{n} productos aleatorios agregados.")
        return added_names


def main():
    # Variables desde .env
    auth_url = os.getenv('ROBLE_AUTH_URL')
    base_host = os.getenv('ROBLE_BASE_HOST')
    contract = os.getenv('ROBLE_CONTRACT')

    if not all([auth_url, base_host, contract]):
        print("Define ROBLE_AUTH_URL, ROBLE_BASE_HOST y ROBLE_CONTRACT en el .env")
        return

    auth_client = AuthenticationClient(auth_url)
    product_client = ProductClient(base_host, contract, auth_client)

    while True:
        print("\n=== Menú Roble Client ===")
        print("1. Login")
        print("2. Logout")
        print("3. Crear usuario")
        print("4. Mostrar tokens actuales")
        print("5. Renovar token")

        print("6. Listar productos")
        print("7. Agregar producto manual")
        print("8. Actualizar producto")
        print("9. Eliminar producto")
        print("10. Eliminar todos los productos")
        print("11. Agregar 30 productos aleatorios")

        print("12. Salir")
        choice = input("Selecciona una opción: ")

        try:
            if choice == '1':
                auth_client.login()
            elif choice == '2':
                auth_client.logout()
            elif choice == '3':
                auth_client.signup()  
            elif choice == '4':
                auth_client.show_tokens()
            elif choice == '5':
                auth_client.refresh()

            # elif choice == '3':
            #     products = product_client.get_products()
            #     for p in products:
            #         print(p)
            # elif choice == '4':
            #     name = input("Nombre: ")
            #     desc = input("Descripción: ")
            #     qty = int(input("Cantidad: "))
            #     product_client.add_product({'name': name, 'description': desc, 'quantity': qty})
            # elif choice == '5':
            #     pid = input("ID del producto a actualizar: ")
            #     key = input("Campo a actualizar (name/description/quantity): ")
            #     val = input("Nuevo valor: ")
            #     updates = {key: int(val) if key == 'quantity' else val}
            #     product_client.update_product(pid, updates)
            # elif choice == '6':
            #     pid = input("ID del producto a eliminar: ")
            #     product_client.delete_product(pid)
            # elif choice == '7':
            #     confirm = input("¿Seguro? Esto eliminará TODOS los productos (s/n): ")
            #     if confirm.lower() == 's':
            #         product_client.delete_all_products()
            # elif choice == '8':
            #     product_client.add_random_products(30)

            elif choice == '12':
                print("Saliendo...")
                break
            else:
                print("Opción no válida.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
