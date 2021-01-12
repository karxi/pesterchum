# -*- coding=UTF-8; tab-width: 4 -*-
from __future__ import division

# A library to help manage Pesterchum's egregious issues with themes.

from PyQt4 import QtGui, QtCore

import collections, copy, fnmatch, json, os, string, sys, traceback
import itertools
import ostools
from parsetools import ThemeException
from stylestruct import ThemeStruct
from pnc.dep.attrdict import AttrDict

try:
    basestr = basestring
except NameError:
    # Python 3.
    # This script really isn't made to work with it, but it saves us a bit of
    # trouble if we ever decide to port it.
    basestr = str

_datadir = ostools.getDataDir()

import logging
#~logging.basicConfig(level=logging.ERROR)
logging.basicConfig(level=logging.WARNING)

logbak = []

# TODO:
# A lot of the Styler class is just garbage. Figure out how to compose
# everything into a Pesterchum-wide stylesheet, not necessarily Pythonically
# (that can come later), and apply it to the top-level window.

class Styler(object):
    """A mixin meant to provide a Pesterchum object with Theme support."""

    # The string that gets formatted/has the Theme applied to it.
    stylesheet_template = ""
    # A path through a Theme to a ready-to-use stylesheet.
    stylesheet_path = ""
    # NOTE: We have to construct a stylesheet ourselves....
    current_stylesheet = ""

    # Subclasses should supply this.
    # An iterable of keys (e.g. "toasts/title/style") that this particular
    # object requires. Expect to be considered with that of its children.
    # NOTE: Might implement a hook to refresh or notify upon changes.
    needed_styles = set()
    # Extra things (but ones we have defaults for).
    optional_styles = set()

    # Replaces 'layout'.
    # The layout class that's used by default. (Optional.)
    # Not sure if I'll keep this.
    organizer = None

    # Instance of the Theme object we're using
    # NOTE: This should be a subset with just the keys we need, shouldn't it?
    theme = None

    def __init__(self, *args, **kwargs):
        # This class is meant to pick up vars from another class that
        # implements it.
        if not self.needed_styles:
            self.needed_styles = self.get_needed_styles()
        super(Styler, self).__init__(*args, **kwargs)

    def get_needed_styles(self):
        # We expect a string for this...fetching from stylesheet_template.

        if self.stylesheet_path:
            needfrom = (self.stylesheet_path,)
        elif self.stylesheet_template:
            needfrom = self.stylesheet_template
            # Returns a list.
            needfrom = self.parse_needed_styles(needfrom, raw=False)
        return set(needfrom)

    def setTheme(self, theme, recurse=True):
        # TODO: Apply the stylesheet and such.
        # If there are other widgets 'owned' by this window, call setTheme on
        # all of them too (unless 'recurse' is False).
        self.setStyleSheet(theme)
        if recurse:
            for child in self.children():
                # I'm not sure if I should have it recurse, it depends on how
                # deep the list of children goes on each object.
                # NOTE: Not all children will have this class, and thus
                # setTheme. We should probably be ready to do all the recursion
                # ourself, especially since 'parents' are supposed to exercise
                # a measure of control over smaller objects.
                child.setTheme(theme, recurse=recurse)

    def construct_stylesheet(self, *args, **kwargs):
        # TODO. This might mean defining logic on each of these classes to
        # fetch the theme information its children use and incorporate it into
        # its own style sheet, which I'm kind of okay with.
        pass

    class NeededStyles(dict):
        """Tracks which style keys are checked, and thus which ones are needed,
        compiling them into a set."""
        # Pretend to be a style and run through the theme-acquisition process
        # as usual.
        # NOTE: I'm not sure what this should inherit from. It's effectively a
        # set pretending to be a dict of dicts.
        # NOTE: This is a VERY weird class. Expect changes.
        checked_keys = None
        # Makes the object log all attempted accesses - sets, gets, dels, 'in'
        # checks - everything.
        # TODO: Test this more extensively.
        log_all = False
        # Whether or not this has received all of the checks it needs to, and
        # thus is ready to be accessed "normally".
        finalized = False
        # A Theme to return values from.
        passthru = None

        def __init__(self, passthru=None, log_all=False):
            self.checked_keys = set()
            self.passthru = passthru
            self.log_all = log_all
            self.finalized = False
        def _log_key_access(self, op, key, *args, **kwargs):
            logall, final, passto = self.log_all, self.finalized, self.passthru
            if final:
                # Ignore log_all if we're already finalized
                logall = False
            # Is this a reserved name?
            reserved = (key.startswith('__') and key.endswith('__'))
            # If it's a 'get' attempt, we log it, unless we're already
            # finalized or it's a reserved keyword.
            logit = (logall or (op == 0 and not (final or reserved)))
            # The function we hand off to, if we have one
            pthru = None

            # This is messy/dangerous, but oh well
            if final and op != 0:
                # No modifying finalized objects.
                raise AttributeError("Already finalized")
            if logit:
                # Log our attempted access.
                self.checked_keys.add(key)

            if op > 0:
                # Set.
                if passto and not reserved:
                    pthru = self.passthru.__setitem__
            elif op < 0:
                # Delete.
                if passto and not reserved:
                    pthru = self.passthru.__delitem__
            else: # op == 0
                # Get.
                if passto:
                    pthru = self.passthru.__getitem__
            if pthru is not None:
                return pthru(key, *args, **kwargs)
            else:
                return True


            if self.passthru is not None:
                if op > 0 and self.finalized:
                    # Set.
                    pthru = self.passthru.__setitem__
                elif op < 0 and self.finalized:
                    # Delete.
                    pthru = self.passthru.__delitem__
                else: # op == 0
                    # Get.
                    pthru = self.passthru.__getitem__
                    if not self.finalized:
                        self.checked_keys.add(key)
                # Pass through.
                return pthru(key, *args, **kwargs)
            if self.finalized:
                # TODO: Make passthru work above this??
                # Actually fuss with things.
                if op > 0:
                    # Set.
                    # Ignore the value.
                    self.checked_keys.add(key)
                elif op < 0:
                    # Delete.
                    self.checked_keys.discard(key)
                else: # op == 0
                    # Get.
                    return key in self
                return
            elif (op > -1 or self.log_all) and not (
                    key.startswith("__") and key.endswith("__")
                    ):
                self.checked_keys.add(key)
            # Dummy response.
            return True
        __getitem__ = lambda s, *x, **y: s._log_key_access( 0, *x, **y)
        __setitem__ = lambda s, *x, **y: s._log_key_access( 1, *x, **y)
        __delitem__ = lambda s, *x, **y: s._log_key_access(-1, *x, **y)
        # TODO: Consider __iter__ so it converts into a set properly.

        def finalize(self):
            """Set this object so it stops pretending to be something it is
            decidedly not."""
            self.finalized = True

        def __contains__(self, key):
            # Check if we have a key that begins with this (and thus includes
            # it).
            # This gives us a list...sorting should put the shorter keys first.
            to_check = sorted(self.checked_keys)
            if self.log_all and not self.finalized:
                # Log this access before we begin, but keep it out of our
                # working list.
                self.checked_keys.add(key)
            for path in to_check:
                #~if key.startswith(path):
                #~    return True
                pathbits = path.split('/')
                keybits = key.split('/')
                if len(keybits) < len(pathbits):
                    # This one can't possibly match; the tested key is higher
                    # in a directory structure than the one we're using to
                    # validate. (I.e. it could contain our validator.)
                    continue
                # Considered zip()-ing this, but it'd make the lengths
                # equal....
                for i, pb in enumerate(pathbits):
                    if keybits[i] != pb:
                        # No match; this is a split in the path.
                        break
                else:
                    # We've hit the limit of the already-extant key.
                    # Because that means we're going deeper into the path than
                    # it, the old key contains the new one.
                    return True
            return False

        def __repr__(self):
            return "{0}({1!r})".format(
                    type(self).__name__,
                    self.checked_keys
                    )

        @staticmethod
        def _stopper_list(x, y, equalize=False):
            """Put a None 'stopper' at the end of whichever list is
            shorter than the other."""
            # AKA 'equalize'.
            x, y = list(x), list(y)
            xl, yl = len(x), len(y)
            if xl > yl:
                shorter, longer = y, x
                diff = xl - yl
            elif xl < yl:
                shorter, longer = x, y
                diff = yl - xl
            else:
                # Same length.
                return x, y
            if equalize:
                shorter.extend([None] * diff)
            else:
                # Just a stopper for zip()
                shorter.append(None)

            return x, y

        def _purge_deep_links(self, log_all=None):
            """Clear all superfluous links from this object.
            Returns the number of links pruned.
            
            Does nothing if log_all is set."""
            if log_all is None:
                log_all = self.log_all
            if log_all:
                return -1

            def zipcmp(cb, vb):
                """Compare two lists of path chunks to see which is more exact,
                and tells the loop which (if any) list to keep.
                Length 0 lists are automatically pruned."""
                # cb = check bits
                # vb = validator bits
                # 'v' is the already-extant key, 'c' is the one being
                # evaluated.
                # We give a tuple with whether or not we should keep each
                # value.
                keepchk, keepvld = True, True
                if len(cb) < 1:
                    keepchk = False
                if len(vb) < 1:
                    keepvld = False
                # Either way, we can't compare if either of those is the case.
                if not (keepchk and keepvld):
                    # Short-circuit.
                    return (keepchk, keepvld)

                for c, v in zip(*self._stopper_list(cb, vb)):
                    # Since we preempted length 0 lists, this is okay
                    if c is None:
                        # Checked value is shorter/worth more.
                        keepvld = False
                        break
                    elif v is None:
                        # Validator value is shorter/worth more.
                        keepchk = False
                        break
                    elif c != v:
                        # They've diverged; they handle different paths.
                        ##keepchk = keepvld = True
                        break

                return (keepchk, keepvld)

            # Of course we can't use the normal interface to check this....
            to_check = sorted(self.checked_keys)
            # Format: {"key/goes/here": [keep?, ("key", "goes", "here")]}
            links = dict()
            for key in to_check:
                # Assume we keep them all by default
                links[key] = [True, key.split('/')]

            # We're prepared, so go through and check them now.
            for key in to_check:
                keybits = key.split('/')
                # So we can check depth
                keyblen = len(keybits)

                # Run it against the others in the file.
                for lnk, lnkinfo in links.items():
                    lnkkeep, lnkbits = lnkinfo
                    lnkblen = len(lnkbits)
                    if not lnkkeep:
                        # Just skip this entry, it's already on its way out
                        continue
                    # Compare the two.
                    keykeep, lnkkeep = zipcmp(keybits, lnkbits)
                    # Find invalid entries and mark them as garbage.
                    if not keykeep:
                        links[key][0] = False
                    if not lnkkeep:
                        links[lnk][0] = False
                    # That excludes them from being used as validators and
                    # marks them to be purged.

            # Actually purge the unnecessary links.
            purged = 0
            for key in links:
                if not links[key][0]:
                    self.checked_keys.discard(key)
                    purged += 1

            # And now we're done!
            return purged

    @classmethod
    def parse_needed_styles(cls, ss, raw=False):
        """Parse a stylesheet block for its format-replaced keys and compile
        them into a list of necessary keys/keys to watch.
        
        If 'raw', give the actual object used to find this out instead of
        parsing it ourseles."""

        # We cheat here, by just formatting the styles with a dict that logs
        # accesses. Since we can *use* Pesterchum's theme format now, we don't
        # have to do much processing.
        stylechecker = cls.NeededStyles(log_all=True)

        # We have the false theme to provide. Now....
        ss.format(style=stylechecker)
        # Don't even bother saving the output.

        # Set it up to be read.
        stylechecker.finalize()
        
        if raw:
            return stylechecker
        else:
            return sorted(stylechecker.checked_keys)


# TODO: !!!!!!! REWRITE THIS SO ITS INHERITANCE ACTUALLY *WORKS*
# It's not usable until you do!!
class ThemeBase(AttrDict):
    """A class meant to provide the basics for the way Theme objects handle
    access and storage.
    This is also occasionally used to present the appearance of being a Theme
    for the purposes of data access."""

    inherits = None

    # Calls from this get rebounded from AttrDict...so we need a way to
    # indicate they're being called from this function, and using the inspect
    # module for things like this isn't necessary.
    def __getitem__(self, key):
        # Do our weird splitting thing.
        # This *should* do the trick....
        return self._process_theme_key(key, action=0, func="__getitem__")
    def __setitem__(self, key, value):
        self._process_theme_key(key, value, action=1, func="__setitem__")
        return
    def __delitem__(self, key):
        self._process_theme_key(key, action=-1, func="__delitem__")
        return


    def _proc_inheritance(self, key):
        #~try:
        #~    thm = self.inheritedTheme
        #~    rv = thm[key]
        #~except KeyError:
        #~    try:
        #~        thm = self.defaultTheme
        #~        rv = thm[key]
        #~    except KeyError:
        #~        raise KeyError("Key {0!r} not found!!".format(key))

        #~return rv
        if key == "inherits":
            return super(ThemeBase, self).__getattribute__(key)

        if "inheritedTheme" in self:
            # Fall back on our parent.
            return self.inheritedTheme[key]
        elif "defaultTheme" in self:
            # Fall back on the most basic Theme we have.
            return self.defaultTheme[key]
        else:
            raise KeyError("Key {0!r} not found!!".format(key))

    def _process_theme_key(self, key, value=None, action=0,
            caller=None, func=None):
        """_process_theme_key(key[, value][, action]):
        Handles the legwork for accessing our dict.
        'action' >  0 => Set variable
        'action' == 0 => Get variable
        'action' <  0 => DELETE marked key"""

        logbak.append(
            "Processing theme key: {0!r} ({1!r} / {2}); ({3!r} / {4})".format(
            key, caller, id(caller), self, id(self))
            )
        logbak.append("{0!s: <4}, {1!r}, {2!r}".format(self, value, action))
        if func is None:
            src = self
        else:
            src = None
        if isinstance(keys, basestr):
            keys = key.split("/")

        if caller is self:
            # Prevent infinite recursion.
            if action == 0:
                return super(ThemeBase, self).__getattr__(key)
            else:
                # We...shouldn't be called by ourself like this unless we're
                # specifically trying to fetch a value inside of ourself.
                # Moreover, we SHOULD only be doing it with one key segment.
                raise ValueError("wtf just happened???")
        keylist = keys[:]
        # We have a place to start, now begin iterating down.
        # The number of iterations we've had.
        i = 0
        # Start with ourself and work our way down.
        delve = self
        safety = None
        hole = None
        # We should always have at least one key....
        while keys:
            # Keep a record of where we were before.
            safety = (delve, hole)
            # Figure out where we're going.
            hole = keys.pop(0)
            
            try:
                if i > 0 or True:
                    # Dig a hole and jump in.
                    #~delve = delve[hole]
                    # TODO: KLUDGE! We're having infinite recursion issues....
                    delve = delve._process_theme_key(hole, caller=self)
                elif i < 1:
                    # First one, which means we're jumping into ourself. This
                    # presents an infinite recursion issue, so we have to use a
                    # bit of alternative handling.
                    delve = super(ThemeBase, delve).__getattr__(hole)
            except KeyError:
                # The key we want doesn't exist.
                if action > 0:
                    # We have a payload to deliver.
                    #~delve[hole] = value
                    setattr(delve, hole, value)
                    return
                elif action == 0:
                    # We're just fetching the variable.
                    # This function shouldn't ever fail, since we'll "always"
                    # have a functional defaultTheme backing us up.
                    return self._proc_inheritance(key=hole)
                elif action < 0:
                    # We're too far in to fill the hole.
                    raise
            #~finally:
            # Increment.
            i += 1
        else:
            # We've exhausted our list of keys.
            # TODO: How the hell did we get here? Are we setting something? If
            # we're retrieving a value, that's no problem - the script already
            # handles that....
            if action < 0:
                # Fill the hole.
                # Safety still contains the before-last info, so we'll use it.
                sinkhole, loc = safety
                # Silly names for silly variables.
                # Delete the entry.
                del sinkhole[loc]
                return
            elif action == 0:
                # We're here purely to fetch data.
                return delve
            elif action > 0:
                # More silly variable names.
                sinkhole, loc = safety
                sinkhole[loc] = value
                return

        return delve

class Theme(ThemeBase):
    """A Pesterchum theme, to be used to change the appearance of the
    client."""

    # Kludges, kind of. These are fallbacks from the old script.
    # We can't include them due to the way this has been reworked.
    #~inheritedTheme = None
    #~defaultTheme = None

    # Later on I might start metaclassing this.
    def __init__(self, theme, name=None):
        # ...
        cls = type(self)

        # We need a way to infer the theme on our own, but w/e.
        # Maybe we should forcefully set this, by touching __dict__?
        self.name = name

        # This won't work because we rely on the keys being absent.
        #~# Set up a framework that will be filled.
        #~self.update(ThemeStruct._process_needs(generator=AttrDict))

        # Note that update() alone would be a shallow copy; we need a deep one.
        self.update(copy.deepcopy(theme))

        try:
            self.defaultTheme
        except (AttributeError, KeyError):
            # We don't already have a default initialized for our class.
            # Set a placeholder to add the key *before* we go about making an
            # object that will check if that key exists. (Read: Prevent an
            # infinite loop.)
            cls.defaultTheme = None
            cls.defaultTheme = cls.from_name("pesterchum")

        if "inherits" in self:
            # 'inherits' is the name, 'inheritedTheme' is the actual Theme
            self.inheritedTheme = self.from_name(self.inherits)

    @classmethod
    def _convert_to_attrdict(cls, tree, heap=None):
        # Convert 'tree' to a series of AttrDicts.
        result = ThemeBase()
        #~# Pass on important variables...guh.
        #~if "inheritedTheme" in tree:
        #~    result.__dict__["inheritedTheme"] = tree["inheritedTheme"]
        #~if "defaultTheme" in tree:
        #~    result.__dict__["defaultTheme"] = tree["defaultTheme"]

        if heap is None:
            # This is where we put the things we've already touched.
            heap = set()

        heap.add(id(tree))

        for key in tree:
            val = tree[key]
            idx = id(val)
            if idx in heap:
                # We've already done something with/to this.
                continue
            else:
                # Record this.
                heap.add(idx)
            if isinstance(val, collections.MutableMapping):
                # We have a dict or something. Thus, recurse.
                val = cls._convert_to_attrdict(val, heap=heap)
            result[key] = val

        return result

    @staticmethod
    def _potential_filename(name):
        # ...
        logging.debug("Trying to find {0!r}...".format(name))
        possiblepaths = (
                os.path.join(_datadir, "themes", name),
                os.path.join("themes", name),
                os.path.join(_datadir, "themes", "pesterchum"),
                os.path.join("themes", "pesterchum")
                # This basically means that
                # %LOCALAPPDATA%/pesterchum/themes is a usable, viable folder.
                # TODO: Make it add that somewhere, so it's more obvious?
                # NOTE: Test to make sure I'm *right* first....
                )

        logging.debug("Path selection: {0!r}".format(possiblepaths))
        for p in possiblepaths:
            if os.path.exists(p):
                path = p
                break
            logging.debug("Path invalid: {0!s}".format(p))
        else:
            logging.warning("Failed to locate theme {!r}.", name)
            # "themes/pesterchum"
            path = possiblepaths[-1]
        logging.debug("Path selected: {0!s}".format(path))
        return path

    @classmethod
    def from_name(cls, name):
        """Fetches a file by name, searching the relevant subdirectories and
        loading it as a Theme."""
        # Gets the file, passes on to the file loader.
        fn = cls._potential_filename(name)

        # We've figured out where the theme we want is, so pass handling on to
        # the function that deals with this.
        inst = cls.from_file(fn, name)
        return inst

    @classmethod
    def from_file(cls, filepath, name=None):
        """Creates a Theme object from a file."""
        # TODO: Metaclass this, it'll probably make your life easier.
        # ... *Probably*.

        # For later.
        def _path_hook(d):
            for (k, v) in d.iteritems():
                if isinstance(v, unicode):
                    s = string.Template(v)
                    d[k] = s.safe_substitute(path=filepath)
            return d

        if name is None:
            # Fetch the last component of the path and use it as a name
            name = os.path.basename(filepath)

        style_js = os.path.join(filepath, "style.js")
        
        try:
            with open(style_js) as fp:
                theme = json.load(fp, object_hook=_path_hook)
        except IOError as err:
            logging.error("Failed to load theme: {!s}", err)
            logging.error(traceback.format_exc())
            # Fall back....
            theme = json.loads("{}")

        theme = cls._convert_to_attrdict(theme)

        inst = cls(theme=theme, name=name)
        return inst

    def validate(self):
        # this is an old relic
        for n in self.needs:
            try:
                self[n]
            except KeyError:
                raise ThemeException("Missing theme requirement: %s" % (n))



class Texter(object):
    """A class that handles sending and receiving text, as well as displaying
    it.
    Basically, a glorified command prompt style class."""

    # These will eventually be phased out.
    @property
    def textArea(self): return self.text.area
    @textArea.setter
    def textArea(self, value): self.text.area = value
    @property
    def textInput(self): return self.text.input
    @textInput.setter
    def textInput(self, value): self.text.input = value
    @property
    def history(self): return self.text.history
    @history.setter
    def history(self, value): self.text.history = value

    # Storage for the items that make this class work.
    text = AttrDict()
    # Typically seems to be of type QtGui.QVBoxLayout.
    # Replaces 'layout'. Contains the class used to *make* our layout.
    # NOTE: Probably going to remove this, it copies a PyQt method.
    organizer = None
    # This may get made into a property so I don't have to keep telling
    # everything how to figure out where the topmost window is.
    mainwindow = None
    # If this is None/False (either or really, but the latter's more explicit),
    # then we don't have tabs to worry about.
    # Otherwise, it's usually a QtGui.QTabBar.
    tabs = None

    # A container for shortcuts.
    # I don't think there's a definition for the constants we need for
    # QShortcut yet - so all we need to remember is that we want 3, for
    # the WidgetWithChildrenShortcut context. (This is why it's set on the
    # window.)
    shortcuts = None
    # A container for actions.
    # Probably an AttrDict.
    actions = None

    def __init__(self, theme, parent=None):
        if parent is None:
            # Not sure if this works, but it's worth a try
            parent = self.parent()
        super(Texter, self).__init__(parent)

        self.text = AttrDict(dict(area=None, input=None, history=None))
        self.shortcuts = AttrDict()
        self.actions = AttrDict()

    def applyTheme(self):
        # Set the theme on this. Don't bother with children - instead,
        # incorporate their themes into this one's sheet??
        # Do sheets inherit?...
        # NOTE / TODO - this is already covered by Styler.setTheme
        pass

