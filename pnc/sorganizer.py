# vim: set autoindent ts=4 sts=4 sw=4 tw=79 expandtab:
# -*- coding=UTF-8; tab-width: 4 -*-
"""A module which provides classes for the storage of settings."""

import inspect, types, weakref
# For deque
import collections
# For sanity
import logging
logger = logging.getLogger(__name__)

try:
    from .attrdict import AttrDict
except ImportError:
    # Fall back on the old location - just in case
    from .dep.attrdict import AttrDict

try:
    basestr = basestring
except NameError:
    # Python 3
    basestr = str

# Not wholly necessary, but still good practice.
__all__ = ["Option", "SettingsDict"]

def _get_path_to(tgt, adjust=0, raw=False, as_list=False, as_refs=False):
    # TODO: Make this a generic at module-level, probably
    sp = [ weakref.ref(tgt) ]
    last_host = tgt
    cur_ref, cur_host = tgt._host, None
    topmost = None
    while cur_ref:
        # Dereference the weakref.
        cur_host = cur_ref()
        # Check validity.
        if cur_host is None:
            # Do we even need to keep track of this?
            topmost = last_host
            break
        # It's valid, keep track of it (via weakref).
        sp.append(cur_ref)
        # Keep track of the actual object.
        last_host = cur_host
        # Get our next ref up.
        cur_ref = cur_host._host

    # Do processing.
    sp.reverse()
    if adjust != 0:
        #~# TODO: Just make sure this doesn't put 'raw' in the wrong place, ok?
        #~splen = len(sp)
        #~if adjust > 0:
        #~    adjust = max(2, splen - adjust)
        #~if splen - abs(adjust) < 2:
        #~    # We'd only be *left* with the one option...
        #~    adjust = max(adjust, splen - abs(adjust))
        # Cut off however many prefixes we were asked to
        sp = sp[adjust:]
    if raw and not (as_refs or as_list) and len(sp) > 1:
        # as_refs and as_list imply raw anyway
        # If it's too short, there's no point....
        sp.insert(1, "raw")

    if as_refs:
        return sp
    else:
        for i, r in enumerate(sp):
            if r == "raw":
                continue
            # Dereference.
            sp[i] = r()

    if as_list:
        return sp

    # If we got here, we're to return a text path
    for i, r in enumerate(sp):
        if r == "raw":
            continue
        sp[i] = r.name
    sp = '.'.join(sp)
    return sp

class OptionError(KeyError):
    # A test.
    pass

class Option(object):
    """Option(name, default, allowed[, callback(s)[, doc]]) =>
        An object that represents a setting.

    See the documentation for Option.__init__() for details on instantiation
    and how to perform it.

    Notes:
    This type is meant for use with SettingsDict or any types deriving from it;
    it should be noted that many features, such as callback support, WILL NOT
    FUNCTION unless it is.
    This is because SettingsDict does a considerable amount of processing when
    an attribute/item is set or fetched. It's simpler to code it this way,
    because doing so means that the value the Option represents is easily
    accessible, but at the same time, so is the Option itself, via use of a
    SettingsDict's .raw attribute (e.g. sd.raw.option_name).

    In time, the focus may be shifted from the SettingsDict type, but at the
    same time this would (unfortunately) likely make the Options themselves
    more complicated to store."""
    # Disabled - slots aren't necessary here. Plus, __doc__ can't be set with
    # them in place: Because Option has a .__doc__, __slots__ prevents a new
    # .__doc__ from being made on its instances - presumably because that would
    # increase the object size or something to that effect.
    #~__slots__ = (
    #~  "__doc__",
    #~  "name",
    #~  "callback", "init_callback", "initialized", "storage",
    #~  "allowed_types", "default", "value")

    # The object containing this one.
    _host = None
    # Attributes on this class.
    allowed_types = tuple()
    default = raw_value = value = None
    initialized = False
    callback = init_callback = None

    def __init__(self, name, default, allowed, callback=None, doc=None,
                 host=None, **kwargs):
        """Initialize an instance.

        If the created instance will be used in a SettingsDict, 'name' should
        follow all of the normal rules for attribute names as a matter of
        principle.

        'allowed' defines the types that are considered valid values for the
        instance, but this is not (yet) enforced by the code. If/when it is,
        it should be noted that setting it to (), an empty tuple, is an easy
        way to stop it from allowing things to set it at all.

        'callback' can be a single callable object, which will be called when a
        value is set to the instance (excluding when __init__ sets it to the
        default), -OR- an iterable of callable objects or None, the assignments
        of which will vary depending on the number of members.
        At present, only an iterable two members long is supported, which
        specifies an init callback as well as the normal one in in the format
        (init, normal).

        'doc' specifies the documentation of the option, and should generally
        be included to prevent confusion on the part of the user as well as the
        programmer."""
        self.name = name
        self.raw_value = default
        self.value = self.default = default
        try:
            allowed = tuple(allowed)
        except TypeError:
            allowed = (allowed,)
        self.allowed_types = allowed
        self.__doc__ = doc
        self.initialized = False
        initcb = None
        if host:
            self._host = weakref.ref(host)
        # TODO: This is frustratingly cruft-y...but it allows minor extension
        # without subclassing.
        try:
            # This expects a dict of some kind, if anything.
            self.etc = kwargs["etc"]
        except KeyError:
            # 'etc' shouldn't really be referenced unless someone expects it,
            # in which case they can handle these things on their own.
            pass
        else:
            self.etc = AttrDict(self.etc)
        if callback is not None:
            try:
                ncbs = len(callback)
            except TypeError:
                # We don't have an iterable, or it doesn't support lengths, so
                # we SHOULD have a single callback....
                callback = self.process_cb(callback)
            else:
                cbs = []
                ##cbs = [ self.process_cb(cb) for cb in cbs ]
                # Process the callbacks into something usable
                for cb in callback:
                    cb = self.process_cb(cb, allow_none=True)
                    cbs.append(cb)

                # Now decide what to do with the callbacks based off of the
                # number present in the iterable we were given
                # Only one potential choice so far....
                if ncbs == 2:
                    # We were passed two callbacks - one for initialization,
                    # and one for when something tries to write to the Option.
                    initcb, callback = cbs
                else:
                    errmsg = "{1!s}: Option.__init__ does not accept {0:d}" \
                        " callbacks; check documentation for usage" \
                        " details".format(ncbs, self)
                    raise TypeError(errmsg)
        self.init_callback = initcb
        self.callback = callback
        # For the occasional bit of data that needs to be saved locally for
        # whatever reason.
        # In the original script, this is often made into a list and used to
        # store hook objects; they are unhooked by the containing Option's
        # callback when its setting is disabled (and vice-versa when it is
        # enabled).
        self.storage = None

    def __repr__(self):
        return '<{0!s} "{1!s}">'.format(type(self).__name__, self.name)

    def get(self, default=None):
        if default is not None:
            # We don't actually support this yet - it's here to be 'safe'.
            # In the future, it might check 'initialized' or similar.
            logger.debug("{opt}: get called with default {defl!r}".format(
                         opt=self, defl=default
                         ))
            pass
        # This function is mostly here to make room for eventual property-esque
        # callbacks that compute values as requested.
        # Of course, that sort of defeats the purpose of this framework...or at
        # least this class's usual role in it.
        return self.value

    def setdefault(self, val, default=None):
        # This is just here for convenience; we don't actually support this
        # functionality.
        # As such, it may be removed later.
        # TODO: Consider this.
        dbgmsg = "{opt}: setdefault called with {val!r}"
        if default:
            dbgmsg += " (default: {defl!r})"
        dbgmsg.format(opt=self, val=val, defl=default)
        logger.debug(dbgmsg)
        return self.set(val)

    def set(self, val):
        # ... Moved from SettingsDict. Presently testing. ...
        ###cb = self.callbacks[key] # Should be None or an actual callback
        #~cb = self.raw[key].callback
        cb = self.callback
        if cb:
            # We have a callback to call first, but before that we need to
            # save the old value.
            # 
            # Using this syntax creates room for allowing the value to be
            # calculated on-demand instead of requiring that it be a
            # constant, if (when) support for that is implemented in the
            # future.
            #~old = self[key] # Save this just in case; might wanna copy it
            old, oldraw = self.value, self.raw_value
            # Record the "raw version" of the value that was set.
            self.raw_value = val
            # False means we should set it; True means we shouldn't.
            try:
                # It's safe to assume this is an instancemethod because it
                # is MADE one when the Option is being created
                handled = cb(new=val, key=self.name)
            except:
                # We got an error for some reason - that indicates that we
                # most likely couldn't rely on the callback to set things
                # for us, so we should do it ourselves.
                # Making it only query settings.debug means that the only
                # way this could go wrong is if there's an issue with the
                # value of that setting...which would be rather bad anyway.
                #
                # They might've changed the value already, so change it
                # back - just so nothing breaks.
                ##self[key] = old # Whoops! This'd cause a loop....
                #~self.raw[key].value = old
                self.value, self.raw_value = old, oldraw
                # Now continue by raising the error
                raise
            if handled:
                # The Option's callback has apparently already changed the
                # value, and likely has done some special processing; we
                # don't want to overwrite it
                return
        # We got here due to lack of an appropriate callback.
        # We try to type_convert() before setting because it might fail
        newval = self.type_convert(val)
        self.raw_value = val
        self.value = newval

    def set_hard(self, val, convert=True):
        """Set a value without invoking callbacks.
        This can produce invalid results, so it should only be used for
        initialization.
        If 'convert' isn't True, it will skip ALL CALLBACKS, including
        typechecking. THIS IS LIABLE TO CAUSE ERRORS - use at your own risk!"""
        oldval = val
        newval = val
        if convert:
            newval = self.type_convert(val)
        self.raw_value = oldval
        self.value = newval

    def type_convert(self, val):
        """Convert a given value into the expected/processed type.
        This is called by callbacks at times; it's just processing/coercion to
        make sure that the value set is valid to everything that would use it.
        Can be replaced, like everything else."""
        allowed = self.allowed_types
        if not allowed or (len(allowed) > 0 and allowed[0] is None):
            # There aren't any types to coerce to, so just return it as-is.
            return val
        newval = None
        # We'll be using this as a queue.
        allowed = list(allowed)
        allowed.reverse()
        while allowed:
            wanted = allowed.pop()
            # Try to coerce.
            try:
                newval = wanted(val)
            except Exception as err:
                failmsg = "{opt}: {err}: Failed to coerce {type!r} from {val}"
                failmsg.format(opt=self, type=wanted, val=val, err=err)
                logger.warning(failmsg)
                continue
            else:
                # We coerced successfully; skip to the end.
                break
        else:
            # We couldn't coerce....
            errmsg = "{opt}: Can't convert {val!r} into any of {usable}"
            errmsg = errmsg.format(opt=self, val=val, usable=self.allowed_types)
            logger.error(errmsg)
            raise ValueError(errmsg)

        return newval

    def callback(self, new, key=None):
        """The default callback. Meant to provide an example of what normally
        is supposed to happen; note that this itself is never actually called
        under normal circumstances. It's simply an example of the bare
        minimum required to make a callback work.
        
        A callback is a method for an Option which accepts the listed
        arguments and returns a value which evaluates to True IF there is no
        further processing that needs to be done - i.e., the SettingsDict
        holding the setting SHOULD NOT go on to set the Option's new value
        itself, because the callback has already done so."""
        # Addendum regarding the script this was created for:
        # Having this here allows support for things like a read-only status
        # for options, which actually makes sense with a few of the current
        # ones - namely pickle_protocol. This MIGHT save that from being phased
        # out...*MIGHT*.
        # 2012-10-30T13:47-06:00: Ahahahaha, who was I kidding, nothing's going
        # to save that now.
        return False

    def init_callback(self):
        """The default initialization callback. This essentially exists to set
        the table for whatever the normal callback needs to do, for example, by
        setting self.storage to a list so an extra check isn't needed in the
        main callback.

        See callback() as well."""
        # See callback(), but for this it really doesn't matter what's returned
        pass

    def path_to(self, *args, **kwargs):
        """Get the path to this object."""
        return _get_path_to(self, *args, **kwargs)

    def process_cb(self, callback, allow_none=False):
        """Process a callback for use in the Option from which this method is
        being called. Raises TypeError when passed an invalid callback.
        If allow_none is not True, callbacks of None will be considered
        invalid and raise errors as normal."""
        if allow_none and callback is None:
            return None
        # So far we just need to check for unbound methods (mostly)
        if inspect.ismethod(callback):
            # If we have a MethodType, we need to do some testing
            if callback.im_self is None:
                # We have an unbound method, so create a new instancemethod
                # and bind it to this object manually
                callback = callback.im_func
                # Not sure if we need to specify the class. For now, we won't,
                # because the older code doesn't.
                # Otherwise, the last arg would be 'self's class. This probably
                # affects super() usage or something to that effect.
                callback = types.MethodType(callback, self)
        elif callable(callback):
            # Ideally, in this case, we'd have a function so we could slot
            # it into an instancemethod. However, things like classes are
            # also callable - this isn't made to handle that, and it really
            # doesn't seem likely to come up, but it should work anyway.
            # 
            # 2012-10-30T13:51-06:00: The caching wrappers used in the main
            # script might be a situation in which a callable class instance
            # would be passed, but I can't fathom why they would be set up as
            # a callback....
            # If this is ever expanded to support system settings - that is,
            # ones which aren't supposed to be seen or modified by the person
            # USING the script - then this potential stumbling block might
            # become more relevant.
            callback = types.MethodType(callback, self)
        else:
            # We have an invalid argument....
            raise TypeError("%r is not callable" % callback)
        return callback
    # Included to wrap up the class, for proper folding in vim.
    pass


