import hashlib
import random

import unittest

from chisel import settings
from chisel import models
from fs.opener import opener

def random_hash(length=40):
    return ''.join(random.choice('') for i in range(length))

def random_bytes(size=20):
    return ''.join(chr(random.randint(0, 255)) for i in range(size))

hash_digits = '0123456789abcdef'
twenty_bytes = 'A'*20
sha1_hexdigest = ''.join(hash_digits[i % 16] for i in range(40))

def hex_hash_int(i):
    return hashlib.sha1(str(i)).hexdigest()

def bytes_hash_int(i):
    return hashlib.sha1(str(i)).digest()

class TestScroll(unittest.TestCase):
    def test_save_scroll(self):
        item_hash = twenty_bytes
        scroll_id = sha1_hexdigest
        pyfs = opener.opendir(settings.config['fs_path'])
        scroll = models.Scroll(pyfs, scroll_id)
        scroll.add(item_hash)
        self.assertTrue(scroll.has(item_hash))
        scroll.save()
        contents = pyfs.getcontents(scroll_id + '.scroll')
        self.assertEqual(contents, item_hash)

    def test_load_scroll(self):
        item_hash = twenty_bytes
        scroll_id = sha1_hexdigest
        pyfs = opener.opendir(settings.config['fs_path'])

        with open(scroll_id + '.scroll', 'w+') as f:
            f.write(item_hash)

        scroll = models.Scroll(pyfs, scroll_id)
        scroll.load()
        self.assertTrue(scroll.has(item_hash))
 
    def test_save_big_scroll(self):
        pyfs = opener.opendir(settings.config['fs_path'])
        scroll_id = sha1_hexdigest
        scroll = models.Scroll(pyfs, scroll_id)

        items = []
        for i in range(100):
            item_hash = bytes_hash_int(i)
            scroll.add(item_hash)
            items.append(item_hash)

        for item_hash in items:
            self.assertTrue(scroll.has(item_hash))

        scroll.save()
        contents = pyfs.getcontents(scroll_id + '.scroll')
        self.assertEqual(contents, ''.join(items))

    def test_slice(self):
        pyfs = opener.opendir(settings.config['fs_path'])
        scroll_id = sha1_hexdigest
        scroll = models.Scroll(pyfs, scroll_id)
        
        items = []
        for i in range(10):
            item_hash = bytes_hash_int(i)
            scroll.add(item_hash)
            items.append(item_hash)
        
        four, five = scroll.slice(4, 2)
        self.assertEqual(four, bytes_hash_int(4))
        self.assertEqual(five, bytes_hash_int(5))
