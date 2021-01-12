# -*- coding=UTF-8; tab-width: 4 -*-
from __future__ import division

# A module to hold data on how Pesterchum's themes are supposed to be
# structured.


class ThemeStruct(object):
    """A helper for the Theme class that defines all of the keys that are needed
    for a given theme to work."""
    # This class exists entirely so it can serve as a data container.
    # The keys might have types associated with them later, so we use dicts to
    # provide structure.

    needs = {
        'convo': {'chumlabel': {'align': {'h': None, 'v': None},
                                 'maxheight': None,
                                 'minheight': None,
                                 'style': None,
                                 'text': None},
                   'input': {'style': None},
                   'margins': None,
                   'size': None,
                   'style': None,
                   'systemMsgColor': None,
                   'tabs': {'selectedstyle': None, 'style': None, 'tabstyle': None},
                   'tabwindow': {'style': None},
                   'text': {'beganpester': None,
                            'blocked': None,
                            'blockedmsg': None,
                            'ceasepester': None,
                            'closememo': None,
                            'idle': None,
                            'joinmemo': None,
                            'kickedmemo': None,
                            'openmemo': None,
                            'unblocked': None},
                   'textarea': {'style': None}},
         'main': {'addchum': {'loc': None, 'size': None, 'style': None, 'text': None},
                  'background-image': None,
                  'block': {'loc': None, 'size': None, 'text': None},
                  'chums': {'loc': None,
                            'moods': {'blocked': {'icon': None},
                                      'chummy': {'icon': None}},
                            'size': None,
                            'style': None,
                            'userlistcolor': None},
                  'close': {'image': None, 'loc': None},
                  'defaultmood': None,
                  'defaultwindow': {'style': None},
                  'icon': None,
                  'menu': {'loc': None,
                           'menuitem': None,
                           'selected': None,
                           'style': None},
                  'menubar': {'style': None},
                  'menus': {'client': {'_name': None,
                                       'addgroup': None,
                                       'exit': None,
                                       'idle': None,
                                       'import': None,
                                       'logviewer': None,
                                       'memos': None,
                                       'options': None,
                                       'randen': None,
                                       'reconnect': None,
                                       'userlist': None},
                            'help': {'_name': None,
                                     'about': None,
                                     'calsprite': None,
                                     'chanserv': None,
                                     'help': None,
                                     'nickserv': None},
                            'profile': {'_name': None,
                                        'block': None,
                                        'color': None,
                                        'quirks': None,
                                        'switch': None},
                            'rclickchumlist': {'addchum': None,
                                               'banuser': None,
                                               'blockchum': None,
                                               'invitechum': None,
                                               'memohidden': None,
                                               'memoinvite': None,
                                               'memomute': None,
                                               'memonoquirk': None,
                                               'memosetting': None,
                                               'movechum': None,
                                               'notes': None,
                                               'opuser': None,
                                               'pester': None,
                                               'quirksoff': None,
                                               'removechum': None,
                                               'removegroup': None,
                                               'renamegroup': None,
                                               'unblockchum': None,
                                               'viewlog': None,
                                               'voiceuser': None}},
                  'minimize': {'image': None, 'loc': None},
                  'moodlabel': {'loc': None, 'style': None, 'text': None},
                  'moods': None,
                  'mychumhandle': {'colorswatch': {'loc': None, 'size': None},
                                   'handle': {'loc': None,
                                              'size': None,
                                              'style': None},
                                   'label': {'loc': None,
                                             'style': None,
                                             'text': None}},
                  'pester': {'loc': None, 'size': None, 'text': None},
                  'size': None,
                  'style': None,
                  'trollslum': {'label': {'style': None, 'text': None},
                                'size': None,
                                'style': None},
                  'windowtitle': None},
         'memos': {'input': {'style': None},
                   'label': {'align': {'h': None, 'v': None},
                             'maxheight': None,
                             'minheight': None,
                             'style': None,
                             'text': None},
                   'margins': None,
                   'memoicon': None,
                   'op': {'icon': None},
                   'size': None,
                   'style': None,
                   'systemMsgColor': None,
                   'textarea': {'style': None},
                   'time': {'arrows': {'left': None, 'right': None, 'style': None},
                            'buttons': {'style': None},
                            'text': {'style': None, 'width': None}},
                   'userlist': {'style': None, 'width': None},
                   'voice': {'icon': None}}
          }

    # The ridiculously long list of required theme keys from parsetools.py.
    # This is what was used to construct that set of dicts.
    raw_needs = [
        "main/size", "main/icon", "main/windowtitle", "main/style", \
        "main/background-image", "main/menubar/style", "main/menu/menuitem", \
        "main/menu/style", "main/menu/selected", "main/close/image", \
        "main/close/loc", "main/minimize/image", "main/minimize/loc", \
        "main/menu/loc", "main/menus/client/logviewer", \
        "main/menus/client/addgroup", "main/menus/client/options", \
        "main/menus/client/exit", "main/menus/client/userlist", \
        "main/menus/client/memos", "main/menus/client/import", \
        "main/menus/client/idle", "main/menus/client/reconnect", \
        "main/menus/client/_name", "main/menus/profile/quirks", \
        "main/menus/profile/block", "main/menus/profile/color", \
        "main/menus/profile/switch", "main/menus/profile/_name", \
        "main/menus/help/about", "main/menus/help/_name", "main/moodlabel/text", \
        "main/moodlabel/loc", "main/moodlabel/style", "main/moods", \
        "main/addchum/style", "main/addchum/text", "main/addchum/size", \
        "main/addchum/loc", "main/pester/text", "main/pester/size", \
        "main/pester/loc", "main/block/text", "main/block/size", "main/block/loc", \
        "main/mychumhandle/label/text", "main/mychumhandle/label/loc", \
        "main/mychumhandle/label/style", "main/mychumhandle/handle/loc", \
        "main/mychumhandle/handle/size", "main/mychumhandle/handle/style", \
        "main/mychumhandle/colorswatch/size", "main/mychumhandle/colorswatch/loc", \
        "main/defaultmood", "main/chums/size", "main/chums/loc", \
        "main/chums/style", "main/menus/rclickchumlist/pester", \
        "main/menus/rclickchumlist/removechum", \
        "main/menus/rclickchumlist/blockchum", "main/menus/rclickchumlist/viewlog", \
        "main/menus/rclickchumlist/removegroup", \
        "main/menus/rclickchumlist/renamegroup", \
        "main/menus/rclickchumlist/movechum", "convo/size", \
        "convo/tabwindow/style", "convo/tabs/tabstyle", "convo/tabs/style", \
        "convo/tabs/selectedstyle", "convo/style", "convo/margins", \
        "convo/chumlabel/text", "convo/chumlabel/style", "convo/chumlabel/align/h", \
        "convo/chumlabel/align/v", "convo/chumlabel/maxheight", \
        "convo/chumlabel/minheight", "main/menus/rclickchumlist/quirksoff", \
        "main/menus/rclickchumlist/addchum", "main/menus/rclickchumlist/blockchum", \
        "main/menus/rclickchumlist/unblockchum", \
        "main/menus/rclickchumlist/viewlog", "main/trollslum/size", \
        "main/trollslum/style", "main/trollslum/label/text", \
        "main/trollslum/label/style", "main/menus/profile/block", \
        "main/chums/moods/blocked/icon", "convo/systemMsgColor", \
        "convo/textarea/style", "convo/text/beganpester", "convo/text/ceasepester", \
        "convo/text/blocked", "convo/text/unblocked", "convo/text/blockedmsg", \
        "convo/text/idle", "convo/input/style", "memos/memoicon", \
        "memos/textarea/style", "memos/systemMsgColor", "convo/text/joinmemo", \
        "memos/input/style", "main/menus/rclickchumlist/banuser", \
        "main/menus/rclickchumlist/opuser", "main/menus/rclickchumlist/voiceuser", \
        "memos/margins", "convo/text/openmemo", "memos/size", "memos/style", \
        "memos/label/text", "memos/label/style", "memos/label/align/h", \
        "memos/label/align/v", "memos/label/maxheight", "memos/label/minheight", \
        "memos/userlist/style", "memos/userlist/width", "memos/time/text/width", \
        "memos/time/text/style", "memos/time/arrows/left", \
        "memos/time/arrows/style", "memos/time/buttons/style", \
        "memos/time/arrows/right", "memos/op/icon", "memos/voice/icon", \
        "convo/text/closememo", "convo/text/kickedmemo", \
        "main/chums/userlistcolor", "main/defaultwindow/style", \
        "main/chums/moods", "main/chums/moods/chummy/icon", "main/menus/help/help", \
        "main/menus/help/calsprite", "main/menus/help/nickserv", "main/menus/help/chanserv", \
        "main/menus/rclickchumlist/invitechum", "main/menus/client/randen", \
        "main/menus/rclickchumlist/memosetting", "main/menus/rclickchumlist/memonoquirk", \
        "main/menus/rclickchumlist/memohidden", "main/menus/rclickchumlist/memoinvite", \
        "main/menus/rclickchumlist/memomute", "main/menus/rclickchumlist/notes"
        ]

    @classmethod
    # Used to generate our .needs
    def _process_needs(cls, generator=dict):
        result = generator()

        for need in cls.needs:
            keys = need.split("/")
            # We have a place to start, now begin iterating down.
            # The number of iterations we've had.
            i = 0
            # Prepare for the first jump.
            delve = result
            while keys:
                # We're only cataloguing, so we don't need to worry about
                # inheritance.
                # Figure out where we're going.
                hole = keys.pop(0)
                # Dig a hole and hop in.
                delve = delve.setdefault(hole, generator)
                # Increment.
                i += 1
            # Fall through to the next need.

        return result



# vim: set autoindent ts=4 sts=4 sw=4 textwidth=79 expandtab:
