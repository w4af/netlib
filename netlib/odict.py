from __future__ import (absolute_import, print_function, division)
import re
import copy


def safe_subn(pattern, repl, target, *args, **kwargs):
    """
        There are Unicode conversion problems with re.subn. We try to smooth
        that over by casting the pattern and replacement to strings. We really
        need a better solution that is aware of the actual content ecoding.
    """
    return re.subn(str(pattern), str(repl), target, *args, **kwargs)


class ODict(object):

    """
        A dictionary-like object for managing ordered (key, value) data. Think
        about it as a convenient interface to a list of (key, value) tuples.
    """

    def __init__(self, lst=None):
        self.lst = lst or []

    def _kconv(self, s):
        return s

    def __eq__(self, other):
        return self.lst == other.lst

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iter__(self):
        return self.lst.__iter__()

    def __getitem__(self, k):
        """
            Returns a list of values matching key.
        """
        ret = []
        k = self._kconv(k)
        for i in self.lst:
            if self._kconv(i[0]) == k:
                ret.append(i[1])
        return ret

    def keys(self):
        return list(set([self._kconv(i[0]) for i in self.lst]))

    def _filter_lst(self, k, lst):
        k = self._kconv(k)
        new = []
        for i in lst:
            if self._kconv(i[0]) != k:
                new.append(i)
        return new

    def __len__(self):
        """
            Total number of (key, value) pairs.
        """
        return len(self.lst)

    def __setitem__(self, k, valuelist):
        """
            Sets the values for key k. If there are existing values for this
            key, they are cleared.
        """
        if isinstance(valuelist, str):
            raise ValueError(
                "Expected list of values instead of string. "
                "Example: odict['Host'] = ['www.example.com']"
            )
        kc = self._kconv(k)
        new = []
        for i in self.lst:
            if self._kconv(i[0]) == kc:
                if valuelist:
                    new.append([k, valuelist.pop(0)])
            else:
                new.append(i)
        while valuelist:
            new.append([k, valuelist.pop(0)])
        self.lst = new

    def __delitem__(self, k):
        """
            Delete all items matching k.
        """
        self.lst = self._filter_lst(k, self.lst)

    def __contains__(self, k):
        for i in self.lst:
            if self._kconv(i[0]) == self._kconv(k):
                return True
        return False

    def add(self, key, value):
        self.lst.append([key, value])

    def get(self, k, d=None):
        if k in self:
            return self[k]
        else:
            return d

    def get_first(self, k, d=None):
        if k in self:
            return self[k][0]
        else:
            return d

    def items(self):
        return self.lst[:]

    def copy(self):
        """
            Returns a copy of this object.
        """
        lst = copy.deepcopy(self.lst)
        return self.__class__(lst)

    def extend(self, other):
        """
            Add the contents of other, preserving any duplicates.
        """
        self.lst.extend(other.lst)

    def __repr__(self):
        return repr(self.lst)

    def format(self):
        elements = []
        def str_to_bytes(s):
            if hasattr(s, 'encode'):
                return s.encode('utf-8')
            return s
        for itm in self.lst:
            elements.append(str_to_bytes(itm[0]) + b": " + str_to_bytes(itm[1]))
        elements.append(b"")
        return b"\r\n".join(elements)

    def in_any(self, key, value, caseless=False):
        """
            Do any of the values matching key contain value?

            If caseless is true, value comparison is case-insensitive.
        """
        if caseless:
            value = value.lower()
        for i in self[key]:
            if caseless:
                i = i.lower()
            if value in i:
                return True
        return False

    def match_re(self, expr):
        """
            Match the regular expression against each (key, value) pair. For
            each pair a string of the following format is matched against:

            "key: value"
        """
        for k, v in self.lst:
            s = "%s: %s" % (k, v)
            if re.search(expr, s):
                return True
        return False

    def replace(self, pattern, repl, *args, **kwargs):
        """
            Replaces a regular expression pattern with repl in both keys and
            values. Encoded content will be decoded before replacement, and
            re-encoded afterwards.

            Returns the number of replacements made.
        """
        nlst, count = [], 0
        for i in self.lst:
            k, c = safe_subn(pattern, repl, i[0], *args, **kwargs)
            count += c
            v, c = safe_subn(pattern, repl, i[1], *args, **kwargs)
            count += c
            nlst.append([k, v])
        self.lst = nlst
        return count

    # Implement the StateObject protocol from mitmproxy
    def get_state(self, short=False):
        return [tuple(i) for i in self.lst]

    def load_state(self, state):
        self.lst = [list(i) for i in state]

    @classmethod
    def from_state(klass, state):
        return klass([list(i) for i in state])


class ODictCaseless(ODict):

    """
        A variant of ODict with "caseless" keys. This version _preserves_ key
        case, but does not consider case when setting or getting items.
    """

    def _kconv(self, s):
        return s.lower()
