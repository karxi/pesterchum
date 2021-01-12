# -*- coding=UTF-8; tab-width: 4 -*-
from __future__ import division

__all__ = ["CaselessDict", "Hostmask"]

# karxi: This entire 

from ..dep.attrdict import AttrDict

import collections
##import math					# For math.sqrt
##import operator					# Need its .sub() for Color.difference()
# In hindsight neither of the two listed above were required at all. Oops!
import fnmatch					# For Hostmask.match_against - NOTE: lazy!

try:
    from UserDict import UserDict
except ImportError:
    # Python 3....
    from collections import UserDict
    basestr = str
else:
    # Python 2!
    basestr = basestring

# A caseless dictionary - like mIRC uses for its hashes, for example
##class CaselessDict(object, UserDict.IterableUserDict):
class CaselessDict(UserDict):
    # TODO: Fix from_keys!! It seems like it MAY be borked; we CANNOT allow
    # duplicate entries, because they cause bugs to crop up when we iterate.
    # Maybe update_keylist() should cleanse the dict too, as a stopgap?
    def __init__(self, dict=None, **kwargs):
        self.data = {}
        self._keys = {}
        if dict is not None:
            self.update(dict)
        if len(kwargs):
            self.update(kwargs)
        # update_keylist() is called by update() too
    def __getstate__(self):
        # This should save at least a little bit of space
        result = self.__dict__.copy()
        del result["_keys"]
        return result
    def __setstate__(self, state):
        for k in state:
            self.__dict__[k] = state[k]
        self._keys = {}
        self.update_keylist()
    def keyconv(self, key): return self._keys[self._conv(key)]
    def __repr__(self): return "%s(%r)" % (self.__class__.__name__, self.data)
    def __cmp__(self, dict):
        if isinstance(dict, CaselessDict):
            ##return cmp(self.data, dict.data)
            return cmp(self._keys.keys(), dict._keys.keys())
        else: return cmp(self.data, dict)
    def __getitem__(self, key):
        try: key = self.keyconv(key)
        except KeyError:
            if hasattr(self.__class__, "__missing__"):
                return self.__class__.__missing__(self, key)
            ##if hasattr(self, "__missing__"):
            ##	return self.__missing__(key)
            raise
        else:
            if key in self.data: return self.data[key]
    def __setitem__(self, key, item):
        if self._conv(key) in self._keys: key = self.keyconv(key)
        else: self._keys[self._conv(key)] = key
        self.data[key] = item
    def __delitem__(self, key):
        del self.data[self.keyconv(key)], self._keys[self._conv(key)]
    def clear(self): self.data.clear(); self._keys.clear()
    # Added the iter*s, because UserDict doesn't have those normally
    def iteritems(self): return self.data.iteritems()
    def iterkeys(self): return self.data.iterkeys()
    def itervalues(self): return self.data.itervalues()
    def has_key(self, key): return key in self # Delegate to __contains__()
    def update(self, dict=None, **kwargs):
        if dict is None:
            pass
        elif isinstance(dict, CaselessDict):
            self.data.update(dict.data)
        elif isinstance(dict, type({})) or not hasattr(dict, 'items'):
            self.data.update(dict)
        else:
            for k, v in dict.items():
                self[k] = v
        if len(kwargs):
            self.data.update(kwargs)
        self.update_keylist()
    def update_keylist(self):
        self._keys.clear()
        for key in self.data.keys():
            self._keys[self._conv(key)] = key
        return
        # Old version
        keys = self.data.keys()
        values = keys[:]
        keys = map(str.lower, keys)
        self._keys = dict(zip(keys, values))
    # Added the view*s, because UserDict doesn't have those normally
    def viewitems(self): return self.viewitems()
    def viewkeys(self): return self.data.viewkeys()
    def viewvalues(self): return self.data.viewvalues()
    def pop(self, key, *args):
        result = self.data.pop(self._conv(key), *args)
        del self._keys[self._conv(key)]
        return result
    def popitem(self):
        result = self.data.popitem()
        key = result[0]
        del self._keys[self._conv(key)] # We no longer HAVE the key, so...
        return result
    def __contains__(self, key):
        return self._conv(key) in self._keys
        # Note that this is less than perfect, but it's also much faster

    ##_conv = lambda self, s: self.converter(s)
    def _conv(self, s):
        if self.converter: return self.converter(s)
        else: return str.lower(s)
    # The function which will convert things to 'lowercase'
    ##converter = staticmethod(lambda s: str.lower(s))
    converter = None
    # This is present so the definition of lowercase can be changed from
    # Python's own. IRC uses a different definition, and it's important to be
    # able to follow it.



