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

    def login(self, email: str, password: str) -> bool:
        url = f"{self.auth_url}/login"
        resp = self.session.post(url, json={'email': email, 'password': password})
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data['accessToken']
        self.refresh_token = data['refreshToken']
        self.session.headers.update({'Authorization': f'Bearer {self.access_token}'})
        print("Login exitoso.")
        return True

    def logout(self) -> bool:
        url = f"{self.auth_url}/logout"
        resp = self.session.post(url)
        resp.raise_for_status()
        self.session.headers.pop('Authorization', None)
        self.access_token = None
        self.refresh_token = None
        print("Logout exitoso.")
        return True

    def refresh(self) -> bool:
        url = f"{self.auth_url}/refresh-token"
        headers = {'refreshToken': self.refresh_token}
        resp = self.session.post(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data['accessToken']
        self.session.headers.update({'Authorization': f'Bearer {self.access_token}'})
        print("Token renovado.")
        return True

class ProductClient:
    """
    Cliente para operar CRUD sobre productos en Roble.
    """
    def __init__(self, base_host: str, contract: str, auth_client: AuthenticationClient):
        self.base_host = base_host.rstrip('/')
        self.contract = contract
        self.session = auth_client.session
        self.table = 'Product'

    def get_products(self) -> List[Dict]:
        url = f"https://{self.base_host}/database/{self.contract}/read"
        params = {'tableName': self.table}
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        products = resp.json()
        print(f"Encontrados {len(products)} productos.")
        return products

    def add_product(self, product: Dict) -> bool:
        url = f"https://{self.base_host}/database/{self.contract}/insert"
        body = {'tableName': self.table, 'records': [product]}
        resp = self.session.post(url, json=body)
        resp.raise_for_status()
        print(f"Producto '{product.get('name')}' agregado.")
        return True

    def update_product(self, product_id: str, updates: Dict) -> bool:
        url = f"https://{self.base_host}/database/{self.contract}/update"
        body = {
            'tableName': self.table,
            'idColumn': '_id',
            'idValue': product_id,
            'updates': updates
        }
        resp = self.session.put(url, json=body)
        resp.raise_for_status()
        print(f"Producto con ID {product_id} actualizado.")
        return True

    def delete_product(self, product_id: str) -> bool:
        url = f"https://{self.base_host}/database/{self.contract}/delete"
        body = {'tableName': self.table, 'idColumn': '_id', 'idValue': product_id}
        resp = self.session.delete(url, json=body)
        resp.raise_for_status()
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
    email = os.getenv('ROBLE_EMAIL')
    password = os.getenv('ROBLE_PASSWORD')

    if not all([auth_url, base_host, contract, email, password]):
        print("Por favor, define ROBLE_AUTH_URL, ROBLE_BASE_HOST, ROBLE_CONTRACT, ROBLE_EMAIL y ROBLE_PASSWORD en el .env")
        return

    auth_client = AuthenticationClient(auth_url)
    product_client = ProductClient(base_host, contract, auth_client)

    while True:
        print("\n=== Menú Roble Client ===")
        print("1. Login")
        print("2. Logout")
        print("3. Listar productos")
        print("4. Agregar producto manual")
        print("5. Actualizar producto")
        print("6. Eliminar producto")
        print("7. Eliminar todos los productos")
        print("8. Agregar 30 productos aleatorios")
        print("9. Salir")
        choice = input("Selecciona una opción: ")

        try:
            if choice == '1':
                auth_client.login(email, password)
            elif choice == '2':
                auth_client.logout()
            elif choice == '3':
                products = product_client.get_products()
                for p in products:
                    print(p)
            elif choice == '4':
                name = input("Nombre: ")
                desc = input("Descripción: ")
                qty = int(input("Cantidad: "))
                product_client.add_product({'name': name, 'description': desc, 'quantity': qty})
            elif choice == '5':
                pid = input("ID del producto a actualizar: ")
                key = input("Campo a actualizar (name/description/quantity): ")
                val = input("Nuevo valor: ")
                updates = {key: int(val) if key == 'quantity' else val}
                product_client.update_product(pid, updates)
            elif choice == '6':
                pid = input("ID del producto a eliminar: ")
                product_client.delete_product(pid)
            elif choice == '7':
                confirm = input("¿Seguro? Esto eliminará TODOS los productos (s/n): ")
                if confirm.lower() == 's':
                    product_client.delete_all_products()
            elif choice == '8':
                product_client.add_random_products(30)
            elif choice == '9':
                print("Saliendo...")
                break
            else:
                print("Opción no válida.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
