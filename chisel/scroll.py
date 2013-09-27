from twisted.internet import defer

from chisel import settings, crypto
from chisel import errors as e

class Policy(dict):
    pass

class ScrollUpdate(object):
    def __init__(self, content):
        self.content = content

class Scroll(object):
    """
    Ordered set of item hashes.
    """
    def __init__(self, pyfs, scroll_id):
        self.policy = {
            'value-size': 20,
            'signed': True,
            'valid-keys': [],
            'go-hard': True,
        }
        self.pyfs = pyfs
        self.id = scroll_id
        self._data_set = set()
        self._data_list = []
        self.state = scroll_id
        if self.pyfs.isfile( self.scroll_path):
            self._load()
        self._fh = self.pyfs.open(self.scroll_path, 'a+')

    @property 
    def scroll_path(self):
        return "%s.scroll" % self.id

    @property
    def serial_number(self):
        return len(self._data_list)

    def _load(self):
        scroll_content = self.pyfs.getcontents("%s.scroll" % self.id)
        value_size = self.policy['value-size']
        assert len(scroll_content) % value_size == 0
        for i in range(len(scroll_content)/value_size):
            item_hash = scroll_content[value_size*i:value_size*(i+1)]
            self._add(item_hash)

    def __iter__(self):
        for item_hash in self._data_list:
            yield item_hash

    def slice(self, start, limit=1):
        """
        Returns list of items from the scroll.
        """
        return self._data_list[start:start+limit]

    def has(self, item_hash):
        return item_hash in self._data_set
    
    def _write(self, item_hash):
        self._fh.write(item_hash)
        self._fh.flush()

    def _add(self, item_hash):
        self._data_set.add(item_hash)
        self._data_list.append(item_hash)
        self.state = settings.HASH(self.state + item_hash)

    def add(self, item_hash):
        """
        Adds an entry to the scroll if it isn't already present.
        """
        if item_hash not in self._data_set:
            self._write(item_hash)
            self._add(item_hash)
            return True

class SignedScroll(Scroll, crypto.KeyStore):
    def __init__(self, pyfs, scroll_id, fingerprint):
        self.fingerprint = fingerprint
        super(SignedScroll, self).__init__(pyfs, scroll_id)

    @property
    def scroll_path(self):
        self.pyfs.makeopendir(self.id, recursive=True)
        return "%s/%s.scroll" % (self.id, self.fingerprint)

class LocalScroll(SignedScroll):
    def sign_update(self, update):
        signing_key = self.get_signing_key(self.fingerprint)

        signed_update = signing_key.sign(update)
        return signed_update

class RemoteScroll(SignedScroll):
    def verify_update(self, signed_update):
        verify_key = self.get_verify_key(self.fingerprint)

        update = verify_key.verify(signed_update)

        item_hash = update[:20]
        state = update[20:]
        next_state = settings.HASH(self.state + item_hash)
        if state != next_state:
            raise e.InconsistentState

        return update
