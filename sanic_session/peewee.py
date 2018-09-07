from sanic_session.base import BaseSessionInterface
from sanic_session.utils import ExpiringDict

try:
    from peewee import *

    database_proxy = Proxy()

    class BaseModel(Model):
        class Meta:
            database = database_proxy

    class _SessionStoreModel(BaseModel):
        key = CharField()
        value = CharField()
        expiry = IntegerField()

except ImportError:
    _SessionStoreModel = None


class PeeweeSessionInterface(BaseSessionInterface):

    def __init__(
            self, db, domain: str=None, expiry: int = 2592000,
            httponly: bool=True, cookie_name: str = 'session',
            prefix: str='session:',
            sessioncookie: bool=False):
        """Initializes the interface for storing client sessions in SQLite3, MariaDB or PostgresSQL via peewee.
        Requires a peewee database object.

        Args:
            db (peewee.Database):
                The peewee database object.
            domain (str, optional):
                Optional domain which will be attached to the cookie.
            expiry (int, optional):
                Seconds until the session should expire.
            httponly (bool, optional):
                Adds the `httponly` flag to the session cookie.
            cookie_name (str, optional):
                Name used for the client cookie.
            prefix (str, optional):
                Memcache keys will take the format of `prefix+session_id`;
                specify the prefix here.
            sessioncookie (bool, optional):
                Specifies if the sent cookie should be a 'session cookie', i.e
                no Expires or Max-age headers are included. Expiry is still
                fully tracked on the server side. Default setting is False.

        """
        if _SessionStoreModel is None:
            msg = "Please install peewee dependencies: pip install sanic_session[peewee]"
            raise RuntimeError(msg)

        database_proxy.initialize(db)
        db.create_tables([_SessionStoreModel])

        self.expiry = expiry
        self.prefix = prefix
        self.cookie_name = cookie_name
        self.domain = domain
        self.httponly = httponly
        self.sessioncookie = sessioncookie

    async def _get_value(self, prefix, sid):
        try:
            val = _SessionStoreModel.get(key=self.prefix + sid).value
            return val
        except:
            return None

    async def _delete_key(self, key):
        try:
            _SessionStoreModel.delete().where(SessionStore.key==key)
        except:
            pass

    async def _set_value(self, key, data):
        _SessionStoreModel.get_or_create(key=key, value=data, expiry=self.expiry)