# An old class, used by the textsub script. Pending adjustment/refactoring.
class Hostmask(object):
    """Hostmask(nick, ident, host) => Hostmask object
    Hostmask(hostmask string) => Hostmask object

    An object which represents a hostmask."""
    # Changed - properties apparently don't need their own slots
    ##__slots__ = ("nick", "ident", "host")
    __slots__ = ("_nick", "_ident", "_host")
    ##def __init__(self, mask):
    def __init__(self, nick=None, ident=None, host=None):
        # TODO: Set up a __new__ for this so it can deal with Hostmask(Hostmask()) cases (?...)
        self._nick = self._ident = self._host = None
        # Parse the hostmask
        ##match = re.match(r"^(?:(?P<nick>[\w\\[]{}^`|][-.\w\\[]{}^`|]+)!)?(?:(?P<ident>[-\w\d~.]+)@)?(.*)$", mask)
        ##match = parse_hostmask_re.match(mask)
        ##if (isinstance(nick, ConPt)):
        ##	# We have a connection point
        ##	cpt = nick
        ##	if (isinstance(cpt.mask, Hostmask)):
        ##		mask = cpt.mask
        ##		nick, ident, host = mask.nick, mask.ident, mask.host
        ##	else:
        ##		nick, ident, host = cpt.nick, None, cpt.host
        if isinstance(nick, Hostmask):
            # Essentially, we want to duplicate the Hostmask we were passed
            nick, ident, host = nick
        elif (hasattr(nick, "nick")
            and hasattr(nick, "ident")
            and hasattr(nick, "host")
            ):
            # Detect things which we can read and run with (or try to run with)
            nick, ident, host = nick.nick, nick.ident, nick.host
        elif nick is not None:
            if ident is host is None and ('!' in nick or '@' in nick):
                # Called with only one argument, and we aren't just being given
                # a nick, but rather, we've been passed a hostmask as a string
                ##nick, ident, host = self.parse_str(nick)
                nick, ident, host = self.str_to_tuple(nick)
            ##elif '@' in ident and bool(ident) ^ bool(host):
            elif bool(ident) ^ bool(host):
                # Technically that could just be done as a(n) != operation,
                # because != is actually equivalent to a logical xor if it's
                # applied to two bools, but that isn't very CLEAR
                #
                # Presumably getting here means we've been passed a nick and a
                # string along the lines of <ident>@<host> - a few things in
                # XChat tend to give those
                # In either case, using + in this way means we don't have to
                # have two cases (one for 'ident', one for 'host') like we
                # would need otherwise.
                combined = (ident or '') + (host or '')
                if '@' in combined:
                    ident, host = combined.split('@', 1)
        # Don't store these, for space reasons
        # Maybe use str() on these?
        ##if nick: nick = str(nick)
        if nick is not None:	nick = str(nick)
        if ident is not None:	ident = str(ident)
        if host is not None:	host = str(host)
        ##self.nick, self.ident, self.host = nick, ident, host
        self._nick	= self._sfs(nick)
        self._ident	= self._sfs(ident)
        self._host	= self._sfs(host)

    # Pickling methods
    def __getstate__(self):
        # Basically experimental
        ##return str(self)
        # Yes, the parenthesis are staying because they emphasize that this is
        # returning a tuple
        ##return (self.nick, self.ident, self.host)
        return tuple(self)
    def __setstate__(self, state):
        if isinstance(state, basestr):
            # It's the experimental kind
            self.nick, self.ident, self.host = self.str_to_tuple(state)
        elif isinstance(state, tuple):
            # An alternative storage method, which may be implemented if a
            # __slots__ is ever made for this class
            self.nick = state[0] or None
            self.ident = state[1] or None
            self.host = state[2] or None
        ##elif isinstance(state, dict):
        else:
            # If we got here, it's PROBABLY a dict
            # 2012-08-17T05:59-06:00:
            # ...In hindsight that would be AWFULLY STRANGE, because this class
            # uses __slots__.... As such, changed the workings of the actual
            # assignment
            # TODO: Add error checking
            ##for k in state:
            for k in type(self).__slots__:	# Might be unnecessary?
                ##self.__dict__[k] = state[k]
                # The above was removed because of __slots__; hopefully the
                # replacement below will do just fine (not that it really
                # matters - this situation should probably never actually come
                # up!).
                setattr(self, k, state[k])

    # Builtins
    def __contains__(self, value): return value in self.wildstr()
    def __getitem__(self, ind): return (self.nick, self.ident, self.host)[ind]
    def __eq__(self, other):
        return hash(self) == hash(other)
    def __ne__(self, other): return not self.__eq__(other)
    def __hash__(self):
        # Will probably be removed when ImmutableHostmask is completed - though
        # I'm not sure that type is even technically necessary...also, we
        # could probably subtype namedtuple or something for this
        ##return hash(str(self))
        result =  hash(self._nick)
        result ^= hash(self._ident)
        result ^= hash(self._host)
        return result
    def __iter__(self):
        # Makes it possible to use this as a tuple during assignments, making
        # it rather like a NamedTuple object
        # However, since we also support __len__ and __getitem__, it isn't
        # strictly necessary - Python would generate an iterator for us if need
        # be. Unfortunately, that means it wouldn't qualify as a subclass of
        # collections.Iterable on its own.
        targs = (self.nick, self.ident, self.host)
        for t in targs:
            yield t
        # If we got here, we're out of attributes to provide
        raise StopIteration
    def __len__(self):
        # Just return 3 - there shouldn't be an instance in which this isn't
        # the case
        return 3
    def __nonzero__(self):
        return bool(self._nick or self._ident or self._host)

        # Old version, in case reversion needs to happen. Also explains a bit
        if self._nick or self._ident or self._host:
            # Check if ANY of these are set; if so, return True
            return True
        # Otherwise, none of those are set so this is essentially a blank
        # hostmask
        return False
    __bool__ = __nonzero__		# To maintain forward compatibility with Py3
    def __repr__(self): return "%s(%r)" % (type(self).__name__, str(self))
    # TODO: Consider a minimal version of str (which cuts off unneeded parts)
    def __str__(self):
        if self:
            result = "%s!%s@%s" % \
                tuple(self)
                ##(
                    ##self.nick or '*', self.ident or '*', self.host or '*'
                    ##self.nick or '', self.ident or '', self.host or ''
                    ##self.nick, self.ident, self.host
                    ##)
        else:
            result = ''
        return result
    ##def asterstr(self):
    def wildstr(self):
        # String representation with blanks replaced by asterisks - intended
        # for use with search functions
        t = (self.nick or '*', self.ident or '*', self.host or '*')
        result = "%s!%s@%s" % t
        return result

    # String methods
    def altstr(self):
        result = []
        if self.host: result.append(self.host)
        if self.nick or self.ident:
            # This also triggers if we have an ident, because having two
            # backslashes instead of one shows that the last thing listed is an
            # ident - not a nick, as one would expect
            result.append(self.nick)
        if self.ident: result.append(self.ident)
        ##if result == []:
        ##	# Still not sure whether the 'H' in this message should be
        ##	# capital or lowercase...but that's a rather minor detail
        ##	result = "<empty Hostmask>"
        ##else:
        ##	result = '\\'.join(result)
        # This is acceptable because it will output the empty string if none of
        # the above conditions are true, which is the intention here.
        result = '\\'.join(result)
        return result
    # These two might be able to benefit from some optimization?...eh, screw it
    # (at least for now) - it probably doesn't make much difference at ALL
    def lower(self): return type(self)(str(self).lower())
    def upper(self): return type(self)(str(self).upper())

    def match_against(self, mask):
        """HM.match_against(mask) =>
            Match HM against 'mask', a pattern Hostmask."""
        qnick, qident, qhost = mask
        if qnick and qnick != '*':
            if not fnmatch.fnmatch(self.nick, qnick):
                # Its nick doesn't fit....
                return False
        if qident and qident != '*':
            if not fnmatch.fnmatch(self.ident, qident):
                # Its ident doesn't fit....
                return False
        if qhost and qhost != '*':
            if not fnmatch.fnmatch(self.host, qhost):
                # Its host doesn't fit....
                return False
        return True

    @classmethod
    def fragment_type(cls, text):
        # TODO: Option to allow some uncertainty so the no match situations can
        # be resolved
        # TODO!: Make this tally up the number of indicators and use the one
        # with the greatest number of successes to determine which type of
        # fragment we have!
        ##not_nick = not_ident = not_host = None
        nick = ident = host = None
        ##if not long_idents and len(text) > 10: not_ident = True
        nick = cls.is_nick(text)
        ident = cls.is_ident(text)
        host = cls.is_host(text)

        # Yes, we do this the clumsy way.
        # N.B.: The bitshifts here are valid because bool is a subtype of int
        ##if nick and not ident and not host: return True << 0	# Nick
        ##if not nick and ident and not host: return True << 1	# Ident
        ##if not nick and not ident and host: return True << 2	# Host
        if nick and not ident and not host: return 1
        if not nick and ident and not host: return 2
        if not nick and not ident and host: return 3
        # If none of those are the case, we can't make a conclusive decision...
        ##return False >> 0 # (1 >> 1) (because "1 << -1" is invalid)
        return 0

        # WIP
        highest = max(nick, ident, host)
        if highest < 1: return 0
        elif highest == nick == ident == host:
            # By some fluke we ended up with all of them being equal....
            return 0
        elif nick == highest: return 1
        elif ident == highest: return 2
        elif host == highest: return 3
    # Functions used by fragment_type
    # TODO: Ugh...this was better as one function, tallying results; recombine
    # it.
    @staticmethod
    def is_nick(nick):
        """Attempts to determine if a given string is a valid nick.
        0 is returned in the event that a decision cannot be made."""
        ##if '~' in nick: return False # Ident (?)
        if nick.startswith('~'): return False
        if '.' in nick: return False # Ident or host
        # TODO: Add a check for nick length limits? Might need to specify that
        # one via a setting or add something to ircclient....
        return 0
    @staticmethod
    def is_ident(ident):
        """Attempts to determine if a given string is a valid ident.
        0 is returned in the event that a decision cannot be made."""
        ##if '~' in ident: return True
        if ident.startswith('~'): return True
        # TODO: Make an option that allows unusually long idents
        if len(ident) > 10: return False
        return 0
    @staticmethod
    def is_host(host):
        """Attempts to determine if a given string is a valid host.
        0 is returned in the event that a decision cannot be made."""
        if '[' in host or ']' in host: return False # Nick (or ident?)
        if ':' in host: return True
        return 0

    @classmethod
    def from_str(cls, mask):
        """Create a new Hostmask instance by parsing a provided string."""
        # TODO:
        # This: def from_str(cls, mask, fmt="nim"):
        # That is, mplement 'fmt' - order of letters 'nim' determine what order
        # the nick, ident, and mask are expected to be in (respectively).
        nick = ident = host = None
        ##parts = re.split(r"[!@]", mask)
        # Basically this is organized like a switch statement instead of as a
        # tree as was originally planned - this is simpler since each
        # combination can be accounted for on its own
        if '!' in mask and '@' in mask:
            # both ! AND @:	nick!ident@host
            # We must have a full hostmask
            nick, parts = mask.split('!', 1)
            ident, host = parts.split('@', 1)
        elif '!' in mask:
            # ! but no @:	nick!ident
            # We don't have a mask, but we at least have a nick and presumably
            # an ident as well
            nick, ident = mask.split('!', 1)
        elif '@' in mask:
            # @ but no !:	ident@host or nick@host; we assume the latter
            nick, host = mask.split('@', 1)
        else:
            # no @, no !:
            # Hand things off to the method that determines what kind of thing
            # we're dealing with
            t = cls.fragment_type(mask)
            if t == 1: nick = mask
            elif t == 2: ident = mask
            elif t == 3: host = mask
        if nick is ident is host is None:
            nick, ident, host = cls.str_to_tuple(mask)
        if nick is ident is host is None:
            # If it's STILL None, raise an error - we couldn't parse it
            raise ValueError("Couldn't convert %r into a hostmask!" % mask)
        return cls(nick=nick, ident=ident, host=host)
    @classmethod
    def str_to_tuple(cls, mask):
        # TODO: Check if there isn't a better way to do this
        parts = mask.split('!', 1)
        try:
            nick = parts[0] or None
            ##parts = mask.split('@', 1)
            parts = parts[1].split('@', 1)
            ident = parts[0] or None
            host = parts[1] or None
        except IndexError:
            # If we got here, try our essentially proprietary method
            # That is, "host\nick[\<ident>]"
            parts = mask.split('\\', 2)
            mask = parts[0] or None
            nick = parts[1] or None
            try: ident = parts[2] or None
            except IndexError: ident = None
        return nick, ident, host

    # Property junk
    @staticmethod
    def _sanitize_for_getter(value):
        if (value is None): return ''
        return value # They're ALREADY strings, so we don't need to str() them
    @staticmethod
    def _sanitize_for_setter(value):
        if (value == ''
            ##or value == '*'
            ):
            return None
        return value
    # Aliases for the above
    _sfg = _sanitize_for_getter
    _sfs = _sanitize_for_setter

    # 2012-08-01T12:53-06:00: Deleters removed. Deletions generally only cause
    # things to break in classes like this, and they're effectively unnecessary
    # for clearing a value here - they were little more than a (rather obscure)
    # potential shortcut which found no use whatsoever.
    @property
    def nick(self): return self._sfg(self._nick)
    @nick.setter
    def nick(self, nick): self._nick = self._sfs(nick)

    @property
    def ident(self): return self._sfg(self._ident)
    @ident.setter
    def ident(self, ident): self._ident = self._sfs(ident)

    @property
    def host(self): return self._sfg(self._host)
    @host.setter
    def host(self, host): self._host = self._sfs(host)
##collections.MutableSequence.register(Hostmask)

# VERY unfinished - methods from Hostmask are fairly likely to break when
# called for an instance of ImmutableHostmask!
class ImmutableHostmask(Hostmask):
    """An immutable version of the Hostmask type, suitable for use as keys in
    dicts, elements in sets, and so on.

    Note that this is currently a definite work in progress, and as such it
    should probably not be used for anything important until its completion."""
    __slots__ = Hostmask.__slots__

    def __hash__(self):
        return hash(self._nick) ^ hash(self._ident) ^ hash(self._host)
    # Note the lack of setters
    @property
    def nick(self): return self._sfg(self._nick)
    @property
    def ident(self): return self._sfg(self._ident)
    @property
    def host(self): return self._sfg(self._host)

# vim: set autoindent ts=4 sts=4 sw=4 textwidth=79 expandtab:
