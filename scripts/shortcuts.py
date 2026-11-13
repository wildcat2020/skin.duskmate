# -*- coding: utf-8 -*-
"""
Duskmate shortcuts: custom home menu items and remote buttons, set up by the viewer.

Run with RunScript(special://skin/scripts/shortcuts.py) from Duskmate's skin settings.
What the viewer sets up is kept in special://profile/addon_data/skin.duskmate/shortcuts.json.
Menu items are handed to the skin through Skin strings (duskmate.menu.N.*), and buttons are
written to special://profile/keymaps/duskmate_shortcuts.xml, which Kodi reads with its keymaps.
"""
import json
import os
import time
from xml.sax.saxutils import escape

import xbmc
import xbmcgui
import xbmcvfs

MAX_ITEMS = 8
DATA_DIR = xbmcvfs.translatePath("special://profile/addon_data/skin.duskmate/")
DATA_FILE = os.path.join(DATA_DIR, "shortcuts.json")
KEYMAP_FILE = xbmcvfs.translatePath("special://profile/keymaps/duskmate_shortcuts.xml")
DEFAULT_ICON = "icons/sidemenu/addons.png"
DUSKMATE = "com.expansionkit.tv"
dialog = xbmcgui.Dialog()

KODI_SECTIONS = [
    ("Movies", "ActivateWindow(Videos,videodb://movies/titles/,return)"),
    ("TV shows", "ActivateWindow(Videos,videodb://tvshows/titles/,return)"),
    ("Music", "ActivateWindow(Music,root,return)"),
    ("Videos (files)", "ActivateWindow(Videos,root,return)"),
    ("Pictures", "ActivateWindow(Pictures)"),
    ("Add-ons", "ActivateWindow(1100)"),
    ("Favourites", "ActivateWindow(favouritesbrowser)"),
    ("Weather", "ActivateWindow(Weather)"),
    ("Settings", "ActivateWindow(Settings)"),
    ("File manager", "ActivateWindow(FileManager)"),
    ("System information", "ActivateWindow(SystemInfo)"),
    ("Event log", "ActivateWindow(EventLog)"),
    ("Power menu", "ActivateWindow(ShutdownMenu)"),
    ("Update video library", "UpdateLibrary(video)"),
    ("Reload skin", "ReloadSkin()"),
]

DUSKMATE_SCREENS = [
    ("Duskmate", "StartAndroidActivity(%s)" % DUSKMATE),
    ("Duskmate: Tonight for you", "StartAndroidActivity(%s,android.intent.action.VIEW,,expansionkit://tonight/)" % DUSKMATE),
    ("Duskmate: Settings", "StartAndroidActivity(%s,android.intent.action.VIEW,,expansionkit://settings)" % DUSKMATE),
]


# ---------------------------------------------------------------- storage

def load():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    data.setdefault("items", [])
    data.setdefault("buttons", [])
    return data


def save(data):
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    apply(data)


def quoted(value):
    return '"%s"' % value.replace("\\", "\\\\").replace('"', '\\"')


def apply(data):
    """Hands the menu items to the skin and writes the keymap, then reloads the keymaps."""
    for n in range(1, MAX_ITEMS + 1):
        item = data["items"][n - 1] if n <= len(data["items"]) else None
        if item:
            xbmc.executebuiltin("Skin.SetString(duskmate.menu.%d.label,%s)" % (n, quoted(item["label"])))
            xbmc.executebuiltin("Skin.SetString(duskmate.menu.%d.action,%s)" % (n, quoted(item["action"])))
            xbmc.executebuiltin("Skin.SetString(duskmate.menu.%d.icon,%s)" % (n, quoted(item.get("icon") or DEFAULT_ICON)))
        else:
            for key in ("label", "action", "icon"):
                xbmc.executebuiltin("Skin.Reset(duskmate.menu.%d.%s)" % (n, key))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             "<!-- Written by Duskmate shortcuts. Change it from Duskmate's skin settings, not by hand. -->",
             "<keymap>", "  <global>", "    <keyboard>"]
    for b in data["buttons"]:
        lines.append('      <key id="%d">%s</key>' % (int(b["code"]), escape(b["action"])))
    lines += ["    </keyboard>", "  </global>", "</keymap>", ""]
    folder = os.path.dirname(KEYMAP_FILE)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    with open(KEYMAP_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    xbmc.executebuiltin("Action(reloadkeymaps)")


# ---------------------------------------------------------------- choosing an action

def rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    try:
        return json.loads(xbmc.executeJSONRPC(json.dumps(request))).get("result") or {}
    except Exception:
        return {}


def pick(title, options):
    """options: list of (label, value). Returns the value or None."""
    if not options:
        dialog.notification("Duskmate", "Nothing to choose from here.", xbmcgui.NOTIFICATION_INFO, 3000)
        return None
    i = dialog.select(title, [o[0] for o in options])
    return None if i < 0 else options[i][1]


def android_apps():
    result = rpc("Files.GetDirectory", {"directory": "androidapp://sources/apps/", "media": "files"})
    apps = []
    for f in result.get("files") or []:
        package = os.path.basename(f.get("file", "").rstrip("/"))
        if package:
            apps.append((f.get("label") or package, "StartAndroidActivity(%s)" % package))
    return sorted(apps, key=lambda a: a[0].lower())


def addons(kind):
    result = rpc("Addons.GetAddons", {"type": kind, "enabled": True, "properties": ["name"]})
    out = []
    for a in result.get("addons") or []:
        out.append((a.get("name") or a["addonid"], a["addonid"]))
    return sorted(out, key=lambda a: a[0].lower())


def favourites():
    result = rpc("Favourites.GetFavourites", {"properties": ["window", "windowparameter", "path"]})
    out = []
    for f in result.get("favourites") or []:
        kind, title = f.get("type"), f.get("title", "")
        if kind == "media" and f.get("path"):
            out.append((title, "PlayMedia(%s)" % quoted(f["path"])))
        elif kind == "window" and f.get("window"):
            param = f.get("windowparameter") or ""
            out.append((title, "ActivateWindow(%s%s,return)" % (f["window"], ("," + quoted(param)) if param else "")))
        elif kind == "script" and f.get("path"):
            out.append((title, "RunScript(%s)" % quoted(f["path"])))
        elif kind == "androidapp" and f.get("path"):
            out.append((title, "StartAndroidActivity(%s)" % os.path.basename(f["path"].rstrip("/"))))
    return out


def choose_action():
    """Returns (suggested label, action) or None."""
    kinds = [
        ("An Android app", "app"),
        ("A Duskmate screen", "duskmate"),
        ("A Kodi add-on", "addon"),
        ("A script (RunScript)", "script"),
        ("A Kodi favourite", "favourite"),
        ("A Kodi section", "section"),
        ("Type a Kodi command", "command"),
    ]
    kind = pick("What should it open?", kinds)
    if kind is None:
        return None
    if kind == "app":
        apps = android_apps()
        choice = pick("Android app", apps)
        return (next(l for l, v in apps if v == choice), choice) if choice else None
    if kind == "duskmate":
        choice = pick("Duskmate screen", DUSKMATE_SCREENS)
        return (next(l for l, v in DUSKMATE_SCREENS if v == choice), choice) if choice else None
    if kind == "section":
        choice = pick("Kodi section", KODI_SECTIONS)
        return (next(l for l, v in KODI_SECTIONS if v == choice), choice) if choice else None
    if kind == "favourite":
        favs = favourites()
        choice = pick("Kodi favourite", favs)
        return (next(l for l, v in favs if v == choice), choice) if choice else None
    if kind == "addon":
        found = addons("xbmc.addon.executable") + addons("xbmc.python.pluginsource")
        found = sorted(set(found), key=lambda a: a[0].lower())
        choice = pick("Add-on", found)
        return (next(l for l, v in found if v == choice), "RunAddon(%s)" % choice) if choice else None
    if kind == "script":
        scripts = addons("xbmc.python.script")
        options = scripts + [("Type the script id or path…", "__typed__")]
        choice = pick("Script", options)
        if choice is None:
            return None
        label = next((l for l, v in scripts if v == choice), "")
        if choice == "__typed__":
            choice = dialog.input("Script id or path (for example script.foo or special://home/x.py)").strip()
            if not choice:
                return None
            label = os.path.basename(choice)
        args = dialog.input("Arguments, separated by commas (leave empty for none)").strip()
        return (label or choice, "RunScript(%s%s)" % (choice, ("," + args) if args else ""))
    command = dialog.input("Kodi command, for example RunScript(script.foo,arg) or ActivateWindow(Videos)").strip()
    return (command.split("(")[0], command) if command else None


# ---------------------------------------------------------------- capturing a button

class Capture(xbmcgui.WindowDialog):
    """Shows a prompt and records the code of the next button pressed."""
    def __init__(self):
        super().__init__()
        self.code = None
        w, h = self.getWidth(), self.getHeight()
        self.addControl(xbmcgui.ControlImage(0, 0, w, h, "", colorDiffuse="DD0B0D14"))
        self.addControl(xbmcgui.ControlLabel(0, h // 2 - 60, w, 50, "Press the button to use", font="font30_title", alignment=2))
        self.addControl(xbmcgui.ControlLabel(0, h // 2, w, 40, "It closes by itself after 10 seconds.", font="font14", alignment=2))

    def onAction(self, action):
        code = action.getButtonCode()
        if code:
            self.code = code
            self.close()


def capture_button():
    win = Capture()
    win.show()
    started = time.time()
    monitor = xbmc.Monitor()
    while win.code is None and time.time() - started < 10 and not monitor.abortRequested():
        xbmc.sleep(100)
    code = win.code
    win.close()
    del win
    return code


def assign_button(data, label, action):
    code = capture_button()
    if code is None:
        dialog.notification("Duskmate", "No button was pressed.", xbmcgui.NOTIFICATION_INFO, 3000)
        return
    taken = next((b for b in data["buttons"] if int(b["code"]) == int(code)), None)
    if taken and not dialog.yesno("Duskmate", "That button already opens \"%s\". Use it for \"%s\" instead?" % (taken["label"], label)):
        return
    data["buttons"] = [b for b in data["buttons"] if int(b["code"]) != int(code)]
    data["buttons"].append({"code": int(code), "label": label, "action": action})
    save(data)
    dialog.notification("Duskmate", "Button set for %s." % label, xbmcgui.NOTIFICATION_INFO, 3000)


# ---------------------------------------------------------------- screens

def edit_item(data, index):
    while True:
        item = data["items"][index]
        has_button = any(b["action"] == item["action"] for b in data["buttons"])
        options = [
            ("Name: %s" % item["label"], "name"),
            ("Opens: %s" % item["action"], "action"),
            ("Change the remote button" if has_button else "Give it a remote button", "button"),
        ]
        if has_button:
            options.append(("Remove its remote button", "unbutton"))
        if index > 0:
            options.append(("Move up", "up"))
        if index < len(data["items"]) - 1:
            options.append(("Move down", "down"))
        options.append(("Remove from the home menu", "remove"))
        choice = pick(item["label"], options)
        if choice is None:
            return
        if choice == "name":
            name = dialog.input("Name in the home menu", item["label"]).strip()
            if name:
                item["label"] = name
                save(data)
        elif choice == "action":
            chosen = choose_action()
            if chosen:
                for b in data["buttons"]:
                    if b["action"] == item["action"]:
                        b["action"] = chosen[1]
                item["action"] = chosen[1]
                save(data)
        elif choice == "button":
            data["buttons"] = [b for b in data["buttons"] if b["action"] != item["action"]]
            assign_button(data, item["label"], item["action"])
        elif choice == "unbutton":
            data["buttons"] = [b for b in data["buttons"] if b["action"] != item["action"]]
            save(data)
        elif choice in ("up", "down"):
            other = index - 1 if choice == "up" else index + 1
            data["items"][index], data["items"][other] = data["items"][other], data["items"][index]
            index = other
            save(data)
        elif choice == "remove":
            if dialog.yesno("Duskmate", "Remove \"%s\" from the home menu?" % item["label"]):
                data["buttons"] = [b for b in data["buttons"] if b["action"] != item["action"]]
                del data["items"][index]
                save(data)
                return


def menu_items(data):
    while True:
        options = [(i["label"], n) for n, i in enumerate(data["items"])]
        if len(data["items"]) < MAX_ITEMS:
            options.append(("Add an item…", "add"))
        choice = pick("Home menu items", options)
        if choice is None:
            return
        if choice == "add":
            chosen = choose_action()
            if not chosen:
                continue
            name = dialog.input("Name in the home menu", chosen[0]).strip() or chosen[0]
            data["items"].append({"label": name, "action": chosen[1], "icon": DEFAULT_ICON})
            save(data)
            if dialog.yesno("Duskmate", "Give \"%s\" a remote button as well?" % name):
                assign_button(data, name, chosen[1])
        else:
            edit_item(data, choice)


def buttons(data):
    while True:
        options = [("%s  (button %d)" % (b["label"], int(b["code"])), n) for n, b in enumerate(data["buttons"])]
        options.append(("Assign a button…", "add"))
        choice = pick("Remote buttons", options)
        if choice is None:
            return
        if choice == "add":
            chosen = choose_action()
            if chosen:
                assign_button(data, chosen[0], chosen[1])
        else:
            b = data["buttons"][choice]
            sub = pick(b["label"], [("Opens: %s" % b["action"], "action"), ("Use another button", "rebind"), ("Remove this button", "remove")])
            if sub == "action":
                chosen = choose_action()
                if chosen:
                    b["label"], b["action"] = chosen
                    save(data)
            elif sub == "rebind":
                label, action = b["label"], b["action"]
                del data["buttons"][choice]
                assign_button(data, label, action)
            elif sub == "remove":
                del data["buttons"][choice]
                save(data)


def main():
    data = load()
    while True:
        choice = pick("Duskmate shortcuts", [
            ("Home menu items (%d)" % len(data["items"]), "items"),
            ("Remote buttons (%d)" % len(data["buttons"]), "buttons"),
        ])
        if choice is None:
            return
        if choice == "items":
            menu_items(data)
        else:
            buttons(data)


if __name__ == "__main__":
    main()
