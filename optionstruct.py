# vim: set autoindent ts=4 sts=4 sw=4 tw=79 expandtab:
# -*- coding=UTF-8; tab-width: 4 -*-
from __future__ import division, print_function

from pnc.sorganizer import Option, SettingsDict
try:
    from pnc.attrdict import AttrDict
except ImportError:
    # Fall back on the old location - just in case
    from pnc.dep.attrdict import AttrDict

try:
    basestr = basestring
except NameError:
    # Python 3...this is just convention, really.
    basestr = str

# This is how we write and store our options. Naturally, we'll have to parse
# them into the proper types while loading (or set up a decoder to do that for
# us).
# Save them to 'trollian.js'. :)
import json

import logging, os, sys
import os.path as osp

from collections import OrderedDict

logger = logging.getLogger(__name__)
# We don't setLevel because we're being imported.

# A way to (relatively) sanely access the main window. Set during our init.
MAINWIN = None

# karxi: A module to help set up an alternative options framework.
# NOTE: Keep in mind that this will need to output settings to pesterchum.js
# for compatibility purposes.
# This shouldn't be too hard to manage - just a bit awkward.
# In addition, a wrapper (pending code refactoring) would probably be wise to
# have, so that it can be used as a drop-in replacement for things like
# mainwindow.config.notifyOptions(), config.SIGNIN, and so on.
# Presumably, the wrapper can just *point* to a settings object....
#
# karxi: I'm not entirely sure how difficult this entire thing will be to get
# working.
#
# karxi: ChumMan (chummer.py?) and other namespace-esque things shouldn't go in
# this file, but they'll probably reference it. The intent is to make a module
# that any other module can reference to gain access to Pesterchum's current
# settings. (I may implement support for profile-specific overrides, though.)
#
# These settings should be stored in a separate file, of course. They can be
# compressed down into nearest equivalents for compatibility purposes.

# The main script should set this once we've finished loading, so any callbacks
# we set up here can actually be used properly.
#
# It's either that or we set up callbacks to actually initialize the base
# options - which is also reasonable.
_MAINWIN = None

# TODO: Set up the GUI rows for each option to put up their docstrings on
# mouseover.
# Set up a warning for those who try to mess with 'base'?



# These will probably need to overload 'default()'
class PesterConfigDecoder(json.JSONDecoder):
    def load_sd(self, fp, sd):
        """Load a file into a SettingsDict object."""
        # TODO: Try using object_hook instead of bothering with this!
        # It just has to init them using the SettingsDict and Option objects.

        # There'll be problems figuring out *what* is an option, so the best
        # way to handle this is:
        # ???: Convert all the keys to str
        # A:    For each key, check if that key exists in the main; if not, and
        #       strict, error out.

        # TODO: Consider giving Options special handlers or something...rather,
        # set up an 'etc' optional argument for them, for weird things like
        # this. opt.etc.priority, opt.etc.encoder, opt.etc.decoder, things like
        # that.

        # TODO: Since configWrapper can load like Pesterchum normally does it,
        # we can run through its dict ourselves, and set our 'base' that way.
        pass
    def convert_values():
        pass
    pass

class PesterConfigEncoder(json.JSONEncoder):
    def dump_sd(self, fp, sd):
        """Dump a SettingsDict object into a file."""
        # Assume we already got the fo/sdict for now, etc. Prototyping.
        # JSON dict. ... Should we do this, or just subclass default
        jsd = dict()
        # NOTE: It looks like this already serializes properly, because of how
        # the classes were written...huh.

        # We need to handle 'base' specially, because it is written to
        # pesterchum.js, whereas we use trollian.js.
        # TODO: ALL OPTIONS IN 'base' NEED TO NATURALLY CONVERT TO/FROM
        # PESTERCHUM'S DEFAULT TYPES!!!
        # They are compatibility options, so other options might overwrite
        # them when they're set. Those take precedent...
        # TODO!!!: Figure out how to resolve conflicts! ... Really, we just
        # need the config wrapper from the other file in here so we can make
        # 'base' into a suitable dict, converting new key names to old ones as
        # we need to,
        # ...sanest option seems to be to look back through the config and see
        # what we do and do not need to carry over.
        # Write a function that handles conflicts between the old and new
        # files; if an Option is just set to its default, override it with the
        # compatibility version.

        # TODO TODO TODO ffs - just add an 'etc={"supporting":
        # ("chums.colored_chum_names", "gui.flash_on_msg")}' or something like
        # that!!
        # 'etc=dict(supporting=("chums.colored_chum_names",
        #                       "gui.flash_on_msg")
        # TODO: Better idea - just subclass Option (CompatOption), add
        # 'supporting' explicitly. :/
        pass
    pass