# 2012-10-15T17:23-06:00: Made SettingsDict independent from AttrDict
# 2017-01-25T10:29-05:00: Made SettingsDict inherit from AttrDict again
class SettingsDict(AttrDict):
#~class SettingsDict(dict):
    """A dictionary which is specifically keyed for storing settings."""

    # The object containing this one, if any.
    _host = None

    # These 3 (4?) were copied from AttrDict (and modified slightly, of course)
    def __repr__(self):
        return "{0!s}({1!s}, {2!s})".format(
                type(self).__name__,
                self.name,
                dict.__repr__(self))

    # May be phased out to force usage of .raw....
    def __delitem__(self, key):
        return super(SettingsDict, self).__delitem__(key)
    __delattr__ = __delitem__

    def copy(self): return type(self)(self)
    # Not really perfect....

    def __init__(self, *args, **kwargs):
        # 'init' was originally expected to be a dict of tuples, e.g.:
        # init={
        #   "autojoin_invite": (False, bool, ...),
        #   "verbose": (True, bool, ...)
        # }
        # 
        # However, now a list or tuple is expected instead, in which case the
        # '.name's of the options contained therein will be used to generate
        # the keys.
        # 2013-01-09T09:53-07:00: Changed to support naming again. Hopefully it
        # will actually WORK this time.
        arglen = len(args)
        init = None
        doc = None
        if arglen > 2:
            # We Assume name, init, doc? Doc is always last....
            # Let us fall through to below for now.
            doc = args[-1]
        if arglen > 1:
            # Assume that means name, then init
            name, init = args[:2]
        elif arglen > 0:
            # We only have one argument.
            #~init = args[0]
            #~name = kwargs.get("name")
            name = args[0]
        else:
            # Assume we have no unnamed arguments
            name = kwargs.get("name")
            init = kwargs.get("init")
        if doc is None or "doc" in kwargs:
            # It was specified directly (we hope).
            doc = kwargs.get("doc", None)
        if init is None:
                init = []
        if "host" in kwargs:
            self.__dict__["_host"] = host

        self._init_raw()
        self._set_name(name)
        ##self._set_name(self._sanitize_name(name))
        self.__dict__["__doc__"] = doc
        if isinstance(init, (list, tuple)):
            for opt in init:
                try:
                    self.add(opt)
                except (AttributeError, TypeError, ValueError):
                    raise

    # Since we make SURE that 'raw' is an attribute, it shouldn't be included
    # in the state, which means the old __getstate__() should do fine here
    # Normally it wouldn't matter if it were included or not, but the pickler
    # throws a fit if it can't find a class it needs upon load, and since
    # our SDRawInterface object is defined in the definition for SettingsDict
    # (and thus apparently invisible to the pickler), we end up being unable to
    # load at all. Luckily, that object doesn't need to be saved and can simply
    # be recreated on load.
    # EDIT: Changed the way these two function from how AttrDict does; we now
    # copy the __dict__ and explicitly delete .raw from the new entry
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["raw"]
        return state.items()
    def __setstate__(self, items):
        for key, val in items: self.__dict__[key] = val
        self._init_raw() # Since we *kind of need* that .raw

    def __getitem__(self, key):
        # Fetching the actual Option objects is handled by our .raw, which is
        # an instance of SDRawInterface
        obj = super(SettingsDict, self).__getitem__(key)
        if isinstance(obj, SettingsDict):
            return obj
        # We assume this is an Option.
        return obj.get()
    def __setitem__(self, key, item):
        # TODO: Consider making this capable of returning a list that has
        # callbacks for when its contents are modified if the Option's value is
        # a list
        # Options basically get free passes until TS's load_conf() is reworked;
        # everything ELSE should be using the <inst>.raw syntax to access the
        # actual Option objects
        # 2012-10-30T14:00-06:00: Actually, it seems fair enough to leave this
        # as it currently is.
        if isinstance(item, Option):
            # Perform the usual init check on the Option
            self._option_init_check(item)
            # Assign the Option to the requested key
            super(SettingsDict, self).__setitem__(key, item)
        elif isinstance(item, SettingsDict):
            super(SettingsDict, self).__setitem__(key, item)
        else:
            #~# We're setting an option's value
            #~# TODO: This needs to be moved to Option. A callback on the host is
            #~# reasonable - but the Options themselves need to have get, set,
            #~# and setdefault functionality. Otherwise, code gets
            #~# overcomplicated.
            #~###cb = self.callbacks[key] # Should be None or an actual callback
            #~cb = self.raw[key].callback
            #~if cb:
            #~    # We have a callback to call first, but before that we need to
            #~    # save the old value.
            #~    # 
            #~    # Using this syntax creates room for allowing the value to be
            #~    # calculated on-demand instead of requiring that it be a
            #~    # constant, if (when) support for that is implemented in the
            #~    # future.
            #~    old = self[key] # Save this just in case; might wanna copy it
            #~    # False means we should set it; True means we shouldn't.
            #~    try:
            #~        # It's safe to assume this is an instancemethod because it
            #~        # is MADE one when the Option is being created
            #~        handled = cb(new=item, key=key)
            #~    except:
            #~        # We got an error for some reason - that indicates that we
            #~        # most likely couldn't rely on the callback to set things
            #~        # for us, so we should do it ourselves.
            #~        # Making it only query settings.debug means that the only
            #~        # way this could go wrong is if there's an issue with the
            #~        # value of that setting...which would be rather bad anyway.
            #~        #
            #~        # They might've changed the value already, so change it
            #~        # back - just so nothing breaks.
            #~        ##self[key] = old # Whoops! This'd cause a loop....
            #~        self.raw[key].value = old
            #~        # Now continue by raising the error
            #~        raise
            #~    if handled:
            #~        # The Option's callback has apparently already changed the
            #~        # value, and likely has done some special processing; we
            #~        # don't want to overwrite it
            #~        return
            #~##super(SettingsDict, self).__setitem__(key, item)
            #~self.raw[key].value = item
            #~# Set the raw value too!
            #~# N.B.: Make it standard for this to be set in the callbacks?
            #~self.raw[key].raw_value = item
            self.raw[key].set(item)
        # And now we're done
    #~__getattr__, __setattr__ = __getitem__, __setitem__

    # Above removed - we're back to subclassing AttrDict.

    def add(self, opt):
        """Add an Option or SettingsDict to this one, in a similar fashion to
        the definitions given during init."""
        if isinstance(opt, SettingsDict) and not opt.name:
            msg = "SettingsDicts used as groups MUST have names!"
            raise ValueError(msg)
        self.raw[self._sanitize_name(opt.name)] = opt
        # Make sure it knows what it belongs to.
        opt.__dict__["_host"] = weakref.ref(self)
        try:
            self._option_init_check(opt)
        except AttributeError:
            # Presumably we had a SettingsDict if this is the case
            pass

    def path_to(self, *args, **kwargs):
        """Get the path to this object."""
        return _get_path_to(self, *args, **kwargs)

    def path_get(self, path, raw=False, strict=True):
        # TODO: This needs a docstring.
        strict_types = (SettingsDict, Option, SDRawInterface)

        if not (path and isinstance(path, basestr)):
            errmsg = "invalid path: {0!r}".format(path)
            raise ValueError(errmsg)

        # Get started processing.
        keys = path.split('.')
        keyq = collections.deque(keys)
        # -1 means no 'raw' was found or assigned.
        iraw = -1
        # Ensure 'raw' access; we'll need it for processing.
        # If there's already a 'raw' in there, that'd break, so we have to
        # process it....
        if 'raw' not in keyq:
            # We're always accessing from self, so 'raw' is added at 0.
            keyq.appendleft('raw')
            iraw = 0
        elif strict:
            # 'raw' already existed. If we've got 'strict' set, error.
            errmsg = "invalid path: {0!r} (raw indicator present; use" \
                " raw=True instead)".format(path)
            raise ValueError(errmsg)
        else:
            # Not strict. Handle the 'raw'.
            # Yes, we *do* use *keys* here, not keyq. Deque objects don't have
            # an index method...and the contents of the two isn't different,
            # yet.
            iraw = keys.index('raw')
            if iraw == 0:
                # Best-case scenario.
                logger.warning(
                    "{0!r} begins with 'raw'; ignoring...".format(path)
                )
            else:
                logger.warning(
                    "Removing extraneous 'raw' from {0!r}.".format(path)
                )
                del keyq[iraw]
                # Put the 'raw' in a more favorable position.
                keyq.appendleft('raw')

        # Save a copy of our "starting point".
        # Lists are more flexible than deques.
        start = list(keyq)
        keysln, keyqln, startln = map(len, (keys, keyq, start))
        # We start from self.
        cur = self
        key = None

        def _failpt():
            # Determine where we screwed up.
            # Make a copy, just in case...and/or perform a type change.
            failed = list(start)
            # Use the remaining length of keyq to determine how much we
            # processed, and thus, where we stopped; then, cut that many keys
            # from our starting list.
            failed = failed[:-len(keyq)]
            # Just to make sure the math is right.
            assert(failed[-1] == key)
            # Remove the 'raw' from the output...
            if failed[-1] != 'raw':
                # ...unless it was part of our target...? That shouldn't ever
                # happen, though.
                try:
                    failed.remove('raw')
                except ValueError:
                    # Odd...we didn't have one?? That shouldn't happen.
                    # Ignore it for now.
                    pass
            else:
                logger.warning("Last element of %r is 'raw'", path)
            failat = '.'.join(failed)
            return failat

        while keyq:
            key = keyq.popleft()
            keyqln = len(keyq)
            try:
                # Progress a step.
                cur = getattr(cur, key)
            except AttributeError:
                # We've gone too far, and ran out of objects to follow.
                errmsg = "invalid path: {0!r}" \
                    " (fails at {1!r})".format(path, _failpt())
                raise OptionError(errmsg)
            # Do a bit of sanity checking.
            if strict and not isinstance(cur, strict_types):
                # This ensures that every step of the way, we're getting a
                # reasonable object.
                errmsg = "invalid path: {0!r} (strict; {1!r}; {2!r} isn't an" \
                    " acceptable type)".format(path, _failpt(), type(cur))
                raise TypeError(errmsg)
        else:
            # We finally finished iterating, thus, 'cur' is our desired
            # result...sort of.
            if isinstance(cur, SDRawInterface):
                # Point to the actual sdict instead.
                cur = cur._host()
            elif not raw and isinstance(cur, Option):
                # Do the usual fetching.
                cur = cur.get()

        # Return the result!
        return cur

    def _sanitize_name(self, name):
        # Keeping this short for now
        return name.lower() if name is not None else None

    @property
    def all_defaults(self):
        defs = AttrDict()
        for key in self:
            elt = self.raw[key]
            try:
                # See if we have a SettingsDict. If we do, we'll iterate down
                # through its defaults.
                defs[key] = elt.all_defaults
            except AttributeError:
                # We probably have an Option.
                defs[key] = elt.default
        return defs

    @property
    def defaults(self):
        defs = AttrDict()
        for key in self:
            elt = self.raw[key]
            try:
                defs[key] = elt.default
            except AttributeError:
                # It's not an Option
                pass
        return defs

    @property
    def groups(self):
        grps = []
        for k in self:
            x = self.raw[k]
            if isinstance(x, SettingsDict):
                grps.append(x)
        return grps

    # TODO: Consider being slightly more lenient with the definition for this?
    # Alternately: Keep both of these lists on hand as a running tally?
    @property
    def options(self):
        opts = []
        for k in self:
            x = self.raw[k]
            if isinstance(x, Option):
                opts.append(x)
        return opts

    # Considered all of these, but scrapped the ideas - what's being done right
    # now seems to work fine, so apparently doing so wasn't a case of bad
    # judgment
    ##def _get(self, key): return super(SettingsDict, self).__getitem__(key)
    ##def _set(self, key, item):
    ##  """Set a key in this dictionary without invoking callbacks."""
    ##  super(SettingsDict, self).__setitem__(key, item)
    ##def _setattr(self, attr, item):
    ##  """Set an attribute without invoking callbacks...."""
    ##  self.__dict__[key] = item
    def _init_raw(self):
        """Create and assign a .raw for the SettingsDict calling this."""
        raw = SDRawInterface(host=self)
        ##self._setattr("raw", raw)
        self.__dict__["raw"] = raw
    def _option_init_check(self, option):
        if not option.initialized:
            # This might not even need to be a conditional, but it's left
            # like this in case someone ever decides to do something
            # especially odd (which seems happen even when you explicitly try
            # to prevent people from being able to!)
            # In either case, the option wasn't initialized prior, so we'll
            # do so now if possible.
            cb = option.init_callback
            if cb:
                # If initialization failed it should throw an error, which
                # would bring this to a grinding halt anyway, so this isn't
                # as careless as it looks.
                cb()
                # May not need the separate property; it hasn't been used at
                # present, so....
                option.initialized = True
    def _set_name(self, name):
        self.__dict__["name"] = name
    # Included to wrap up the class, for proper folding in vim.
    pass


