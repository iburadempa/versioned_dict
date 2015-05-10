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
A versioned dictionary class derived from :class:`dict`.

This class is useful when subsequent versions of a dictionary frequently
have common key-value pairs which consume quite some memory or would be
time-consuming to deep-copy for each new version.

When 'archiving' a version, only the difference relative to the last stored
version is put on the archive stack (kind of incremental backup):
Added keys and their values, deleted keys and their values and modified keys
and their values are are stored.

Limitations::
  * If rewinding of versions happens very often, this approach
    lacks performance, in particular when there are many versions.
  * When archiving a version, the difference is examined only on the highest
    level: In case of a common key the substructure of the values is not
    examined. (That would somewhat correspond to a differential backup.)
  * When rewinding or looking up a specific archived version, the item
    ordering is usually not preserved (as is not to be expected from a
    :class:`dict`).
  * keys are assumed to objects of type :class:`str`. We do deep-copy keys
    when archiving, but this is not tested.

Example use case: Version 0 of the dictionary has just one key containing the
fulltext of a longer document. Other versions add or delete keys containing
intermediate results in analyzing the document, which may themselves be of
considerable size, but which don't change the document.
"""

from copy import deepcopy


class VersionedDictInvalidVersionError(Exception):

    """
    Error associated with VersionedDict: invalid version requested.

    Occurs when :meth:`VersionedDict.get_version` was called with an
    unavailable version number.
    """

    def __init__(self, versioned_dict, req_ver_n):
        self.versioned_dict = versioned_dict
        self.req_ver_n = req_ver_n

    def __str__(self):
        max_ver_n = self.versioned_dict.version_number()
        if max_ver_n:
            return 'VersionedDict instance has versions up to %i, '\
                   'but no version %i' % (max_ver_n, self.req_ver_n)
        else:
            return 'VersionedDict instance has no versions'


class VersionedDictRewindError(Exception):

    """
    Error associated with VersionedDict: rewind impossible.

    Occurs when version_number equals 0 and thus no previous version
    has been archived.
    """

    def __str__(self):
        return 'VersionedDict rewind impossible'


class VersionedDict(dict):

    """
    A versioned dictionary derived from :class:`dict`.

    Instances of this class behave like a conventional :class:`dict` object.
    In such usage the current version is used without overhead; the archive
    remains unaffected. The current value is affected only by
    :meth:`rewind_version`. Calling :meth:`forward_version` does not affect
    the current version; it just archives a deep copy of it and increments
    the :attr:`version_number`. Initially the :attr:`version_number` equals 0.
    """

    def __init__(self, *args, **kwargs):
        self.__additions = []      # history for added keys
        self.__deletions = []      # history for deleted keys
        self.__modifications = []  # history for changed values
        self.__version = 0
        super().__init__(*args, **kwargs)

    def forward_version(self):
        """
        Create a new version and return its number.

        Take the current version, diff it against the last archived one
        and put the difference on the archive stack, while retaining the
        current value.
        """
        if self.version_number > 0:
            addition, deletion, modification = \
                self.__diff_current_against_latest_archived()
            # archive addition
            self.__additions.append(addition)
            # archive deletion
            self.__deletions.append(deletion)
            # archive modification
            self.__modifications.append(modification)
        else:
            self.__additions.append({deepcopy(key): deepcopy(value)
                                     for key, value in self.items()})
            self.__deletions.append({})
            self.__modifications.append({})
        self.__version += 1
        return self.__version

    def __diff_current_against_latest_archived(self):
        """
        Diff the current version agaionst the latest archived one.

        Return 3 dictionaries: addition (with added key-value pairs),
        deletion (with deleted keys and their latest values),
        modification (with keys which had a values change and the new value).
        """
        archived_keys = self.keys_in_version(version_n=self.version_number - 1)
        addition = {deepcopy(key): deepcopy(value)
                    for key, value in self.items()
                    if key not in archived_keys}
        deletion = {}
        for key in archived_keys - set(self.keys()):
            value = self.lookup_value(
                key,
                version_n=self.version_number - 1
            )
            deletion[deepcopy(key)] = deepcopy(value)
        modification = {}
        for key in archived_keys.intersection(set(self.keys())):
            value = self.lookup_value(
                key,
                version_n=self.version_number - 1
            )
            if self[key] != value:
                modification[deepcopy(key)] = deepcopy(self[key])
        return addition, deletion, modification

    def rewind_version(self):
        """
        Restore the previous version and return its number.

        Recreate the latest older version by consecutively updating an empty
        dict with the stored versions. Dispose the current version.
        """
        if self.version_number > 0:
            archived_keys = self.keys_in_version(
                                            version_n=self.version_number - 1)
            archived_dict = {}
            for key in archived_keys:
                val = self.lookup_value(key, version_n=self.version_number - 1)
                archived_dict[key] = val
            self.clear()
            self.update(deepcopy(archived_dict))
            del self.__additions[-1]
            del self.__deletions[-1]
            del self.__modifications[-1]
            self.__version -= 1
            return self.__version
        else:
            raise VersionedDictRewindError()

    @property
    def version_number(self):
        """
        Return the version number of the current version.

        Numbering starts from 0, i.e., when no :meth:`forward_version` has
        taken place, then the current version has number 0.
        """
        return self.__version

    def version_number_valid(self, version_n):
        """
        Return whether *version_n* is a valid version number.

        *version_n* must be a non-negative int not bigger than
        self.version_number .
        """
        return (isinstance(version_n, int) and version_n >= 0 and
                version_n <= self.version_number)

    def lookup_version(self, version_n):
        """
        Return the archived version for a given version number *version_n*.

        If the version is invalid, raise
        :class:`VersionedDictInvalidVersionError`.

        Note: Does not return a (deep) copy.
        """
        if not self.version_number_valid(version_n):
            raise VersionedDictInvalidVersionError(self, version_n)
        if version_n == self.version_number:
            return self
        archived_keys = self.keys_in_version(version_n=version_n)
        archived_dict = {}
        for key in archived_keys:
            val = self.lookup_value(key, version_n=version_n)
            archived_dict[key] = val
        return archived_dict

    def keys_in_version(self, version_n=None):
        """
        Return a set of keys in the version with number *version_n*.

        If *version_n* is None, then return the keys in the current version.

        If *version_n* is invalid, raise an :raise:`InvalidDictVersionError`.
        """
        if version_n is not None and not self.version_number_valid(version_n):
            raise VersionedDictInvalidVersionError(self, version_n)
        if version_n is None or version_n == self.version_number:
            return self.keys()
        archived_keys = set()
        for version_i in range(version_n + 1):
            archived_keys |= set(self.__additions[version_i].keys())
            archived_keys -= set(self.__deletions[version_i].keys())
        return archived_keys

    def lookup_value(self, key, version_n=None):
        """
        Lookup the value for a given *key* and version number *version_n*.

        If *version_n* is None, then return the current value for the key.

        If *version_n* is invalid, raise an :raise:`InvalidDictVersionError`.

        If the key is not present in the requested version, raise a
        :raise:`KeyError`.

        Otherwise return the value.

        Note: Does not return a (deep) copy.
        """
        if version_n is not None and not self.version_number_valid(version_n):
            raise VersionedDictInvalidVersionError(self, version_n)
        if version_n is None or version_n == self.version_number:
            return self[key]
        for version_i in reversed(range(version_n + 1)):
            if key in self.__deletions[version_i]:
                raise KeyError(key)
            elif key in self.__additions[version_i]:
                return self.__additions[version_i][key]
            elif key in self.__modifications[version_i]:
                return self.__modifications[version_i][key]
        else:
            raise KeyError(key)

    def diff_previous(self, version_n=None):
        """
        Return information on the difference between two consecutive versions.

        Return the additions, deletions and modifications from
        *version_n* - 1 to *version_n*.

        If *version_n* is None, return the difference of the current version
        against the latest archived one.
        """
        if version_n is None:
            return self.__diff_current_against_latest_archived()
        if version_n < 1:
            return {}, {}, {}
        return (self.__additions[version_n - 1],
                self.__deletions[version_n - 1],
                self.__modifications[version_n - 1])

    def diff_pair(self, version_n1, version_n2):
        """
        Return information on the difference between two arbitrary versions.

        Return the additions, deletions and modifications from
        *version_n1* to *version_n2*.

        Note: Does not return a (deep) copy.
        """
        if version_n1 >= version_n2:
            return {}, {}, {}
        archived_keys1 = self.keys_in_version(version_n=version_n1)
        archived_keys2 = self.keys_in_version(version_n=version_n2)
        addition = {}
        for key in archived_keys2 - archived_keys1:
            value = self.lookup_value(key, version_n=version_n2)
            addition[key] = value
        deletion = {}
        for key in archived_keys1 - archived_keys2:
            value = self.lookup_value(key, version_n=version_n1)
            deletion[key] = value
        modification = {}
        for key in archived_keys1.intersection(archived_keys2):
            value1 = self.lookup_value(key, version_n=version_n1)
            value2 = self.lookup_value(key, version_n=version_n2)
            if value1 != value2:
                modification[key] = value2
        return addition, deletion, modification