# A lot of these specify string-style paths. Gotta write a function to work
# with those. (Use reduce()?)
def CompatOption(Option):
    """An option representing a Pesterchum base setting. Contains extra
    information to allow Pesterchum's older style to safely coexist with the
    newer implementation."""
    supporting = tuple()
    def __init__(self, *args, **kwargs):
        self.supporting = kwargs.pop("supporting", tuple())
        super(CompatOption, self).__init__(*args, **kwargs)
    pass

def PointerOption(Option):
    # The idea here is to allow an option to give the value of another option,
    # possibly with some processing for getting/setting. Seems like
    # compatibility stuff really... TODO: Evaluate specific use cases.
    pass



consts = AttrDict(dict(
    # Use for bit flag log setting
    LOG     = 1 << 0,   # 1
    STAMP   = 1 << 1,   # 2
    # Use for bit flag blink
    PBLINK  = 1 << 0,   # 1
    MBLINK  = 1 << 1,   # 2
    # Use for bit flag notfications
    SIGNIN  = 1 << 0,   # 1
    SIGNOUT = 1 << 1,   # 2
    NEWMSG  = 1 << 2,   # 4
    NEWCONVO= 1 << 3,   # 8
    INITIALS= 1 << 4    # 16
))

def import_from_pesterchum():
    """Import Pesterchum's settings for use in the more advanced 'Trollian'
    side of things."""
    # karxi: This is mostly to handle our initial upgrade, so settings are
    # preserved.
    # Thankfully, I already did most of the work in the configWrapper class.
    pass

def export_to_pesterchum():
    """Export the Trollian settings to pesterchum.js, chums.js, groups.js, and
    so on."""
    # This is how we handle compatibility, for the sake of sanity. Trollian
    # settings take priority.
    pass

def js_raw_process(cfgdict):
    # 

def js_decode_names(cfgdict):
    # Make the JSON setting keys/names into normal strings.
    # TODO: This.
    return

def js_group_reorder(cfgdict, order=None):
    """Recursively reorders options, including pathed ones, down to the order
    provided by the preset group definitions."""
    # Doesn't support recursion yet.
    # TODO: This.
    if order is None:
        global _groups
        order = list(_groups)

    # Just roll down through. So far, recursion isn't supported. ... So what we
    # need to do is get path specifiers - e.g. startswith(grp + '.') and sort
    # through them as lists, then compile those lists into a larger one.
    # Then their options can be fetched and returned as an OrderedDict.
    return

def js_categorize(cfgdict, key=None, memo=None):
    """Restructure "base.setting_here" style options to "base: {setting_here}"
    style ones.
    'cfgdict': The JSON dict to run through.
    'key': The key from the JSON dict that we're running down. 'None' means to
    run through all of them sequentially.
    'memo': The WIP OrderedDict tree to add our work to."""
    # TODO: This.
    # TODO: Just handle all the reordering/parsing stuff here, then let
    # js_drilldown do the dirty work.
    global _groups

    cats = list(_groups)
    if memo is None:
        memo = OrderedDict()

    # PROCEDURE
    # Get list of keys
    # Split them, by periods, into tuples
    # Sort them (according to groups or otherwise)
    pass

