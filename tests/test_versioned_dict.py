# -*- coding: utf-8 -*-

# Copyright (C) 2015 ibu@radempa.de
#
# Permission is hereby granted, free of charge, to
# any person obtaining a copy of this software and
# associated documentation files (the "Software"),
# to deal in the Software without restriction,
# including without limitation the rights to use,
# copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is
# furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission
# notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY
# OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Unit tests for :mod:`versioned_dict`.
"""

import unittest
from versioned_dict import *


class TestVersionedDict(unittest.TestCase):

    """
    Test VersionedDict
    """

    def test_init(self):
        d = VersionedDict({'a': 5}, b=2)
        self.assertEqual(d, {'a': 5, 'b': 2})
        self.assertEqual(d.version_number, 0)
        self.assertEqual(dict(a=5, b=2), d.lookup_version(0))

    def test_update_current(self):
        d = VersionedDict({'a': 1}, b=2)
        d['c'] = 3
        d.update({'d': 4})
        del d['a']
        self.assertEqual(d, dict(b=2, c=3, d=4))
        self.assertFalse(d.version_number_valid(-1))
        self.assertTrue(d.version_number_valid(0))
        self.assertFalse(d.version_number_valid(1))
        self.assertEqual(dict(b=2, c=3, d=4), d.lookup_version(0))

    def test_forward(self):
        d = VersionedDict(dict(a=1))
        self.assertEqual(0, d.version_number)
        self.assertEqual(1, d.forward_version())
        self.assertEqual(d, dict(a=1))
        self.assertEqual(1, d.version_number)
        d['a'] = 2
        d['b'] = 2
        self.assertEqual(d, dict(a=2, b=2))
        self.assertEqual(1, d.version_number)
        self.assertEqual(2, d.forward_version())
        self.assertEqual(d, dict(a=2, b=2))
        self.assertEqual(2, d.version_number)
        self.assertEqual({'a', 'b'}, d.keys_in_version(version_n=2))
        self.assertEqual(dict(a=1), d.lookup_version(0))
        self.assertEqual(dict(a=2, b=2), d.lookup_version(1))
        self.assertEqual(dict(a=2, b=2), d.lookup_version(2))
        d['c'] = 3
        del d['a']
        d['b'] = 1
        self.assertEqual(d, dict(b=1, c=3))
        self.assertEqual(3, d.forward_version())
        self.assertEqual(d, dict(b=1, c=3))
        self.assertEqual(3, d.version_number)
        d['i'] = 9
        del d['c']
        d['b'] = 2
        self.assertEqual(d, dict(b=2, i=9))
        self.assertEqual((dict(i=9), dict(c=3), dict(b=2)), d.diff_previous())
        self.assertEqual((dict(c=3), dict(a=2), dict(b=1)), d.diff_previous(3))
        self.assertEqual((dict(b=2), dict(), dict(a=2)), d.diff_previous(2))
        self.assertEqual((dict(a=1), dict(), dict()), d.diff_previous(1))
        self.assertEqual((dict(), dict(), dict()), d.diff_previous(0))
        self.assertEqual((dict(c=3), dict(a=2), dict(b=1)),
                         d.diff_pair(1, 2))
        self.assertEqual((dict(c=3, b=1), dict(a=1), dict()),
                         d.diff_pair(0, 2))
        self.assertEqual((dict(i=9, b=2), dict(a=1), dict()),
                         d.diff_pair(0, 3))
        self.assertEqual((dict(i=9), dict(c=3), dict(b=2)),
                         d.diff_pair(2, 3))

    def test_rewind(self):
        d = VersionedDict(dict(a=1))
        self.assertEqual(0, d.version_number)
        self.assertEqual(1, d.forward_version())
        self.assertEqual({'a'}, d.keys_in_version(version_n=0))
        self.assertEqual(1, d.lookup_value('a', version_n=0))
        self.assertEqual(1, d.lookup_value('a'))
        self.assertEqual(d, dict(a=1))
        self.assertEqual(1, d.version_number)
        d['a'] = 5
        self.assertEqual(1, d.lookup_value('a', version_n=0))
        self.assertEqual(5, d.lookup_value('a'))
        d['b'] = 2
        self.assertEqual(d, dict(a=5, b=2))
        self.assertEqual(1, d.version_number)
        self.assertEqual(2, d.forward_version())
        self.assertEqual({'a'}, d.keys_in_version(version_n=0))
        self.assertEqual({'a', 'b'}, d.keys_in_version(version_n=1))
        self.assertEqual(d, dict(a=5, b=2))
        self.assertEqual(2, d.version_number)
        d['c'] = 3
        del d['a']
        self.assertEqual(3, d.forward_version())
        self.assertEqual(d, dict(b=2, c=3))
        self.assertEqual(3, d.version_number)
        d['i'] = 9
        self.assertEqual(d, dict(b=2, c=3, i=9))
        self.assertEqual(2, d.rewind_version())
        self.assertEqual(d, dict(b=2, c=3))
        self.assertEqual(2, d.version_number)
        self.assertEqual(1, d.rewind_version())
        self.assertEqual(d, dict(a=5, b=2))
        self.assertEqual(1, d.version_number)
        self.assertEqual(0, d.rewind_version())
        self.assertEqual(d, dict(a=1))
        self.assertEqual(0, d.version_number)
        with self.assertRaises(VersionedDictRewindError):
            d.rewind_version()

    def test_empty_dict(self):
        d = VersionedDict()
        self.assertEqual({}, d)
        self.assertEqual(1, d.forward_version())
        self.assertEqual({}, d)
        self.assertEqual(2, d.forward_version())
        self.assertEqual({}, d)
        self.assertEqual(1, d.rewind_version())
        self.assertEqual({}, d)
        self.assertEqual(0, d.rewind_version())
        self.assertEqual({}, d)

    def test_lookup_version(self):
        d = VersionedDict()
        d.forward_version()
        d.update(dict(m=1, r=1, s=2, t=3, u=4))
        d.forward_version()
        d['a'] = 1
        del d['r']
        d['m'] = 2
        d.forward_version()
        d['b'] = 2
        del d['s']
        d['m'] = 3
        d.forward_version()
        d['c'] = 3
        del d['t']
        d['m'] = 4
        d.forward_version()
        d['d'] = 4
        del d['u']
        d['m'] = 5
        d.forward_version()
        self.assertEqual(d.lookup_version(0), dict())
        self.assertEqual(d.lookup_version(1), dict(m=1, r=1, s=2, t=3, u=4))
        self.assertEqual(d.lookup_version(2), dict(m=2, a=1, s=2, t=3, u=4))
        self.assertEqual(d.lookup_version(3), dict(m=3, a=1, b=2, t=3, u=4))
        self.assertEqual(d.lookup_version(4), dict(m=4, a=1, b=2, c=3, u=4))
        self.assertEqual(d.lookup_version(5), dict(m=5, a=1, b=2, c=3, d=4))
        self.assertEqual(d.lookup_version(6), dict(m=5, a=1, b=2, c=3, d=4))
        with self.assertRaises(VersionedDictInvalidVersionError):
            d.lookup_version(7)
        with self.assertRaises(VersionedDictInvalidVersionError):
            d.lookup_version(-1)

    def test_deep_copying(self):
        x1 = [(7, 'anything', {'h': 'ha'}), set([1, 2, 3])]
        d = VersionedDict(x1=x1)
        self.assertEqual(x1, d['x1'])
        self.assertEqual(1, d.forward_version())
        self.assertFalse(x1 is d.lookup_version(0)['x1'])
        self.assertTrue(x1 is d['x1'])
        self.assertTrue(x1[0][2] == d.lookup_version(0)['x1'][0][2])
        self.assertTrue(x1[0][2]['h'] == d.lookup_version(0)['x1'][0][2]['h'])
