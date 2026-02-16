import socket
import xmlrpc.client


class OdooAPI:
    def __init__(self, url, db, login, api_key):
        self.url = url.rstrip('/')
        self.db = db
        self.login = login
        self.api_key = api_key
        self.uid = None
        self._models = None

    def authenticate(self):
        try:
            common = xmlrpc.client.ServerProxy(
                f'{self.url}/xmlrpc/2/common', allow_none=True
            )
            self.uid = common.authenticate(self.db, self.login, self.api_key, {})
        except socket.gaierror:
            raise Exception(f'Cannot resolve hostname. Check your Odoo URL.')
        except ConnectionRefusedError:
            raise Exception(f'Connection refused. Check your Odoo URL and port.')
        except xmlrpc.client.ProtocolError as e:
            if e.errcode == 404:
                raise Exception(f'Database "{self.db}" not found. Check your database name and URL.')
            raise Exception(f'Could not connect (HTTP {e.errcode}). Check your URL and database name.')
        except xmlrpc.client.Fault as e:
            msg = str(e.faultString)
            if 'does not exist' in msg:
                raise Exception(f'Database "{self.db}" does not exist. Check your database name.')
            if 'Access Denied' in msg or 'access denied' in msg.lower():
                raise Exception('Access denied. Check your login and API key.')
            raise Exception(f'Server error: {msg[:200]}')
        except OSError as e:
            raise Exception(f'Cannot connect to server. Check your URL. ({e})')
        except Exception as e:
            if 'SSL' in str(type(e).__name__) or 'ssl' in str(e).lower():
                raise Exception('SSL error. Try using https:// instead of http:// (or vice versa).')
            raise Exception(f'Connection failed: {str(e)[:200]}')

        if not self.uid:
            raise Exception('Login failed. Check your email/login and API key.')
        self._models = xmlrpc.client.ServerProxy(
            f'{self.url}/xmlrpc/2/object', allow_none=True
        )
        return self.uid

    def create(self, model, vals):
        """vals can be a dict (single) or list of dicts (batch)."""
        result = self._models.execute_kw(
            self.db, self.uid, self.api_key, model, 'create', [vals]
        )
        return result

    def search(self, model, domain, limit=0, context=None):
        kwargs = {}
        if limit:
            kwargs['limit'] = limit
        if context:
            kwargs['context'] = context
        return self._models.execute_kw(
            self.db, self.uid, self.api_key, model, 'search', [domain], kwargs
        )

    def search_read(self, model, domain, fields, limit=0):
        kwargs = {'fields': fields}
        if limit:
            kwargs['limit'] = limit
        return self._models.execute_kw(
            self.db, self.uid, self.api_key, model, 'search_read', [domain], kwargs
        )

    def read(self, model, ids, fields):
        return self._models.execute_kw(
            self.db, self.uid, self.api_key, model, 'read', [ids], {'fields': fields}
        )

    def write(self, model, ids, vals):
        return self._models.execute_kw(
            self.db, self.uid, self.api_key, model, 'write', [ids, vals]
        )

    def api_call(self, model, method, args, kwargs=None):
        return self._models.execute_kw(
            self.db, self.uid, self.api_key, model, method, args, kwargs or {}
        )