class PesterBaseDialog(Styler, QtGui.QDialog):
    """A basic dialog class for Pesterchum."""
    # Used for things like the quirk testing window
    # I'll just impement Texter and set up the quirk tester to implement it
    # despite the fact that it's a QDialog
    pass

class PesterBaseWindow(Styler, Texter, QtGui.QFrame):
    """A basic window class for Pesterchum."""
    # I might have this inherit from something higher up, but I'm worried about
    # making the MRO testy... :p

    # This needs to keep track of its children.
    # For a few reasons - so they can be themed, so it can pass around events
    # to them...

    def __init__(self, theme, parent=None):
        if parent is None:
            # Not sure if this works, but it's worth a try
            parent = self.parent()
        super(PesterBaseWindow, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_QuitOnClose, False)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

        # No better way to get this, yet.
        self.mainwindow = parent.mainwindow

class PesterTextArea(QtGui.QTextEdit):
    pass

class PesterTextInput(QtGui.QLineEdit):
    pass

def _compose_singular_stylesheet(theme):
    # karxi: Still VERY WIP.
    # ....
    # Basically write code that composes/formats a list of things into
    # something we can use. This'll be used in main once we switch....
    # TODO: Make initTheme call changeTheme as a standard, or something.
    #
    # Organize by class/appearance? Maybe? ... Eh, just class for now.
    # Each will be pushed through something akin to '.format(style=theme)',
    # like many other things are right now.

    # Open this into a set of kwargs, and assign the whole thing to 'style'.
    #~fmtargs = AttrDict(dict())
    fmtargs = AttrDict({
        "style": theme,
        "name": getattr(theme, "name", None),
        "convo": theme["convo"],
        "main": theme["main"],
        "memos": theme["memos"]
        })

    # MACROS~
    def pacn(*args):
        """pacn("x", "y", "z", ...) ==> "x, x*, y, y*, z, z* ", ..."""
        # Parent And Children
        # Just return "x, x *", basically.
        rv = []
        arglist = args
        # karxi: I'm doing this in a silly way just to demonstrate a neat
        # Python feature.
        # Duplicate each entry...
        arglist = itertools.chain(*map(lambda dup: (dup, dup), arglist))
        # ...and flatten them down so we can process them with zip().
        arglist = list(arglist)
        # ========
        # Said feature:
        # ========
        # Turn our argument list into a set of tuples.
        arglist = zip(*([iter(arglist)] * 2))
        # Confused? Assume x = iter(args). Doubling that list gives us
        # "[x, x]", which means zip() calls the iterator twice for each tuple
        # it's constructing. Iterators keep track of their next item
        # internally, so zip() is advancing their count twice for every tuple
        # it creates.
        # This works with a multiplier of any size. Isn't Python great?~
        #
        # Anyway....
        for i1, i2 in arglist:
            rv.append("{0!s}, {1!s} *,".format(i1, i2))
        else:
            # Remove the last comma.
            rv[-1] = rv[-1][:-1]
        # Join it all together so it can be used as a specifier.
        rv = ' '.join(rv)
        # Put a space at the end so we don't have to do that manually. :P
        rv += ' '
        return rv

    # Screw it, making this into subfunctions. This is an expensive function
    # that shouldn't be called often anyway.
    # Make sure to pass the keys of the theme as args, plus 'style' (the theme
    # itself).
    # As a note, "style.main.chums.size[0]" could be used here, as an example.
    # The choice is mostly just personal preference, though '/' format is a
    # tiny bit longer.
    def ss_chumArea():
        ss = [
            "chumArea {{",
            # Height is hard-set
            "   min-width:  {main.chums.size[0]};",
            "   max-width:  {main.chums.size[0]};",
            "   min-height: {main.chums.size[1]};",
            "   max-height: {main.chums.size[1]};",
            # We're kinda trusting this part of things more than I'd like
            "   {main.chums.style}",
            "}}"]
        if "main/chums/scrollbar" in theme:
            ss += [
                # 5 (+1) entries
                "chumArea QScrollBar {{ {main.chums.scrollbar.style} }}",
                "chumArea QScrollBar::handle {{",
                "   {main.chums.scrollbar.handle} }}",
                "chumArea QScrollBar::add-line {{",
                "   {main.chums.scrollbar.downarrow} }}",
                "chumArea QScrollBar::sub-line {{",
                "   {main.chums.scrollbar.uparrow} }}",
                "chumArea QScrollBar::up-arrow {{",
                "   {main.chums.scrollbar.uarrowstyle} }}",
                "chumArea QScrollBar::down-arrow {{",
                "   {main.chums.scrollbar.darrowstyle} }}"
                ]
        return ss

    def ss_console():
        ss = [
            "ConsoleWindow {{",
            "   min-width: 400; min-height: 600; }}",
            pacn("ConsoleWindow") + "{{ {convo.style} }}",
            pacn("ConsoleText") + "{{ {convo.textarea.style} }}",
            pacn("ConsoleInput") + "{{ {convo.input.style} }}",
            pacn("ConsoleText", "ConsoleInput") + "{{",
            # We force this for the sake of having a monospace font.
            "   font-family: 'Courier'; }}"
            ]
        if "convo/scrollbar" in theme:
            ss += [
                "ConsoleWindow QScrollBar:vertical {{",
                "   {convo.scrollbar.style} }}",
                "ConsoleWindow QScrollBar::handle:vertical {{",
                "   {convo.scrollbar.handle} }}",
                "ConsoleWindow QScrollBar::add-line:vertical {{",
                "   {convo.scrollbar.downarrow} }}",
                "ConsoleWindow QScrollBar::sub-line:vertical {{",
                "   {convo.scrollbar.uparrow} }}",
                "ConsoleWindow QScrollBar:up-arrow:vertical {{",
                "   {convo.scrollbar.uarrowstyle} }}",
                "ConsoleWindow QScrollBar:down-arrow:vertical {{",
                "   {convo.scrollbar.darrowstyle} }}"
                ]

            # ...huh. That was pretty simple.
            # The console might get changed later.

    def ss_mainwin():
        ss = [
            "QFrame#main {{ {main.style} }}",
            # Gotta be careful with this.
            "QMenuBar#mainmenu, QMenuBar#mainmenu * {{",
            "   background: transparent; }}",
            "QMenuBar#mainmenu {{ {main.menubar.style} }}",
            "QMenuBar#mainmenu::item {{",
            "   {main.menubar.menuitem} }}",
            "QMenuBar#mainmenu QMenu {{",
            "   {main.menu.style} }}",
            "QMenuBar#mainmenu QMenu::selected {{",
            "   {main.menu.selected} }}",
            "QMenuBar#mainmenu QMenu::disabled {{",
            "   {main.menu.disabled} }}",
            "QLabel#moodslabel {{ {main.moodlabel.style} }}",
            "QLabel#myhandlelabel {{ {main.mychumhandle.label.style} }}",
            "QPushButton#addchumbtn {{ {main.addchum.style} }}",
            "QPushButton#newpesterbtn {{ {main.pester.style} }}",
            "QPushButton#blockbtn {{ {main.block.style} }}"
            ]
        if "main/addchum/pressed" in theme:
            ss += [
                "QPushButton#addchumbtn:pressed {{ {main.addchum.pressed} }}"
                ]
        if "main/pester/pressed" in theme:
            ss += [
                "QPushButton#newpesterbtn:pressed {{ {main.pester.pressed} }}"
                ]
        if "main/block/pressed" in theme:
            ss += [
                "QPushButton#blockbtn:pressed {{ {main.block.pressed} }}"
                ]
        return ss
    
    sheet = []
    # Format every string in every sub-list.
    # Join every sub-list with newlines.
    # Join every result of this with newlines.
    def render_stylesheet(target=None, processing=None, memo=None):
        if target is None:
            # Grab from the parent function
            target = working
        # Note that 'fmtargs' is pulled from the parent too.
        if processing is None:
            processing = []
        if memo is None:
            memo = []
        tid = id(target)
        if tid in memo:
            # Don't iterate through something we've already touched.
            # TODO: Make this fetch from a hash, like deepcopy?
            return target
        # NOTE: We apply this earlier than the loop does as a safeguard against
        # infinite recursion.
        memo.append(tid)

        if isinstance(target, basestr):
            # We were passed a string, which means we iterated down far enough
            # to reach those.
            # Add to processing, then return.
            felt = target.format(**fmtargs)
            processing.append(felt)
            return felt
        # Okay, so it's not a string - try to iterate over it.
        # Note that this is only safe as long as we don't modify it....
        try:
            queue = iter(target)
        except TypeError:
            # This isn't iterable.
            return target
        # Otherwise....
        for elt in queue:
            eid = id(elt)
            if eid in memo:
                # We've already processed this.
                # NOTE: Skipping it means we're ignoring an entry....
                continue
            # Don't record the ID yet - we might have to recurse.
            memo.append(eid)

            if isinstance(elt, basestr):
                # We have a string! Format it.
                felt = elt.strip()
                felt = felt.format(**fmtargs)
                processing.append(felt)
                # Indicate that we worked on this.
                memo.append(eid)
                continue
            # We have something that's not a string.
            try:
                # Try to iterate over it anyway.
                rep = iter(elt)
            except TypeError:
                # We don't know how to use this, so skip it.
                continue
            # Go through the sublist.
            for n in rep:
                # Recurse.
                render_stylesheet(target=n, processing=processing, memo=memo)
                # This automatically adds to 'processing' and 'memo'.
            # Now its processed contents are part of the running list.
            # ...which means it's safe to fall through as before.
        else:
            # Eventually, we'll finish running through the queue.
            # Since processing is a merged list, we just return it.
            # Anything that called us and is paying attention to 'processing'
            # and/or 'memo' made sure to pass us something so it can look over
            # our work.
            #
            # By the end of this, we *should* have a 'flat' list of formatted
            # strings.
            return processing
    
    working = [
        # Wide-ranging changes
        [
            pacn("QDialog") + "{{ {main.default.style} }}"
            ],

        # convo.py
        # ....

        # logviewer.py
        # ....

        # pesterchum.py
        ## chumArea
        ss_chumArea(),
        ## Trollslum
        [
            pacn("trollSlum") + "{{ {main.trollslum.chumroll.style} }}",
            "TrollSlumWindow {{",
            "   min-width:  {main.trollslum.size[0]};",
            "   max-width:  {main.trollslum.size[0]};",
            "   min-height: {main.trollslum.size[1]};",
            "   max-height: {main.trollslum.size[1]};",
            # Should this inherit too?...
            "   {main.trollslum.style}",
            "}}",
            # NOTE: This might need to be made more specific.
            "TrollSlumWindow > QLabel {{ {main.trollslum.label.style} }}"
            ],

        ## Main window (PesterWindow)
        ss_mainwin(),

        # memo.py
        # ....

        # menus.py
        [
            ## PesterQuirkList
            "PesterQuirkList {{",
            "   min-width: 400; min-height: 200; }}",
            pacn("PesterQuirkList") + "{{",
            "   background: black; color: white; }}",
            pacn("QMessageBox#delquirkwarning") + "{{",
            "   {main.defaultwindow.style} }}",
            ## QuirkTester
            # Note that these use PesterText and PesterInput.
            "QuirkTester {{ min-width: 350; min-height: 300; }}",
            pacn("QuirkTester") + "{{ {main.defaultwindow.style} }}",
            ## PesterQuirkTypes
            "PesterQuirkTypes {{ min-width: 500, min-height: 310; }}",
            pacn("PesterQuirkTypes") + "{{",
            "   {main.defaultwindow.style} }}",
            pacn("PesterQuirkTypes > QListWidget") + "{{",
            "   color: white; background-color: black; }}",
            ## PesterChooseProfile
            ## PesterChooseQuirks
            ## PesterChooseTheme
            ## PesterMentions
            ## PesterOptions
            ## AboutPesterchum
            ## UpdatePesterchum
            # These are *almost* all QDialog, I believe.
            pacn(
                "PesterChooseProfile",
                "PesterChooseQuirks",
                "PesterChooseTheme",
                "PesterMentions",
                "PesterOptions",
                "AboutPesterchum",
                "UpdatePesterchum"
                ) + "{{",
            "   {main.defaultwindow.style} }}",
            ## PesterChooseProfile
            "PesterChooseProfile QLineEdit#setprofilehandle {{",
            "   min-width: 200; }}",
            "PesterChooseProfile QPushButton#setprofilecolor {{",
            "   min-width: 50; max-width: 50;",
            "   min-height 20: max-height:20; }}",
            ## PesterOptions
            # Just the idle setter.
            pacn("PesterOptions QSpinBox") + "{{",
            "   background: white; color: black; }}",
            ## PesterUserlist
            "PesterUserlist {{ {main.defaultwindow.style} }}",
            # TODO: Tweak this.
            #~"PesterUserlist RightClickList,",
            "PesterUserlist > RightClickList {{",
            "   {main.chums.style} }}",
            # This *should* work, but may need tweaked
            "PesterUserlist RightClickList * {{",
            "   color: {main.chums.userlistcolor}; }}",
            ## PesterMemoList
            "PesterMemoList {{",
            "   min-width: 460; max-width: 460;",
            # Maybe this will let us resize it down?? IDK.
            # TODO: Work on it later.
            "   min-height: 300;",
            "   }}",
            "PesterMemoList RightClickTree > * {{",
            "   color: {main.chums.userlistcolor}; }}",
            ## LoadingScreen
            "LoadingScreen, LoadingScreen * {{",
            "   {main.defaultwindow.style} }}",
            ## AddChumDialog
            pacn("AddChumDialog") + "{{",
            "   {main.defaultwindow.style} }}"
            ],

        # toast.py

        # Miscellaneous
        [
                # TODO: Test and tweak this.
                "*#errormsg, *#errormsg * {{ color: red; }}",
            ],

        [
            """xxxxx {{
            }}"""
            ]

        ]

    # So, whenever we've finished that...we move on from there to
    # processing. Thus....
    protosheet = render_stylesheet(working)
    # Since that formats everything on its own, we can just conjoin it all
    # ourselves.
    finalized = '\n'.join(protosheet)
    # That should be all...
    return finalized

# vim: set autoindent ts=4 sts=4 sw=4 tw=79 expandtab:
