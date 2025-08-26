import os
import requests
import random
import string
from typing import List, Dict, Optional

from authentication_client import AuthenticationClient

class ProductClient:
    """
    Cliente para operar CRUD sobre productos en Roble,
    con manejo automático de refresh en 401.
    """
    def __init__(self, base_url: str, contract: str, auth_client: AuthenticationClient):
        self.database_url = f"{base_url}/database/{contract}".rstrip('/')
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
        url = f"{self.database_url}/read"
        resp = self._request('GET', url, params={'tableName': self.table})
        products = resp.json()
        print(f"Encontrados {len(products)} productos.")
        return products

    def add_product(self, product: Dict) -> bool:
        url = f"{self.database_url}/insert"
        resp = self._request('POST', url, json={'tableName': self.table, 'records': [product]})
        print(f"Producto '{product.get('name')}' agregado.")
        return True

    def update_product(self, product_id: str, updates: Dict) -> bool:
        url = f"{self.database_url}/update"
        body = {'tableName': self.table, 'idColumn': '_id', 'idValue': product_id, 'updates': updates}
        resp = self._request('PUT', url, json=body)
        print(f"Producto con ID {product_id} actualizado.")
        return True

    def delete_product(self, product_id: str) -> bool:
        url = f"{self.database_url}/delete"
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