# Subclassing SettingsDict for this seems...kludgy. Formerly subclassed object.
class SDRawInterface(SettingsDict):
    """An object which exists to make it easier to access the settings in
    an instance of SettingsDict, by acting as a redirector residing in its
    .raw attribute.
    Not keyed for providing a save state for pickling or similar - the
    object exists purely for convenience reasons.
    For clarity: Iteration over raw settings should be done using the keys
    of the SettingsDict that owns this, but checked using this (via .raw)
    instead of the SettingsDict itself.
    An example would be using [sd.raw[k] for k in sd] to fetch all Options,
    where sd is, of course, a SettingsDict instance."""
    # TODO: Make these callable, invoking a variant of raw pathing.
    # Could potentially rework it so this is how normal pathing works.
    # ...
    # Considered making .raw.foo.bar call .raw("foo.bar"), which would do
    # something akin to sdict's path_get(), but in practice, this is a Bad
    # Idea unless it effectively resolves into .raw("foo")("bar") .
    # Really, the only benefit is that it allows for automatic error checking
    # of fetched types - which the caller can and SHOULD do themselves!

    # Always set during init. This is the object we're mirroring to.
    # ...or a weakref to it.
    _host = None

    def __init__(self, host):
        # Using weakrefs should prevent cyclical references.
        self.__dict__["_host"] = weakref.ref(host)

    def __repr__(self):
        dead, invalid = False, False
        subm = ""
        if self._host is None:
            subm = "INVALID"
            invalid = True
        elif self._host() is None:
            subm = "dead"
            dead = True

        host = None
        if invalid:
            fmt = "<{subm} {cls}>"
        elif dead:
            host = self._host
            fmt = "<{cls} for {host}>"
        else:
            host = self._host()
            fmt = "<{cls} for {host}@{id}>"
        fmt = fmt.format(cls=type(self).__name__, subm=subm,
                         host=type(host).__name__, id=id(host)
                         )
        return fmt

    # Both of these two bypass the methods SettingsDict defines so that the
    # ACTUAL object is affected or retrieved.
    def __setitem__(self, key, item):
        # 2012-10-30T14:08-06:00: Added this so an Option wouldn't go
        # without being initialized in spite of being set properly....
        if isinstance(item, Option):
            self._host()._option_init_check(item)
        return super(SettingsDict, self._host()).__setitem__(key, item)

    def __getitem__(self, key):
        obj = super(SettingsDict, self._host()).__getitem__(key)
        if isinstance(obj, SettingsDict):
            # If we have a SettingsDict, keep the .raw chain going - e.g.,
            # sd1.raw.sd2.sd3 is the same as sd1.sd2.sd3.raw.
            return obj.raw
        return obj

    # TODO: Redo this stuff based off of AttrDict's changes...make way for
    # groups?
    # TODO: Check if this causes wonkiness with things expecting the wrong
    # error.
    __getattr__, __setattr__ = __getitem__, __setitem__
    # Deletion using .raw instead of the main dict is to be encouraged for
    # the purpose of consistency
    def __delitem__(self, key):
        # Note that we skip SettingsDict in the resolution process.
        # In truth, this might be unwise....
        return super(SettingsDict, self._host()).__delitem__(key)
    __delattr__ = __delitem__

    def __getfromhost(self, attr):
        # Get a value from the host.
        return getattr(self._host(), attr)

    @property
    def name(self): return self.__getfromhost("name")

    # Marks the end of the subclass.
    pass


class SettingsGroup(SettingsDict):
    # Potentially, we could shove all sub-dicts into this so that .raw knows to
    # pass them instead or something, but...this causes the same issue as
    # before, i.e., being unable to figure out when to stop passing the next
    # .raw.
    # So, it seems sanest to just discourage .raw usage until you need it.
    # E.g. settings.debug.verbosity.raw.level or something, instead of having
    # 'raw' show up earlier.
    pass
    # Included to wrap up the class, for proper folding in vim.
    pass