def js_drilldown(cfgdict, key, sdict=None):
    """Drills down through sdicts, setting options from the JSON config as
    it goes.
    'cfgdict': The JSON dict to run through.
    'key': The key from the JSON dict that we're running down. 'None' means
    to run through all of them sequentially.
    'sdict': The SettingsDict we should be working on."""
    # WARNING: Because of the way this works, full path writing actually
    # doesn't work. THIS FUNCTION actually supports it - however, because the
    # file reading function calls by group, so that groups can be loaded by
    # order of importance, this is functionally irrelevant.
    # TODO: For now, it's best to fall back on that method and let this
    # function do the heavy lifting. Skip the group stuff for now - we need to
    # get this up and running quickly.
    # For now, we're only supporting the full-on path writing. The rest can
    # come later!
    # TODO:
    # Use the JS dict. Check if the key pointed to is a dict. If so, try to
    # get it; if it's pointing to an sdict, iterate down into the js
    # hierarchy and repeat. If it's pointing to an Option, set it. If it
    # doesn't exist in the settings, error or ignore it (depending on
    # 'strict').
    # ... TODO:
    # RATHER: Use the JS dict. Try to path_get. If it's another sdict,
    # drill down into the JS dir. Log an error if it fails for whatever
    # reason.
    # If not, set it.

    global settings

    logger.debug("Drilldown running with key {key!r}".format(key=key))
    if sdict is None:
        # None provided, assume root.
        sdict = settings
    if key is None:
        for k in cfgdict:
            try:
                js_drilldown(cfgdict, k, sdict=sdict)
            except Exception:
                # Exception already logs in the called function
                pass
        return

    # We have a key. Check and see if it points to anything interesting/useful.
    try:
        val = cfgdict[key]
        target = sdict.path_get(key, raw=True)
    except KeyError:
        errmsg = "Invalid setting path: {sdp}[{path!r}]"
        # Find where we were when we tried to set this.
        # ... PathToSettingsDict
        ptsd = sdict.path_to(adjust=1)
        errmsg = errmsg.format(path=key, sdp=ptsd)
        logger.error(errmsg)
        raise KeyError(errmsg)

    # We have a valid path.
    # Go back and check the JSON against the object we got.
    if isinstance(val, dict):
        # Could be a settings registry.
        if isinstance(target, SettingsDict):
            # Iterate down into it!
            # Let it automatically drill down.
            js_drilldown(val, None, target)
            return
        else:
            # An Option...try to set it.
            # TODO: Better error checking here.
            try:
                target.set(val)
            except Exception as err:
                errmsg = "Drilldown: {err!s}: {msg!r}"
                errmsg = errmsg.format(err=err, msg=err.message)
                logger.warning(errmsg)
    else:
        # This must correspond to an Option...if not, TODO: Error checking.
        try:
            target.set(val)
        except Exception as err:
            errmsg = "Drilldown: {err!s}: {msg!r}"
            errmsg = errmsg.format(err=err, msg=err.message)
            logger.warning(errmsg)

    # We're done here.
    msg = "Set option: {sdp}[{path!r}]"
    msg = msg.format(path=key, sdp=sdict.path_to(adjust=1))
    logger.debug(msg)
    return

def load_settings(file=None):
    """Load the Trollian settings."""
    # This covers the actual loading, processing, and special cases.
    if file is None:
        # Only one potential path for now. ... In the future, might support
        # profile-specific overrides, or similar.
        paths = [
            osp.join(_datadir, "trollian.js")
        ]

    # ...
    try:
        with open(file, 'r') as fo:
            js_cfg = json.load(fo)
    except IOError:
        # TODO: Handle this.
        # ... Better: Just raise it and let the calling function try to import
        # defaults from the usual Pesterchum config.
        raise

    global _groups, settings
    # Actually assign settings.
    # Keys left to run through from the JS file. (Unnecessary?)
    js_left = js_cfg.keys()
    # Keys left to run through from the settings.
    sd_left = AttrDict()
    # For tracking failures
    missing, invalid = [], []
    # Erm...think this over a bit. More efficient would be to get every Option
    # below, then get every path_to(adjust=1) (so we don't get 'trollian' at
    # the top).
    # Then we can go through each and every one with path_get(raw=True) so we
    # get all the Option objects - cached, if you will.
    # 'opt_directory'
    # TODO: Scrap that, pathdrill needs to exist for it. Or /something/.
    #~for grp in _groups:
    #~    # For each division of options, *in order*....
    #~    sd_left[grp] = list()
    #~    ##for opt in settings.options:
    #~    optlist = settings.
    #~    for opt in settings:
    #~        sd_left[grp].append(opt.name)

    def pathdrill(sdict, adjust=1):
        """Fetches all the full paths for Options in a given sdict."""
        paths = []
        for opt in sdict.options:
            path = opt.path_to(adjust=adjust)
            paths.append(path)
        for sd in sdict.groups:
            # Repeat this for the following sdicts.
            paths.extend(pathdrill(sdict, adjust=adjust))
        return paths

    # Now, start iterating - again, using the order provided by _groups
    for grp in _groups:
        # Scrapped that part, we'll roll with the group in our settings.
        #~try:
        #~    # Get the stored dict we'll work with
        #~    js_sd = js_cfg[grp]
        #~except KeyError:
        #~    # Log this.
        #~    missing.append(grp)
        #~    logger.error("Failed to load group {0!r} (missing)".format(grp))
        #~    continue
        try:
            js_drilldown(js_cfg, grp, settings)
        except:
            pass
        #~# TODO: Straighten this out to use grp
        #~paths_by_group = {x: pathdrill() for x in _groups}
        #~opt = settings[grp].path_get(path, raw=True)
        #~opt.set(JS_SD_VAL_HERE)
        #~# TODO: Finish this. Load group by group, setting as we go. (Warn about
        #~# settings that weren't actually set, unless we 'allow_missing' or
        #~# similar.)
        #~# For now, we're only supporting the full-on path writing. The rest can
        #~# come later!
        #~sdict = 

# karxi: Other than one bit of odd behavior...this works. Start setting it up
# when I get back! :D
# Categories... gui, advanced, security, chums.
# ... Table for each?

# BEFORE YOU START: See if there's an option wrapper already made. If not, go
# make it; it shouldn't be hard (just point to the mainwin profile methods).

# ... On second thought, just set up some conditional imports.

# The groups we use, listed in the order to load their settings in.
# Presently subject to later modification.
# NOTE: This is presently a sort of semi-kludge to get loading and such up and
# running.
_groups = [
    "base",
    "convo", "memos", "logs",
    "perms",
    "gui", "advanced",
    "security", "tweaks"
]



# These functions are presented this way so that less-intelligent folding
# mechanisms can easily split the option groups up. It's neater that way.
def _def_sdict_base(cb_source=None):
    # The basic/original Pesterchum settings.
    sd = SettingsDict("base",
        [
            # karxi: This'll probably be set a different way later.
            Option("chumlist",              [], list, None,
                   """The profile's list of friended chumhandles."""),
            # NEEDED: 'setChums'
            # NEEDED: 'addChum'
            # NEEDED: 'removeChum'
            Option("hide_offline_chums",    False, bool, None,
                   """Hide chums that are offline from the chumlist."""),
            # TODO: This is a little weird....
            #~defaultprofile      = _gen_oldget("defaultprofile", None)
            Option("default_profile",       None, (unicode, None), None,
                   """The name of the default profile to load."""),
            Option("tabbed_pesters",        True, bool, None,
                   """Conglomerate pesters into a single tabbed window."""),
            # karxi: TODO: Not sure this'll work properly. Test it.
            # TODO: Make it inherit the former as a default?? This really
            # isn't necesary; unlike vanilla Pesterchum, we intend to make
            # sure all options are set from the get-go, and added at their
            # defaults if they're not already present for one reason or
            # another.
            # Logic like that can be handled in update scripts.
            Option("tabbed_memos",          True, bool, None,
                   """Conglomerate memos into a single tabbed window."""),
            Option("show_timestamps",       True, bool, None,
                   """Prefix pester messages with timestamps.
                   Likely to be deprecated as this functionality is split up
                   for pesters and memos."""),
            Option("timestamp_12hr",        True, bool, None,
                   """Use 12 hour timestamps instead of 24 hour ones.
                   Will become deprecated when custom timestamps are
                   added."""),
            Option("timestamp_seconds",     False, bool, None,
                   """Show seconds in timestamps.
                   Will become deprecated when custom timestamps are
                   added."""),
            # TODO: Figure out where 'sortMethod' is used.
            Option("sort_method",           0, int, None,
                   """The...method used to sort chums?..."""),
            Option("enable_groups",         False, bool, None,
                   """Allow the creation of user-defined groups to sort chums
                   more effectively."""),
            # NEEDED: 'openDefaultGroup'
            # This will require callbacks to actually (un)hide groups.
            Option("show_empty_groups",     False, bool, None,
                   """Show groups without any chums in them."""),
            # TODO: Figure out where 'showOnlineNumbers' is used.
            Option("show_online_numbers",   False, bool, None,
                   """Show online numbers? For groups or something?"""),
            Option("log_pesters",
                   (consts.LOG | consts.STAMP), int, None,
                   """Automatically log pesters."""),
            Option("log_memos",
                   (consts.LOG), int, None,
                   """Automatically log memos."""),
            # NEEDED: 'disableUserLinks'
            # The default here is 10*60*(10**3) ms, i.e., 10 minutes.
            Option("auto_idle_delay",       10*60*10**3, int, None,
                   """The time, in milliseconds, until a user automatically
                   goes idle."""),
            Option("minimize_action",       0, int, None,
                   """Action to take when the minimize button is clicked."""),
            Option("close_action",          1, int, None,
                   """Action to take when the close button is clicked."""),
            Option("show_user_modes",       "qaohv", unicode, None,
                   """The list of channel user flags to show mode change
                   messages for."""),
            # This is normally 'False', but it causes too much lag to leave on
            # by default.
            Option("show_animations",       False, bool, None,
                   """Animate Pesterchum's emoticons.
                   Note that this is known to cause serious lag."""),
            # NEEDED: 'checkForUpdates'
            # Another option that should go in 'system'.
            # Not sure what it's usually set to...a ctime-esque int??
            Option("last_update_check",     0, (int,), None,
                   """Time of the last update check that was performed."""),
            # This is no longer important now that Homestuck is over...right?
            Option("check_mspa_updates",    False, bool, None,
                   """Check MSPA for updates."""),
            Option("msg_blink_flags",
                   (consts.PBLINK | consts.MBLINK), int, None,
                   """Stores the state of blink settings.
                   Will be deprecated as those are split off...possibly."""),
            # TODO: Find out what these are for??
            #~notify              = _gen_oldget("notify", True)
            #~notifyType          = _gen_oldget("notifyType", "default")
            Option("notify_flags",
                   (consts.SIGNIN | consts.NEWMSG | consts.NEWCONVO | \
                    consts.INITIALS), int, None,
                   """Flags for when notifications should happen.
                   Deprecated later?"""),
            Option("low_bandwidth_mode",    False, bool, None,
                   """Low-bandwidth mode.
                   Less bandwidth is used; protects from some spam attacks.
                   Moods will NOT work properly when this is enabled."""),
            Option("pesterdunk_ghostchum",  False, bool, None,
                   """SPOOKY SCARY PESTERGHOSTS"""),
            # karxi: These two have overrides we need to respect.
            # For now, we can run through each option per-group and have 'base'
            # go first, then have 'advanced' carry fallbacks, or override these
            # as needed.
            Option("port",                  6667, int, None,
                   """The port Pesterchum uses to connect to the server."""),
            Option("server",                "irc.mindfang.org", unicode, None,
                   """The server Pesterchum connects to."""),

            Option("enable_sound",          True, bool, None,
                   """Enable sound across the whole app."""),
            Option("beep_on_pester_msg",    True, bool, None,
                   """Beep when receiving a message in a pester."""),
            Option("beep_on_memo_msg",      True, bool, None,
                   """Beep when there's a new message in a memo."""),
            # 'memoPing'
            Option("beep_on_memo_ping",     True, bool, None,
                   """To be determined."""),
            # 'nameSound'
            Option("beep_on_mention",       True, bool, None,
                   """To be determined."""),
            Option("sound_volume",          100, int, None,
                   """The volume of Pesterchum's sounds."""),
            # 'trayMessage'
            Option("tray_msg",              True, bool, None,
                   """To be determined.""")

            # NEEDED: 'getGroups'
            # NEEDED: 'addGroup'
            # NEEDED: 'delGroup'
            # NEEDED: 'expandGroup'
            # NEEDED: 'saveGroups'
        ])
    return sd

def _def_sdict_advanced(cb_source=None):
    sd = SettingsDict("advanced",
        [
            Option("aux_servers",           [], list, None,
                   """List of servers to connect to if the default isn't
                   available.
                   Not implemented; may not ever be."""),
            Option("compatibility_flags",   -1, int, None,
                   """The 'level' of compatibility to attempt to maintain with
                   other clients.
                   This is a series of flags, so the values listed here are
                   bits.
                        -1: Enable all compatibility options. Default.
                         0: Disable all compatibility options.
                         1: Pesterchum 3.41 compatibility.
                         2: Chumdroid compatibility.
                   Flags can be binary OR'd together to try to retain
                   compatibility with the listed clients.
                   If you don't know what that means, you probably shouldn't
                   touch this option.
                   More flags may be introduced later."""),
            # If not false, override. Need callbacks.
            Option("port_override",         0, int, None,
                   """If set, override the default port with this one."""),
            Option("server_override",       "", unicode, None,
                   """If set, override the default server with this one.""")
        ])
    return sd

def _def_sdict_convo(cb_source=None):
    sd = SettingsDict("convo",
        [
            Option("blocked_users",         [], list, None,
                   """Handles blocked from establishing contact.""")
            # NEEDED: 'addBlocklist'
            # NEEDED: 'delBlocklist'
        ])
    return sd

def _def_sdict_memos(cb_source=None):
    sd = SettingsDict("memos",
        [
            Option("rejoin_delay",          500, int, None,
            """Milliseconds to wait before attempting to rejoin a
            memo you were kicked from.""")
        ])
    return sd

def _def_sdict_gui(cb_source=None):
    # TODO?: Allow all-theme overrides?...
    sd = SettingsDict("gui",
        [
            # This will definitely require callbacks to hook/unhook the
            # shortcuts.
            Option("keyboard_shortcuts",    True, bool, None,
                   # This should eventually have a dialog somewhere -
                   # accessible by Ctrl+?, perhaps?
                   """Enable added keyboard shortcuts."""),
            # TODO: Prioritize this, it shouldn't be too hard...and a lot of
            # people will appreciate it.
            # Needs a hard-coded length limit, though.
            Option("multiline_textboxes",   False, bool, None,
                   # Might be usable with callbacks.
                   """Enable multiline textboxes. This allows the sending of
                   multiple lines per post, and also makes it easier to write
                   long posts."""),
            Option("show_emoticons",        True, bool, None,
                   """Display Pesterchum emoticons as inline images."""),
            # This'll require a hook to change things to and fro, but it
            # shouldn't be hard to call something like an "idler_scan" method
            # for all of them.
            Option("show_idlers",           True, bool, None,
                   """Highlight people idling in memos.""")
        ])
    return sd

def _def_sdict_logs(cb_source=None):
    # Note to self: Allow per-Option attrs to enhance flexibility?... Or even
    # make .storage an AttrDict that can be filled on creation.
    sd = SettingsDict("logs",
        [
            # Log handling in Pesterchum really just needs to be revamped. The
            # log writers seem to stack after a while, which is bad...might be
            # an issue in the IRC handling; unsure.

            # Once this is set, it should move all of those logs into a folder
            # for it. If it's unset, it should move them back into the main
            # namespace - simple, right?
            Option("segregate_unnamed",     False, bool, None,
                   """Log pesterClient### clients in their own homogenous
                   folder group, given their propensity for creating messy
                   logs."""),
            # If I do this, I will NEED to set up thread locks. Maybe the Queue
            # class would come in handy here?
            # It'd probably be best that the flush method handled the queue via
            # an iterator, and thus could keep going until the list of new
            # posts has cleared.
            Option("thread_logging",        False, bool, None,
                   """Delegate actually writing logs to a separate thread.
                   Helps keep Pesterchum from locking up due to slow disk write
                   speeds."""),
            # Having it save logs, as base, in Pesterchum format and raw would
            # be best...with the option to load a log and export it.
            Option("write_bbcode",          False, bool, None,
                   """Automatically write logs as BBcode.
                   More than one of these modifiers can be enabled."""),
            Option("write_html",            True, bool, None,
                   """Automatically write logs as HTML.
                   More than one of these modifiers can be enabled.""")
        ])
    return sd

def _def_sdict_permissions(cb_source=None):
    sd = SettingsDict("perms",
        [
            Option("others_can_invite",     True, bool, None,
                   """Allows people who aren't on the chumlist to send you
                   invites."""),
            # Tempted to put this under security...or just make this security.
            # For now, I will.
            Option("others_can_mood",       True, bool, None,
                   """Allows people who aren't on the chumlist to request MOOD
                   replies from you.
                   NOTE: This can be exploited for attacks. Work to fix this is
                   upcoming; this option exists as a quick fix for the issue.
                   NOTE: Canon handles are not considered to be 'safe' for MOOD
                   responses with this option active. Their requests are
                   ignored.""")
        ])
    return sd

def _def_sdict_security(cb_source=None):
    sd = SettingsDict("security",
        [
            Option("chum_flood_exempt",     True, bool, None,
                   """Whether chums can trip flood restrictions."""),
            # These timeout options may be a little bit too granular, so I'll
            # provide generalized options (with callbacks to set things to
            # uniform defaults) as well.
            # ...I might need to consider the order of initialization,
            # though....
            # If these are set to 0, they shouldn't proc.
            Option("max_univ_responses",    0, int, None,
                   """Sets the max_*_response options to the same value."""),
            Option("univ_flood_timeout",    0, int, None,
                   """Sets the *_flood_timeout options to the same value."""),
            Option("univ_flood_cd",         0, int, None,
                   """Sets the *_flood_cd options to the same value."""),

            # === GETMOOD flood protection ===
            Option("max_mood_responses",    5, int, None,
                   """The number of mood responses we can give, in a specified
                   timeframe, before we go on cooldown and stop providing them
                   for a time.
                   Helps resist flood attacks."""),
            Option("mood_flood_timeout",    10*(10**3), int, None,
                   """Time (in ms) until our mood flood detection resets.
                   There can't be any mood requests during this period, or else
                   the duration is reset to full."""),
            Option("mood_flood_cd",         10*(10**3), int, None,
                   """Time (in ms) until we begin sending mood responses after
                   flood detection has been tripped."""),

            # === TIME flood protection ===
            Option("max_time_responses",    5, int, None,
                   """The number of time responses we can give, in a specified
                   timeframe, before we go on cooldown and stop providing them
                   for a time.
                   Helps resist flood attacks."""),
            Option("time_flood_timeout",    10*(10**3), int, None,
                   """Time (in ms) until our time flood detection resets.
                   There can't be any time requests during this period, or else
                   the duration is reset to full."""),
            Option("time_flood_cd",         10*(10**3), int, None,
                   """Time until we begin sending time responses after flood
                   flood detection has been tripped."""),

            # This will probably have to track based off of host...bluh.
            Option("max_query_responses",   3, int, None,
                   """The number of pesters we'll open, in a specified
                   timeframe, before we go on cooldown and stop responding to
                   them for a time.
                   Helps resist flood attacks."""),
            # We should probably have a special flag for these.
            Option("block_on_query_flood",  False, bool, None,
                   """Block users, by host, when they trip flood
                   detection.""")
        ])
    return sd

def _def_sdict_system(cb_source=None):
    sd = SettingsDict("system",
        [
            # ... Things like version information should go here, so we
            # maintain a record, but don't have to hard-code things.
        ])
    return sd

def _def_sdict_tweaks(cb_source=None):
    sd = SettingsDict("tweaks",
        [
            Option("auto_unidle",           True, bool, None,
                   """Automatically unset idle upon returning from being
                   automatically set idle.
                   Changing this makes it less obvious when you've come and
                   gone.""")
        ])
    return sd


settings = SettingsDict("trollian")

def _init_settings(cb_source=None):
    """Initialize the settings storage object provided by this module.
    cb_source should be an AttrDict, or a class (thus assuming staticmethods)
    which provides all the callback functions that the options defined here
    will need.
    This allows more flexible definitions and organization at the cost of
    slightly stricter formatting."""
    global settings

    to_add = [
            _def_sdict_base(cb_source),
            _def_sdict_advanced(cb_source),
            _def_sdict_convo(cb_source),
            _def_sdict_memos(cb_source),
            _def_sdict_logs(cb_source),
            _def_sdict_gui(cb_source),
            _def_sdict_permissions(cb_source),
            _def_sdict_security(cb_source),
            _def_sdict_system(cb_source),
            _def_sdict_tweaks(cb_source)
        ]
    for sd in to_add:
        settings.add(sd)

    # Aaaaand we're done. Simple enough.
    return

# Note that this *must* set MAINWIN
def _init_module_references(refdict):
    self = sys.modules[__name__]
    for key, val in refdict.items():
        setattr(self, key, val)



