import base64
import hashlib
import json
from pathlib import Path
from random import randint

import tomllib
import websocket


class ObsClient(object):
    def __init__(self, host=None, port=None, password=None):
        self.host = host
        self.port = port
        self.password = password
        if not (self.host and self.port and self.password):
            conn = self._conn_from_toml()
            self.host = conn["host"]
            self.port = conn["port"]
            self.password = conn["password"]
        self.ws = websocket.WebSocket()
        self.ws.connect(f"ws://{self.host}:{self.port}")
        self.server_hello = json.loads(self.ws.recv())

    def _conn_from_toml(self):
        filepath = Path.cwd() / "config.toml"
        self._conn = dict()
        with open(filepath, "rb") as f:
            self._conn = tomllib.load(f)
        return self._conn["connection"]

    def authenticate(self):
        secret = base64.b64encode(
            hashlib.sha256(
                (
                    self.password + self.server_hello["d"]["authentication"]["salt"]
                ).encode()
            ).digest()
        )

        auth = base64.b64encode(
            hashlib.sha256(
                (
                    secret.decode()
                    + self.server_hello["d"]["authentication"]["challenge"]
                ).encode()
            ).digest()
        ).decode()

        payload = {"op": 1, "d": {"rpcVersion": 1, "authentication": auth}}

        self.ws.send(json.dumps(payload))
        return self.ws.recv()

    def req(self, req_type, req_data=None):
        if req_data:
            payload = {
                "op": 6,
                "d": {
                    "requestType": req_type,
                    "requestId": randint(1, 1000),
                    "requestData": req_data,
                },
            }
        else:
            payload = {
                "op": 6,
                "d": {"requestType": req_type, "requestId": randint(1, 1000)},
            }
        self.ws.send(json.dumps(payload))
        return json.loads(self.ws.recv())
