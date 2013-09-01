from chisel import settings
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
        self._pyfs = pyfs
        self.id = scroll_id
        self._data_set = set()
        self._data_list = []
        self.state = scroll_id
        # XXX this is a blocking call
        self._fh = self._pyfs.open("%s.scroll" % scroll_id, 'a+')
    
    @property
    def serial_number(self):
        return len(self._data_list)

    def load(self):
        scroll_content = self._pyfs.getcontents("%s.scroll" % self.id)
        value_size = self.policy['value-size']
        assert len(scroll_content) % value_size == 0
        for i in range(len(scroll_content)/value_size):
            item_hash = scroll_content[value_size*i:value_size*(i+1)]
            self._data_set.add(item_hash)
            self._data_list.append(item_hash)

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
    
    def add(self, item_hash):
        """
        Adds an entry to the scroll if it isn't already present.
        """
        if item_hash not in self._data_set:
            assert self.policy['go-hard']

            self._fh.write(item_hash)
            self._fh.flush()

            self._data_set.add(item_hash)
            self._data_list.append(item_hash)

            self.state = settings.HASH(self.state + item_hash)
        else:
            raise e.ObjectAlreadyInPool

class LocalScroll(Scroll):
    pass

class RemoteScroll(Scroll):
    pass


