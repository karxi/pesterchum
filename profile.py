import logging
import os, os.path as osp
from string import Template
import json
import re
import codecs, copy
import platform
from datetime import *
from time import strftime, time
from PyQt4 import QtGui, QtCore

import ostools
from mood import Mood
from dataobjs import PesterProfile, pesterQuirk, pesterQuirks
from parsetools import convertTags, addTimeInitial, themeChecker, ThemeException

_datadir = ostools.getDataDir()

class PesterLog(object):
    def __init__(self, handle, parent=None):
        global _datadir
        self.parent = parent
        self.handle = handle
        self.convos = {}
        self.logpath = _datadir+"logs"

    def log(self, handle, msg):
        if self.parent.config.time12Format():
            time = strftime("[%I:%M")
        else:
            time = strftime("[%H:%M")
        if self.parent.config.showSeconds():
            time += strftime(":%S] ")
        else:
            time += "] "
        if handle[0] == '#':
            if not self.parent.config.logMemos() & self.parent.config.LOG: return
            if not self.parent.config.logMemos() & self.parent.config.STAMP:
                time = ""
        else:
            if not self.parent.config.logPesters() & self.parent.config.LOG: return
            if not self.parent.config.logPesters() & self.parent.config.STAMP:
                time = ""
        if self.parent.isBot(handle): return
        #watch out for illegal characters
        handle = re.sub(r'[<>:"/\\|?*]', "_", handle)
        bbcodemsg = time + convertTags(msg, "bbcode")
        html = time + convertTags(msg, "html")+"<br />"
        msg = time +convertTags(msg, "text")
        modes = {"bbcode": bbcodemsg, "html": html, "text": msg}
        if not self.convos.has_key(handle):
            time = datetime.now().strftime("%Y-%m-%d.%H.%M")
            self.convos[handle] = {}
            for (format, t) in modes.iteritems():
                if not osp.exists("%s/%s/%s/%s" % (self.logpath, self.handle, handle, format)):
                    os.makedirs("%s/%s/%s/%s" % (self.logpath, self.handle, handle, format))
                try:
                    fp = codecs.open("%s/%s/%s/%s/%s.%s.txt" % (self.logpath, self.handle, handle, format, handle, time), encoding='utf-8', mode='a')
                except IOError:
                    errmsg = QtGui.QMessageBox(self)
                    errmsg.setText("Warning: Pesterchum could not open the log file for %s!" % (handle))
                    errmsg.setInformativeText("Your log for %s will not be saved because something went wrong. We suggest restarting Pesterchum. Sorry :(" % (handle))
                    errmsg.show()
                    continue
                self.convos[handle][format] = fp
        for (format, t) in modes.iteritems():
            f = self.convos[handle][format]
            if platform.system() == "Windows":
                f.write(t+"\r\n")
            else:
                f.write(t+"\r\n")
            f.flush()
    def finish(self, handle):
        if not self.convos.has_key(handle):
            return
        for f in self.convos[handle].values():
            f.close()
        del self.convos[handle]
    def close(self):
        for h in self.convos.keys():
            for f in self.convos[h].values():
                f.close()

class userConfig(object):
    # karxi: All of these are set to indicate which bit they stand for.
    # Using << shifts the bit over by the second number's places, so x << 0
    # will return x.

    # Use for bit flag log setting
    LOG     = 1 << 0    # 1
    STAMP   = 1 << 1    # 2
    # Use for bit flag blink
    PBLINK  = 1 << 0    # 1
    MBLINK  = 1 << 1    # 2
    # Use for bit flag notfications
    SIGNIN  = 1 << 0    # 1
    SIGNOUT = 1 << 1    # 2
    NEWMSG  = 1 << 2    # 4
    NEWCONVO= 1 << 3    # 8
    INITIALS= 1 << 4    # 16
    def __init__(self, parent):
        self.parent = parent
        self.filename = osp.join(_datadir, "pesterchum.js")
        with open(self.filename) as fp:
            # This is all in unicode...hm.
            self.config = json.load(fp)
        if "defaultprofile" in self.config:
            self.userprofile = userProfile(self.config["defaultprofile"])
        else:
            self.userprofile = None

        self.logpath = osp.join(_datadir, "logs")

        if not osp.exists(self.logpath):
            os.makedirs(self.logpath)

        # Make sure to create a user theme dir so that they know they can put
        # things there.
        # This works for normal Pesterchum, too, so it's probably good to have.
        uthemepath = osp.join(_datadir, "themes")
        if not osp.exists(uthemepath):
            os.makedirs(uthemepath)

        #~# NOTE: None of this is used yet. Later, this will change.
        #~# TODO: Make this into a reusable function for themes and the like.
        #~# Probably 'establish_file' or something.
        #~grouppaths = (
        #~    osp.join(_datadir, "groups.js"),
        #~    osp.join(self.logpath, "groups.js")
        #~    )
        #~self.group_paths = []
        #~lpath = grouppaths[-1]
        #~for lp in grouppaths:
        #~    if osp.exists(lp):
        #~        self.group_paths.append(lp)
        #~try:
        #~    lpath = self.group_paths[0]
        #~except IndexError:
        #~    # No matches. Use Pesterchum's default.
        #~    lpath = grouppaths[-1]
        #~    self.group_paths.append(lpath)
        lpath = osp.join(self.logpath, "groups.js")

        # Breaks naming convention to fit Pesterchum's convention...ugh.
        self.grouppath = lpath

        # TODO: Reenable this...in a subclass, then remove this code.
        #~for lp in self.group_paths:
        for lp in (self.grouppath,):
            try:
                with open(lp, 'r') as fp:
                    self.groups = json.load(fp)
            except IOError:
                # Try the next.
                continue
            except ValueError as err:
                errmsg = ' '.join("Failed to parse {0!r}",
                                  "({1.__class__.__name__}):",
                                  "{1.message}")
                logging.error(errmsg.format(lp, err))
                continue
            else:
                # We successfully got our groups.
                break
        else:
            # We're out of paths.
            logging.warning("Couldn't find groups.js; making a new one.")
            self.groups = {}
            with open(self.grouppath, 'w') as fp:
                json.dump(self.groups, fp)

    def chums(self):
        return self.setdefault("chums", [])
    def setChums(self, newchums, overwrite=False):
        # If 'overwrite', we're ACTUALLY setting the whole list.
        with open(self.filename, 'r') as fp:
            # TODO: Account for the possibility that we won't be able to grab
            # this to open it.
            oldconfig = json.load(fp)
        oldchums = oldconfig.get("chums", [])
        # Naturally eliminate certain duplicates
        newchums = set(newchums)
        if not overwrite:
            # Merge the two chumrolls.
            newchumroll = set(oldchums) | newchums
        else:
            # *Set* the chumroll to the new one.
            newchumroll = newchums
        newchumroll = list(newchumroll)
        # Keep it sorted - why not?
        newchumroll.sort()

        self.set("chums", newchumroll)
    def addChum(self, chum):
        try:
            # Handle PesterProfile args
            handle = chum.handle
        except AttributeError:
            handle = chum
        if handle not in self.chums():
            self.setChums([handle], overwrite=False)
    def removeChum(self, chum):
        try:
            # Handle PesterProfile args
            handle = chum.handle
        except AttributeError:
            handle = chum
        chums = self.chums()
        oldchums = list(chums)
        modified = False
        while True:
            try:
                chums.remove(handle)
            except ValueError:
                # We've removed every occurrence.
                break
            else: modified = True
        if modified:
            # A change was made. Save.
            self.set("chums", chums)

    def hideOfflineChums(self):
        return self.config.get("hideOfflineChums", False)
    def defaultprofile(self):
        return self.get("defaultprofile", None)
    def tabs(self):
        return self.get("tabs", True)
    def tabMemos(self):
        return self.setdefault("tabmemos", self.tabs())
    def showTimeStamps(self):
        return self.setdefault("showTimeStamps", True)
    def time12Format(self):
        return self.setdefault("time12Format", True)
    def showSeconds(self):
        return self.setdefault("showSeconds", False)
    def sortMethod(self):
        return self.get('sortMethod', 0)
    def useGroups(self):
        return self.get('useGroups', False)

    def openDefaultGroup(self):
        groups = self.getGroups()
        for g in groups:
            if g[0] == "Chums":
                return g[1]
        return True

    def showEmptyGroups(self):
        return self.setdefault("emptyGroups", False)
    def showOnlineNumbers(self):
        return self.setdefault("onlineNumbers", False)
    def logPesters(self):
        return self.get('logPesters', self.LOG | self.STAMP)
    def logMemos(self):
        return self.get('logMemos', self.LOG)
    def disableUserLinks(self):
        return not self.get('userLinks', True)
    def idleTime(self):
        return self.get('idleTime', 10)
    def minimizeAction(self):
        return self.get('miniAction', 0)
    def closeAction(self):
        return self.get('closeAction', 1)
    def opvoiceMessages(self):
        return self.get('opvMessages', True)
    def animations(self):
        return self.get('animations', True)
    def checkForUpdates(self):
        # karxi: There's no way this is the best way to do this.
        u = self.get('checkUpdates', 0)
        if isinstance(u, bool):
            if u: u = 2
            else: u = 3
        return u
        # Once a day
        # Once a week
        # Only on start
        # Never
    def lastUCheck(self):
        return self.get('lastUCheck', 0)
    def checkMSPA(self):
        return self.get('mspa', False)
    def blink(self):
        return self.get('blink', self.PBLINK | self.MBLINK)
    def notify(self):
        return self.get('notify', True)
    def notifyType(self):
        return self.get('notifyType', "default")
    def notifyOptions(self):
        default = self.SIGNIN | self.NEWMSG | self.NEWCONVO | self.INITIALS
        return self.get('notifyOptions', default)
    def lowBandwidth(self):
        return self.get('lowBandwidth', False)
    def ghostchum(self):
        return self.get('ghostchum', False)

    def getBlocklist(self):
        return self.setdefault("block", [])
    def addBlocklist(self, handle):
        l = self.getBlocklist()
        if handle not in l:
            l.append(handle)
            self.set('block', l)
    def delBlocklist(self, handle):
        blockl = self.getBlocklist()
        oldblocks = list(blockl)
        modified = False
        while True:
            try:
                blockl.remove(handle)
            except ValueError:
                # We've removed every occurrence.
                break
            else:
                modified = True
        if modified:
            # A change was made. Save.
            self.set("block", blockl)

    def getGroups(self):
        if not self.groups.has_key('groups'):
            self.saveGroups([["Chums", True]])
        return self.groups.get('groups', [["Chums", True]])
    def addGroup(self, group, open=True):
        l = self.getGroups()
        exists = False
        for g in l:
            if g[0] == group:
                exists = True
                break
        if not exists:
            l.append([group,open])
            l.sort()
            self.saveGroups(l)
    def delGroup(self, group):
        l = self.getGroups()
        i = 0
        for g in l:
            if g[0] == group: break
            i = i+1
        l.pop(i)
        l.sort()
        self.saveGroups(l)
    def expandGroup(self, group, open=True):
        l = self.getGroups()
        for g in l:
            if g[0] == group:
                g[1] = open
                break
        self.saveGroups(l)
    def saveGroups(self, groups):
        self.groups['groups'] = groups
        try:
            jsonoutput = json.dumps(self.groups)
        except ValueError as e:
            raise e
        with open(osp.join(self.logpath, "groups.js"), 'w') as fp:
            fp.write(jsonoutput)

    def server(self):
        try:
            return self.parent.serverOverride
        except AttributeError:
            #~return self.get("server", "irc.mindfang.org")
            # TODO: Change this, it's ugly. Apparently Pesterchum doesn't obey
            # the usual means of overriding, though.
            return self.get("server", "irc.sorcery.net")
    def port(self):
        try:
            return self.parent.portOverride
        except AttributeError:
            return self.get("port", "6667")
    def soundOn(self):
        return self.setdefault("soundon", True)
    def chatSound(self):
        return self.get('chatSound', True)
    def memoSound(self):
        return self.get('memoSound', True)
    def memoPing(self):
        return self.get('pingSound', True)
    def nameSound(self):
        return self.get('nameSound', True)
    def volume(self):
        return self.get('volume', 100)
    def trayMessage(self):
        return self.get('traymsg', True)
    def get(self, item, default=None):
        return self.config.get(item, default)
    def set(self, item, setting):
        self.config[item] = setting
        self.writeout()
    def setdefault(self, item, default):
        retval = self.config.setdefault(item, default)
        self.writeout()
        return retval
    def writeout(self):
        try:
            jso = json.dumps(self.config)
        except ValueError as err:
            raise err
        with open(self.filename, 'w') as fp:
            fp.write(jso)
    def availableThemes(self):
        themes = []
        uthemepath = osp.join(_datadir, "themes")
        dthemepath = "themes"
        # Load user themes.
        for dirname, dirnames, filenames in os.walk(uthemepath):
            for d in dirnames:
                themes.append(d)
        # Also load embedded themes.
        if _datadir:
            for dirname, dirnames, filenames in os.walk(dthemepath):
                for d in dirnames:
                    if d not in themes:
                        themes.append(d)
        themes.sort()
        return themes
    def availableProfiles(self):
        profs = []
        profileloc = osp.join(_datadir, "profiles")
        for dirname, dirnames, filenames in os.walk(profileloc):
            for filename in filenames:
                fn, ext = osp.splitext(filename)
                if ext == ".js":
                    profs.append(fn)
        profs.sort()
        return [userProfile(p) for p in profs]
    # Just here to help Vim realize where to end the fold.
    pass




# These are all ugly and messy, but will be steadily phased out with time.
def _sdict_dig(sdict, key, raw=True):
    path = key.split('.')
    if raw:
        # Inject 'raw' access.
        path.insert(1, "raw")
    # Iterate down to the target.
    targ = reduce(getattr, path, sdict)
    # Do as we will.
    return targ#~, optname
# '_sdict_dig' is called in each generated function instead of once upon
# creation, just in case their targets get swapped out....
# TODO: Make it error instead of returning None for a failed find.
def _gen_oldget(key, default=None):
    if callable(default):
        # If we have a callable object, we should use it to generate a
        # value.
        def get_wrapper(self, key=key, default=default):
            obj = self
            key = self._new_opt_paths.get(key, key)
            default = default()
            if '.' in key:
                obj = _sdict_dig(self.sd_config, key)
                # Query the Option object directly
                return obj.get(default)
            return obj.get(key, default)
    else:
        # We don't bother checking if this is mutable or not; it's safer just
        # to copy() it anyway. Options shouldn't be touched except through
        # their indicated interface....
        def get_wrapper(self, key=key, default=default):
            obj = self
            key = self._new_opt_paths.get(key, key)
            default = copy.copy(default)
            if '.' in key:
                obj = _sdict_dig(self.sd_config, key)
                return obj.get(default)
            return obj.get(key, default)
    get_wrapper.key, get_wrapper.default = key, default
    return get_wrapper
def _gen_oldsget(key, default=None):
    if callable(default):
        def sget_wrapper(self, key=key, default=default):
            # Options don't work this way! They come with defaults built in.
            obj = self
            key = self._new_opt_paths.get(key, key)
            if '.' in key:
                obj = _sdict_dig(self.sd_config, key)
                # Defaults are already accounted for
                val = obj.get()
            else:
                val = self.setdefault(key, default())
                #~self.flush()
            return val
    else:
        def sget_wrapper(self, key=key, default=default):
            obj = self
            key = self._new_opt_paths.get(key, key)
            if '.' in key:
                obj = _sdict_dig(self.sd_config, key)
                val = obj.get()
            else:
                val = self.setdefault(key, copy.copy(default))
                #~self.flush()
            return val
    sget_wrapper.key, sget_wrapper.default = key, default
    return sget_wrapper
def _gen_oldset(key):
    def set_wrapper(self, val, key=key):
        key = self._new_opt_paths.get(key, key)
        if '.' in key:
            obj = _sdict_dig(self.sd_config, key)
            obj.set(val)
            self.flush()
        else:
            self.set(key, val)
            #~self.flush()
    set_wrapper.key = key
    return set_wrapper

class configWrapper(userConfig):
    import types

    # Copied from userConfig - purely to keep them in the namespace, so we can
    # use them.

    # karxi: All of these are set to indicate which bit they stand for.
    # Using << shifts the bit over by the second number's places, so x << 0
    # will return x.

    # Use for bit flag log setting
    LOG     = 1 << 0    # 1
    STAMP   = 1 << 1    # 2
    # Use for bit flag blink
    PBLINK  = 1 << 0    # 1
    MBLINK  = 1 << 1    # 2
    # Use for bit flag notfications
    SIGNIN  = 1 << 0    # 1
    SIGNOUT = 1 << 1    # 2
    NEWMSG  = 1 << 2    # 4
    NEWCONVO= 1 << 3    # 8
    INITIALS= 1 << 4    # 16

    parent = None
    sd_config = None

    # Note: Need to 'reduce()' those of these with periods in them.
    # Period-separated names indicate a SettingsDict path. They're handled by
    # the earlier-defined generator functions.
    _new_opt_paths = dict(
        #~chums               = "base.chumlist",
        hideOfflineChums    = "base.hide_offline_chums",
        # This does some voodoo we don't want to deal with.
        defaultprofile      = "base.default_profile",
        tabs                = "base.tabbed_pesters",
        tabmemos            = "base.tabbed_memos",
        showTimeStamps      = "base.show_timestamps",
        time12Format        = "base.timestamp_12hr",
        showSeconds         = "base.timestamp_seconds",
        sortMethod          = "base.sort_method",
        useGroups           = "base.enable_groups",
        emptyGroups         = "base.show_empty_groups",
        onlineNumbers       = "base.show_online_numbers",
        logPesters          = "base.log_pesters",
        logMemos            = "base.log_memos",
        #~userLinks           = "",
        idleTime            = "base.auto_idle_delay",
        minimizeAction      = "base.minimize_action",
        closeAction         = "base.close_action",
        # Format changed for this one
        #~opvMessages         = "base.show_user_modes",
        animations          = "base.show_animations",
        #~checkUpdates        = "",
        #~lastUCheck          = "",
        checkMSPA           = "base.check_mspa_updates",
        blink               = "base.msg_blink_flags",
        #~notify              = "base.notify",
        #~notifyType          = "base.notify_type",
        notifyOptions       = "base.notify_flags",
        lowBandwidth        = "base.low_bandwidth_mode",
        ghostchum           = "base.pesterdunk_ghostchum",
        #~block               = "convo.blocked_users",
        server              = "base.server",
        port                = "base.port",
        soundon             = "base.enable_sound",
        # Not 100% sure these are appropriate names, needs checking
        chatSound           = "base.beep_on_pester_msg",
        memoSound           = "base.beep_on_memo_msg",
        pingSound           = "base.beep_on_memo_ping",
        nameSound           = "base.beep_on_mention",
        volume              = "base.sound_volume",
        trayMessage         = "base.tray_msg"
    )

    def __init__(self, parent, sdict):
        # Let the old class set things up, for now.
        super(configWrapper, self).__init__(parent)

        # Overwrite a few things as we please.
        self.parent = parent
        # This hasn't been set up to work with a SettingsDict yet.
        # Realistically, it'll probably just be easier to redirect the wrapper
        # to access whatever global options directory we have set up.

        # We rely on our 'config' already being set by userConfig.
        # This has to contain all the other SettingsDicts.
        self.sd_config = sdict

        # Run through _new_opt_paths and set the old config variables to the
        # sdict underlying this. (This is just a wrapper, but we can't ignore
        # Pesterchum's default settings, and there's no other loader yet.)
        for oldkey, newkey in self._new_opt_paths.items():
            # Fetch the actual Option we'll reflect this value onto.
            opt = self.sd_config.path_get(newkey, raw=True)
            # Fetch the old function name.
            val = getattr(self, oldkey)
            # Call the old function, like Pesterchum would/will.
            val = val()
            # Set the loaded value to the sdict option accordingly.
            opt.set(val)

        # ???
        return

    def flush(self):
        # Inherits from userConfig, for now
        self.writeout()

    # Use generators to standardize the access of old values.
    # Later, we can update these to point to new places; eventually, after
    # enough refactoring, this wrapper won't be necessary at all.
    chums               = _gen_oldsget("chums", [])
    # NEEDED: 'setChums'
    # NEEDED: 'addChum'
    # NEEDED: 'removeChum'
    hideOfflineChums    = _gen_oldget("hideOfflineChums", False)
    defaultprofile      = _gen_oldget("defaultprofile", None)
    tabs                = _gen_oldget("tabs", True)
    # karxi: TODO: Not sure this'll work properly. Test it.
    tabmemos            = _gen_oldsget("tabmemos", tabs)
    showTimeStamps      = _gen_oldsget("showTimeStamps", True)
    time12Format        = _gen_oldsget("time12Format", True)
    showSeconds         = _gen_oldsget("showSeconds", False)
    sortMethod          = _gen_oldget("sortMethod", 0)
    useGroups           = _gen_oldget("useGroups", False)
    # NEEDED: 'openDefaultGroup'
    showEmptyGroups     = _gen_oldsget("emptyGroups", False)
    showOnlineNumbers   = _gen_oldsget("onlineNumbers", False)
    logPesters          = _gen_oldget("logPesters", LOG | STAMP)
    logMemos            = _gen_oldget("logMemos", LOG)
    # NEEDED: 'disableUserLinks'
    idleTime            = _gen_oldget("idleTime", 10)
    minimizeAction      = _gen_oldget("miniAction", 0)
    closeAction         = _gen_oldget("closeAction", 1)
    opvoiceMessages     = _gen_oldget("opvMessages", True)
    animations          = _gen_oldget("animations", True)
    # NEEDED: 'checkForUpdates'
    lastUCheck          = _gen_oldget("lastUCheck", 0)
    checkMSPA           = _gen_oldget("mspa", False)
    blink               = _gen_oldget("blink", PBLINK | MBLINK)
    notify              = _gen_oldget("notify", True)
    notifyType          = _gen_oldget("notifyType", "default")
    notifyOptions       = _gen_oldget("notifyOptions",
                                      SIGNIN | NEWMSG | NEWCONVO | INITIALS)
    lowBandwidth        = _gen_oldget("lowBandwidth", False)
    ghostchum           = _gen_oldget("ghostchum", False)
    # NEEDED: 'addChum'
    # NEEDED: 'removeChum'
    getBlocklist        = _gen_oldsget("block", [])
    # NEEDED: 'addBlocklist'
    # NEEDED: 'delBlocklist'
    # karxi: These two have overrides we need to respect.
    # NEEDED: 'server'
    # NEEDED: 'port'
    soundOn             = _gen_oldsget("soundon", True)
    chatSound           = _gen_oldget("chatSound", True)
    memoSound           = _gen_oldget("memoSound", True)
    memoPing            = _gen_oldget("pingSound", True)
    nameSound           = _gen_oldget("nameSound", True)
    volume              = _gen_oldget("volume", 100)
    trayMessage         = _gen_oldget("traymsg", True)

    # NEEDED: 'getGroups'
    # NEEDED: 'addGroup'
    # NEEDED: 'delGroup'
    # NEEDED: 'expandGroup'
    # NEEDED: 'saveGroups'

    # TODO: Map 'set' so that it obeys the proper redirects...and modify
    # 'config' for similar results.



# karxi: What the fuck is this??? This whole class and everything that *uses* it
# needs to be rewritten! It's terrible!
class userProfile(object):
    def __init__(self, user):
        self.profiledir = osp.join(_datadir, "profiles")

        if isinstance(user, PesterProfile):
            self.chat = user
            # THIS IS TERRIBLE PRACTICE.
            # This code effectively sets up defaults, saves them, then
            # haphazardly modifies them while setting up attributes based off
            # of them, often using copy/pasted code.
            # *WHY*??
            self.userprofile = {"handle":user.handle,
                                "color": unicode(user.color.name()),
                                "quirks": [],
                                "theme": "pesterchum"}
            # Convenience.
            uprof = self.userprofile
            self.theme = pesterTheme("pesterchum")
            self.chat.mood = Mood(self.theme["main/defaultmood"])
            self.lastmood = self.chat.mood.value()
            self.quirks = pesterQuirks([])
            self.randoms = False
            initials = self.chat.initials()
            # karxi: The fact that this check exists is terrifying.
            # Our initials should *always* be 2 characters!
            if len(initials) >= 2:
                initials = (initials, "%s%s" % (initials[0].lower(), initials[1]), "%s%s" % (initials[0], initials[1].lower()))
                self.mentions = [r"\b(%s)\b" % ("|".join(initials))]
            else:
                self.mentions = []
            self.autojoins = []
        else:
            with open(osp.join(self.profiledir, user + ".js")) as fp:
                self.userprofile = uprof = json.load(fp)
            try:
                self.theme = pesterTheme(uprof["theme"])
            except ValueError:
                self.theme = pesterTheme("pesterchum")
            self.lastmood = uprof.get('lastmood', self.theme["main/defaultmood"])
            self.chat = PesterProfile(uprof["handle"],
                                      QtGui.QColor(uprof["color"]),
                                      Mood(self.lastmood))
            self.quirks = pesterQuirks(uprof["quirks"])
            self.randoms = uprof.setdefault("randoms", False)
            if "mentions" not in uprof:
                initials = self.chat.initials()
                if len(initials) >= 2:
                    initials = (initials, "%s%s" % (initials[0].lower(), initials[1]), "%s%s" % (initials[0], initials[1].lower()))
                    uprof["mentions"] = [r"\b(%s)\b" % ("|".join(initials))]
                else:
                    uprof["mentions"] = []
            self.mentions = uprof["mentions"]
            self.autojoins = uprof.setdefault("autojoins", [])

        try:
            with open(osp.join(_datadir, "passwd.js")) as fp:
                self.passwd = json.load(fp)
        except (IOError, ValueError):
            self.passwd = {}
        self.autoidentify = False
        self.nickservpass = ""
        chathl = self.chat.handle
        if chathl in self.passwd:
            self.autoidentify = self.passwd[chathl]["auto"]
            self.nickservpass = self.passwd[chathl]["pw"]

    def setMood(self, mood):
        self.chat.mood = mood
    def setTheme(self, theme):
        self.theme = theme
        self.userprofile["theme"] = theme.name
        self.save()
    def setColor(self, color):
        self.chat.color = color
        self.userprofile["color"] = unicode(color.name())
        self.save()
    def setQuirks(self, quirks):
        self.quirks = quirks
        self.userprofile["quirks"] = self.quirks.plainList()
        self.save()
    def getRandom(self):
        return self.randoms
    def setRandom(self, random):
        self.randoms = random
        self.userprofile["randoms"] = random
        self.save()
    def getMentions(self):
        return self.mentions
    def setMentions(self, mentions):
        try:
            for (i,m) in enumerate(mentions):
                re.compile(m)
        except re.error, e:
            logging.error("#%s Not a valid regular expression: %s" % (i, e))
        else:
            self.mentions = mentions
            self.userprofile["mentions"] = mentions
            self.save()
    def getLastMood(self):
        return self.lastmood
    def setLastMood(self, mood):
        self.lastmood = mood.value()
        self.userprofile["lastmood"] = self.lastmood
        self.save()
    def getTheme(self):
        return self.theme
    def getAutoIdentify(self):
        return self.autoidentify
    def setAutoIdentify(self, b):
        self.autoidentify = b
        if self.chat.handle not in self.passwd:
            self.passwd[self.chat.handle] = {}
        self.passwd[self.chat.handle]["auto"] = b
        self.saveNickServPass()
    def getNickServPass(self):
        return self.nickservpass
    def setNickServPass(self, pw):
        self.nickservpass = pw
        if self.chat.handle not in self.passwd:
            self.passwd[self.chat.handle] = {}
        self.passwd[self.chat.handle]["pw"] = pw
        self.saveNickServPass()
    def getAutoJoins(self):
        return self.autojoins
    def setAutoJoins(self, autojoins):
        self.autojoins = autojoins
        self.userprofile["autojoins"] = self.autojoins
        self.save()
    def save(self):
        handle = self.chat.handle
        if handle[0:12] == "pesterClient":
            # dont save temp profiles
            return
        try:
            jsonoutput = json.dumps(self.userprofile)
        except ValueError as e:
            raise e
        with open("%s/%s.js" % (self.profiledir, handle), 'w') as fp:
            fp.write(jsonoutput)
    def saveNickServPass(self):
        # remove profiles with no passwords
        for h,t in self.passwd.items():
            if "auto" not in t and ("pw" not in t or t["pw"] == ""):
                del self.passwd[h]
        try:
            jsonoutput = json.dumps(self.passwd, indent=4)
        except ValueError as e:
            raise e
        with open(osp.join(_datadir, "passwd.js"), 'w') as fp:
            fp.write(jsonoutput)
    @staticmethod
    def newUserProfile(chatprofile):
        if osp.exists(osp.join(_datadir, "profiles",
                               chatprofile.handle + ".js")):
            newprofile = userProfile(chatprofile.handle)
        else:
            newprofile = userProfile(chatprofile)
            newprofile.save()
        return newprofile

class PesterProfileDB(dict):
    def __init__(self):
        self.logpath = osp.join(_datadir, "logs")

        if not osp.exists(self.logpath):
            os.makedirs(self.logpath)
        try:
            with open(osp.join(self.logpath, "chums.js"), 'r') as fp:
                chumdict = json.load(fp)
        except (IOError, ValueError):
            # karxi: This code feels awfully familiar....
            chumdict = {}
            with open(osp.join(self.logpath, "chums.js"), 'w') as fp:
                json.dump(chumdict, fp)

        u = []
        for (handle, c) in chumdict.iteritems():
            options = dict()
            if 'group' in c:
                options['group'] = c['group']
            if 'notes' in c:
                options['notes'] = c['notes']
            if 'color' not in c:
                c['color'] = "#000000"
            if 'mood' not in c:
                c['mood'] = "offline"
            u.append((handle, PesterProfile(handle, color=QtGui.QColor(c['color']), mood=Mood(c['mood']), **options)))
        converted = dict(u)
        self.update(converted)

    def save(self):
        try:
            with open("%s/chums.js" % (self.logpath), 'w') as fp:
                chumdict = dict([p.plaindict() for p in self.itervalues()])
                json.dump(chumdict, fp)
        except Exception as e:
            raise e
    def getColor(self, handle, default=None):
        if not self.has_key(handle):
            return default
        else:
            return self[handle].color
    def setColor(self, handle, color):
        if self.has_key(handle):
            self[handle].color = color
        else:
            self[handle] = PesterProfile(handle, color)
    def getGroup(self, handle, default="Chums"):
        if not self.has_key(handle):
            return default
        else:
            return self[handle].group
    def setGroup(self, handle, theGroup):
        if self.has_key(handle):
            self[handle].group = theGroup
        else:
            self[handle] = PesterProfile(handle, group=theGroup)
        self.save()
    def getNotes(self, handle, default=""):
        if not self.has_key(handle):
            return default
        else:
            return self[handle].notes
    def setNotes(self, handle, notes):
        if self.has_key(handle):
            self[handle].notes = notes
        else:
            self[handle] = PesterProfile(handle, notes=notes)
        self.save()
    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)
        self.save()

class pesterTheme(dict):
    def __init__(self, name, default=False):
        possiblepaths = (
            osp.join(_datadir, "themes", name),
            osp.join("themes", name),
            osp.join(_datadir, "themes", "pesterchum"),
            osp.join("themes", "pesterchum")
        )
        self.path = possiblepaths[-1]
        for p in possiblepaths:
            if osp.exists(p):
                self.path = p
                break

        self.name = name
        try:
            with open(osp.join(self.path, "style.js")) as fp:
                theme = json.load(fp, object_hook=self.pathHook)
        except IOError:
            theme = json.loads("{}")
        self.update(theme)
        if self.has_key("inherits"):
            self.inheritedTheme = pesterTheme(self["inherits"])
        if not default:
            self.defaultTheme = pesterTheme("pesterchum", default=True)
    def __getitem__(self, key):
        keys = key.split("/")
        try:
            v = super(pesterTheme, self).__getitem__(keys.pop(0))
        except KeyError as e:
                if hasattr(self, 'inheritedTheme'):
                    return self.inheritedTheme[key]
                elif hasattr(self, 'defaultTheme'):
                    return self.defaultTheme[key]
                else:
                    raise e
        for k in keys:
            try:
                v = v[k]
            except KeyError as e:
                if hasattr(self, 'inheritedTheme'):
                    return self.inheritedTheme[key]
                elif hasattr(self, 'defaultTheme'):
                    return self.defaultTheme[key]
                else:
                    raise e
        return v
    def pathHook(self, d):
        for (k, v) in d.iteritems():
            if isinstance(v, unicode):
                s = Template(v)
                d[k] = s.safe_substitute(path=self.path)
        return d
    def get(self, key, default=None):
        # Might want some errorchecking if 'None' is supplied.
        logging.warning("pesterTheme.get called without a default")
        keys = key.split("/")
        try:
            v = super(pesterTheme, self).__getitem__(keys.pop(0))
            for k in keys:
                v = v[k]
            return default if v is None else v
        except KeyError:
            if hasattr(self, 'inheritedTheme'):
                return self.inheritedTheme.get(key, default)
            else:
                return default

    def has_key(self, key):
        keys = key.split("/")
        try:
            v = super(pesterTheme, self).__getitem__(keys.pop(0))
            for k in keys:
                v = v[k]
            return (v is not None)
        except KeyError:
            if hasattr(self, 'inheritedTheme'):
                return self.inheritedTheme.has_key(key)
            else:
                return False
