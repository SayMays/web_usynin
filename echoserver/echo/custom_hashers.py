import hashlib
import base64
import os


class CustomPasswordHasher:
    algorithm = 'custom_sha256'
    iterations = 10000

    def salt(self):
        return base64.b64encode(os.urandom(12)).decode('ascii')

    def encode(self, password, salt=None):
        if salt is None:
            salt = base64.b64encode(os.urandom(12)).decode('ascii')
        assert len(salt) >= 12

        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('ascii')

        hash_value = password_bytes + salt_bytes
        for _ in range(self.iterations):
            hash_value = hashlib.sha256(hash_value).digest()

        hash_encoded = base64.b64encode(hash_value).decode('ascii').strip()
        return f"{self.algorithm}${self.iterations}${salt}${hash_encoded}"

    def verify(self, password, encoded):
        try:
            algorithm, iterations, salt, hash_encoded = encoded.split('$', 3)
            assert algorithm == self.algorithm
            assert int(iterations) == self.iterations
        except (ValueError, AssertionError):
            return False

        computed_hash = self.encode(password, salt)
        return computed_hash == encoded

    def safe_summary(self, encoded):
        algorithm, iterations, salt, _ = encoded.split('$', 3)
        return {
            'algorithm': algorithm,
            'iterations': int(iterations),
            'salt': salt,
            'hash': '[hidden]',
        }

    def must_update(self, encoded):
        _, iterations, _, _ = encoded.split('$', 3)
        return int(iterations) != self.iterations
