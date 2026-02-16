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
        common = xmlrpc.client.ServerProxy(
            f'{self.url}/xmlrpc/2/common', allow_none=True
        )
        self.uid = common.authenticate(self.db, self.login, self.api_key, {})
        if not self.uid:
            raise Exception('Authentication failed. Check your credentials.')
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
