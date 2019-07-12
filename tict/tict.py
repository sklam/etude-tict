from collections import MutableMapping, namedtuple, defaultdict
import random
import copy

"""
*Record* is used to store the key-value pair internally of Tict.
It also maintain a chain of hashes to (weakly) check that *SavedState* is
in the correct branch of chains.
"""
Record = namedtuple('Record', ['key', 'value', 'hashed'])

"""
*SavedState* is used to store information needed to rollback to be previous
state.
"""
SavedState = namedtuple('SavedState', ['pos', 'hashinitial', 'hashstate'])


class TictInternalError(RuntimeError):
    pass


class TictRollbackError(RuntimeError):
    pass


class _Removed(object):
    _singleton = None
    def __new__(cls):
        if cls._singleton is None:
            cls._singleton = object.__new__(cls)
        return cls._singleton

    def __repr__(self):
        return "<Removed>"


_Removed = _Removed()


class Tict(MutableMapping):
    """A transaction dictionary that can rollback to a previous state.

    Warning
    -------
    - Do not use with mutating values.  Values in the dictionary should be
      considered as non-mutating for sane behavior.
    """
    def __init__(self):
        # Hash seed
        self._internal_hash = hash
        self._seed = self._internal_hash(random.random())
        self._hashinitial = self._seed
        # List of Record
        self._keyvals = []
        # Caches
        # Known keys
        self._keys = set()
        # Index for fast lookup
        self._index = {}

    def __copy__(self):
        new = Tict()
        new._hashinitial = self._hashinitial
        new._seed = self._seed
        new._keyvals = self._keyvals.copy()
        new._keys = self._keys.copy()
        new._index = self._index.copy()
        return new

    def _update_seed(self, hashval):
        hashed = self._internal_hash((hashval, self._seed))
        self._seed = hashed
        return hashed

    def __setitem__(self, k, v):
        self._keys.add(k)
        self._keyvals.append(
            Record(key=k, value=v, hashed=self._update_seed((k, id(v)))),
        )

    def __getitem__(self, k):
        if k not in self._keys:
            raise KeyError(k)
        try:
            pos = self._index[k]
        except KeyError:
            pos = len(self._keyvals) - 1
            while pos >= 0:
                kv = self._keyvals[pos]
                if k == kv.key:
                    v = kv.value
                    if v is _Removed:
                        msg = 'key ({!r}) was removed'.format(k)
                        raise TictInternalError(msg)
                    return kv.value
                pos -= 1
            else:
                # impossible situation
                raise TictInternalError('cannot find key ({!r})'.format(k))

    def __delitem__(self, k):
        if k not in self._keys:
            raise KeyError(k)

        self._keys.remove(k)
        self._index.pop(k, None)
        self._keyvals.append(
            Record(
                key=k,
                value=_Removed,
                hashed=self._internal_hash((k, _Removed)),
            ),
        )

    def __len__(self):
        return len(self._keys)

    def __iter__(self):
        return iter(self._keys)

    def save(self):
        """Save the current state of the dictionary

        Returns
        -------
        state : SavedState
        """
        hashstate = self._keyvals[-1].hashed
        assert hashstate == self._seed
        return SavedState(
            pos=len(self._keyvals),
            hashinitial=self._hashinitial,
            hashstate=hashstate,
        )

    def rollback(self, state):
        """Rollback to a previously saved state

        Parameters
        ----------
        state : SavedState
        """
        self._sentry_valid_state(state)
        self._rollback_to_position(state.pos)

    def _rollback_to_position(self, end):
        self._keyvals = self._keyvals[:end]
        self._invalidate()

    def revert(self, state):
        """Revert the changes in the dictionary since the given state.

        Done by applying the observable key-values from *state* into the
        current dictionary.
        """
        old = self.copy()
        old.rollback(state)
        # Apply difference from the old state
        got_keys = set()
        for k, v in old.items():
            got_keys.add(k)
            self[k] = v
        dead_keys = self._keys - got_keys
        for k in dead_keys:
            del self[k]
        self._keys = got_keys

    def _sentry_valid_state(self, state):
        if self._hashinitial != state.hashinitial:
            raise TictRollbackError('invalid hash initial in saved state')
        if self._keyvals[state.pos - 1].hashed != state.hashstate:
            raise TictRollbackError('invalid hash state in saved state')

    def _invalidate(self):
        """Invalidate cached info
        """
        self._rebuild_keys()

    def _rebuild_keys(self):
        """Rebuild the *_keys*
        """
        keys = set()
        ignored = set()
        for kv in reversed(self._keyvals):
            if kv.key not in ignored and kv.value is not _Removed:
                keys.add(kv.key)
            ignored.add(kv.key)
        self._keys = keys

    def copy(self):
        return copy.copy(self)

    def revisions(self, since=None, until=None):
        """Returns an generator yielding that state of the dictionary
        at different revision point in the range *since* to *until*
        inclusively.

        Parameters
        ----------
        since : SavedState
            Defaults to None to indicate starting from the beginning.
        until : SavedState
            Defaults to None to indicate stoping at the end.

        """
        if since is not None:
            self._sentry_valid_state(since)
            start = since.pos
        else:
            start = 0

        if until is not None:
            self._sentry_valid_state(until)
            stop = until.pos
        else:
            stop = len(self._keyvals)

        for end in range(start, stop):
            dct = self.copy()
            dct._rollback_to_position(end)
            yield dct
