import sublime, sublime_plugin
import json
import os
from os.path import join
import subprocess

active_menu = False

class OpenFilesCommand(sublime_plugin.TextCommand):
    active = False
    index_highlighted = 0
    command_list = ["Open in Explorer", "Placeholder"]
    action_folder = ["Open Folder in Explorer", "Copy Path to Clipboard", 
                     "Copy Folder Name to Clipboard", "New File"]
    action_file = ["Copy File Path to Clipboard", "Copy File Name to Clipboard", 
                   "Open with Application"]
    window = None
    entries_path = None
    entries_display = None
    length_folders = 0
    path_current = None
    path_parent = None
    # current directory, with index_highlighted, get highted directory

    @classmethod
    def reset(cls):
        cls.active = False
        # cls.index_highlighted = 0

    @classmethod
    def on_highlighted(cls, index):
        cls.index_highlighted = index

    def __init__(self, view):
        sublime_plugin.TextCommand.__init__(self, view)
        self.settings = sublime.load_settings("OpenFiles.sublime-settings")

    def run(self, edit, path = None, key = None, ignore = True):
        type(self).active = True
        # do not use self.view.window(), otherwise None for backward action
        type(self).window = sublime.active_window()
        if not key:
            self.open(path, ignore)
        elif key == "right":
            self.choose_menu()
        elif key == "left":
            self.backward()
        elif key == "tab":
            self.show_hidden_files()
        else:
            pass
    
    def choose_menu(self):
        type(self).window.run_command("hide_overlay")
        type(self).active = True
        global active_menu
        active_menu = True
        if type(self).index_highlighted > type(self).length_folders + 1:
            # action list for file
            action_list = [[action, type(self).entries_path[type(self).index_highlighted]]
                for action in type(self).action_file]

            on_done = self.act_file
        elif type(self).index_highlighted >= 0:
            # action list for sub-directory and parent directory
            action_list = [[action, type(self).entries_path[type(self).index_highlighted]]
                for action in type(self).action_folder]

            on_done = self.act_folder
        else:
            # can not happen
            pass
        type(self).window.show_quick_panel(action_list, on_done)

    def act_folder(self, index):
        full_path = type(self).entries_path[type(self).index_highlighted]
        if index == 0:
            subprocess.call(["explorer", full_path])
        elif index == 1:
            sublime.set_clipboard(full_path)
        elif index == 2:
            sublime.set_clipboard(os.path.basename(full_path))
        elif index == 3:
            self.create_file(full_path)
        else:
            type(self).reset()

    def create_file(self, path):
        type(self).active = False

        def on_done(text):
            text = text.replace("/", "\\")
            text = os.path.join(path, text)
            if text.endswith("\\"):
                os.makedirs(text, exist_ok = True)
            else:
                new_path = os.path.dirname(text)
                os.makedirs(new_path, exist_ok = True)
                if not os.path.exists(text):
                    open(text, "w").close()
                    sublime.active_window().open_file(text)
                else:
                    if os.path.isdir(text):
                        sublime.error_message(
                            'Folder: "{}" has already existed!'.format(text))
                    else:
                        res_dialog = sublime.yes_no_cancel_dialog(
                            'File: "{}" has already existed!'.format(text),
                            "Overwrite It!", "Open It")
                        if res_dialog == sublime.DIALOG_YES:
                            open(text, "w").close()
                            sublime.active_window().open_file(text)
                        elif res_dialog == sublime.DIALOG_NO:
                            sublime.active_window().open_file(text)
                        else:
                            pass

        def on_change(text):
            text = text.replace("/", "\\")
            text = os.path.join(path, text)
            sublime.active_window().status_message(text)

        sublime.active_window().show_input_panel("New", "", on_done, on_change, None)

    def act_file(self, index):
        full_path = type(self).entries_path[type(self).index_highlighted]
        if index == 0:
            sublime.set_clipboard(full_path)
        elif index == 1:
            sublime.set_clipboard(os.path.basename(full_path))
        elif index == 2:
            if full_path.endswith(".pdf"):
                pdf_reader = self.settings.get("pdf_reader", "")
                if pdf_reader:
                    subprocess.call([pdf_reader, full_path])
                else:
                    sublime.message_dialog("Please the path of pdf reader.")
            elif full_path.endswith((".csv", ".CSV", ".xslx", ".xsl")):
                excel = self.settings.get("excel", "")
                if excel:
                    subprocess.call([excel, full_path])
                else:
                    sublime.message_dialog("Please the path of Excel.")
            else:
                sublime.message_dialog("No Application to Open this Type of File.") 
        else:
            type(self).reset()

    def open(self, path = None, ignore = True):
        global active_menu
        active_menu = False
        self.set_files_folders(path, ignore)
        def on_done(index):
            # open files
            if index > type(self).length_folders + 1:
                type(self).window.open_file(type(self).entries_path[index])
            # open subdirectory
            elif index > 0:
                # self.view.run_command("open_files", {"path": type(self).entries_path[index]})
                # Can not use self.view, otherwise can not navigate into folder
                # after backward action, because it's a quick panel view?
                sublime.active_window().active_view().run_command(
                    "open_files", {"path": type(self).entries_path[index]})
            # open parent directory
            elif index == 0:
                sublime.active_window().active_view().run_command(
                    "open_files", {"path": type(self).path_parent})
            else:
                # reset?
                pass
                
        type(self).window.show_quick_panel(type(self).entries_display, on_done, sublime.MONOSPACE_FONT,
            0, type(self).on_highlighted)


    def set_files_folders(self, path = None, ignore = True):
        if not path:
            path = os.path.dirname(self.view.file_name())
        try:
            entries = os.listdir(path)
        except FileNotFoundError as fnfe:
            sublime.error_message(str(fnfe))
        type(self).path_current = path
        type(self).path_parent = os.path.dirname(path)
        files = [file for file in entries if os.path.isfile(join(path, file))]
        folders = list(set(entries) - set(files))
        type(self).length_folders = len(folders)
        # can not place it in the global environment, because it run only once?
        if ignore:
            ignored_extensions = tuple(self.settings.get("ignored_extensions", ()))
            # must after folders = list(set(entries) - set(files))
            files = [file for file in files if not file.lower().endswith(ignored_extensions)]
        
        folders_files = folders + files
        type(self).entries_display = ['..', '.'] + [folder + '/' for folder in folders] + files
        type(self).entries_path = [type(self).path_parent] + [type(self).path_current] \
            + [join(path, folder_file) for folder_file in folders_files]

    def backward(self):
        type(self).active = True
        # hide quick panel
        type(self).window.run_command("hide_overlay")
        if active_menu:
            self.view.run_command("open_files", {"path": type(self).path_current})
        else:
            self.view.run_command("open_files", {"path": type(self).path_parent})

    def show_hidden_files(self):
        type(self).window.run_command("hide_overlay")
        if not active_menu:
            self.view.run_command(
                "open_files",
                {"path": type(self).path_current, "ignore": False})

class OpenListCommand(sublime_plugin.TextCommand):
    active = False
    index_highlighted = None
    window = None

    @classmethod
    def reset(cls):
        cls.active = False

    def run(self, edit, key = None, list_type = None):
        type(self).active = list_type
        # type(self).active = True
        type(self).window = sublime.active_window()
        self.set_list(list_type)
        if not key:
            self.open()
        elif key == "left":
            self.backward(list_type)
        elif key == "right":
            self.choose_menu(list_type)

    def set_list(self, list_type = None):
        settings = sublime.load_settings("OpenFiles.sublime-settings")
        max_recent_items = settings.get("max_recent_items", 15)
        if list_type == "bookmarks":
            bookmarks = settings.get("bookmarks", [])
            if bookmarks:
                pkg_path = sublime.packages_path()
                paths_list = [path if os.path.isabs(path) 
                    else join(pkg_path, path) for path in bookmarks]
                # windows
                # self.paths_list = [path.replace("/", "\\") for path in paths_list]
                self.paths_list = paths_list
                self.names_list = [os.path.basename(path) for path in paths_list]
            else:
                # throw an error?
                self.names_list = None
                self.paths_list = None
        elif list_type == "recent_files":
            session = self.get_session()
            # get()
            paths_list = session["settings"]["new_window_settings"]["file_history"]
            if paths_list:
                # change the string to path
                paths_list = [path[1] + ":" + path[2:] for path in paths_list]
                paths_list = [path for path in paths_list if os.path.exists(path)]
                paths_list = paths_list[0: min(max_recent_items, len(paths_list))]
                self.names_list = [[os.path.basename(path), os.path.dirname(path)] 
                    for path in paths_list]
                # windows
                self.paths_list = paths_list
            else:
                self.paths_list = None 
                self.names_list = None
        elif list_type == "recent_folders":
            session = self.get_session()
            paths_list = session["folder_history"]

            if paths_list:
                paths_list = [path[1] + ":" + path[2:] for path in paths_list]
                paths_list = [path for path in paths_list if os.path.exists(path)]
                paths_list = paths_list[0: min(max_recent_items, len(paths_list))]
                self.paths_list = paths_list
                self.names_list = [[os.path.basename(path), path] 
                    for path in paths_list]
            else:
                self.paths_list = None 
                self.names_list = None
        else:
            pass
    
    def get_session(self):
        path = os.path.dirname(sublime.packages_path())
        session_file = os.path.join(path, "Local", "Session.sublime_session")
        with open(session_file, encoding = "utf8") as file:
            session = json.load(file)
        return session

    def open(self):
        def on_highlighted(index):
            type(self).index_highlighted = index

        def on_done(index):
            if index >= 0:
                # do not use self.view, otherwise do not work after left key?
                full_path = self.paths_list[index]
                if os.path.isfile(full_path):
                    sublime.active_window().open_file(full_path)
                else:
                    sublime.active_window().active_view().run_command(
                        "open_files", {"path": full_path})
            else:
                type(self).reset()
        # do not use self.view.window()
        type(self).window.show_quick_panel(
            self.names_list, on_done, sublime.MONOSPACE_FONT, 0, on_highlighted)

    def choose_menu(self, list_type = None):
        type(self).window.run_command("hide_overlay")
        # must after type(self).window.run_command("hide_overlay")?
        # otherwise active become false. why?
        type(self).active = list_type
        actions_folder = ["Open Folder in Explorer", "Copy Path to Clipboard", 
                         "Copy Folder Name to Clipboard"]
        actions_file = ["Open Containing Folder", "Copy File Path to Clipboard", 
                       "Copy File Name to Clipboard", "Open with Application"]
        full_path = self.paths_list[type(self).index_highlighted]
        if os.path.isfile(full_path):
            actions_list = [[action, full_path] for action in actions_file]
            on_done = self.act_file
        else:
            actions_list = [[action, full_path] for action in actions_folder]
            on_done = self.act_folder

        type(self).window.show_quick_panel(actions_list, on_done)

    def act_file(self, index):
        full_path = self.paths_list[type(self).index_highlighted]
        path_current = os.path.dirname(full_path)
        if index == 0:
            # windows
            path_current = path_current.replace("/", "\\")
            subprocess.call(["explorer", path_current])
        elif index == 1:
            sublime.set_clipboard(full_path)
        elif index == 2:
            sublime.set_clipboard(os.path.basename(full_path))
        elif index == 3:
            if full_path.endswith(".pdf"):
                pdf_reader = self.settings.get("pdf_reader", "")
                if pdf_reader:
                    full_path = full_path.replace("/", "\\")
                    subprocess.call([pdf_reader, full_path])
                else:
                    sublime.message_dialog("Please the path of pdf reader.")
            elif full_path.endswith((".csv", ".CSV", ".xslx", ".xsl")):
                excel = self.settings.get("excel", "")
                if excel:
                    full_path = full_path.replace("/", "\\")
                    subprocess.call([excel, full_path])
                else:
                    sublime.message_dialog("Please the path of Excel.")
            else:
                # furthor 
                pass
        else:
            # further file action
            pass

    def act_folder(self, index):
        full_path = self.paths_list[type(self).index_highlighted]
        if index == 0:
            # windows
            full_path = full_path.replace("/", "\\")
            subprocess.call(["explorer", full_path])
        elif index == 1:
            sublime.set_clipboard(full_path)
        elif index == 2:
            sublime.set_clipboard(os.path.basename(full_path))
        else:
            # further path action
            pass

    def backward(self, list_type):
        type(self).window.run_command("hide_overlay")
        self.view.run_command("open_list", {"list_type": list_type})

class OpenFilesListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        group, index = view.window().get_view_index(view)
        if group == -1 and index == -1 and OpenFilesCommand.active:
            sublime.quickPanelView = view
        else:
            OpenFilesCommand.reset()
            sublime.quickPanelView = None
        # capture three kinds of views
        if group == -1 and index == -1 and OpenListCommand.active == "bookmarks":
            sublime.quickPanelBookmarksView = view
        else:
            sublime.quickPanelBookmarksView = None
        if group == -1 and index == -1 and OpenListCommand.active == "recent_files":
            sublime.quickPanelRecentFilesView = view
        else:
            sublime.quickPanelRecentFilesView = None
        if group == -1 and index == -1 and OpenListCommand.active == "recent_folders":
            sublime.quickPanelRecentFoldersView = view
        else:
            sublime.quickPanelRecentFoldersView = None
        if OpenListCommand.active not in ("bookmarks", "recent_files", "recent_folders"):
            OpenListCommand.reset()

    def on_query_context(self, view, key, operator, operand, match_all):
        if view == sublime.quickPanelView:
            if key == "open_files_backward":
                return True
            if not active_menu:
                if key == "open_files_choose_menu":
                    return True
            if key == "open_files_show_hidden_files" and not active_menu:
                return True
        # Is the repeatition necessary
        if view == sublime.quickPanelBookmarksView:
            if key == "open_bookmarks_choose_menu":
                return True
            if key == "open_bookmarks_backward":
                return True
        if view == sublime.quickPanelRecentFilesView:
            if key == "open_recent_files_choose_menu":
                return True
            if key == "open_recent_files_backward":
                return True
        if view == sublime.quickPanelRecentFoldersView:
            if key == "open_recent_folders_choose_menu":
                return True
            if key == "open_recent_folders_backward":
                return True
        return None


class OpenFilesChooseMenuCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # path: current directory
        self.view.run_command("open_files", {"key": "right"})

class OpenFilesBackwardCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("open_files", {"key": "left"})

class OpenBookmarksChooseMenuCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command(
            "open_list", {"key": "right", "list_type": "bookmarks"})

class OpenBookmarksBackwardCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command(
            "open_list", {"key": "left", "list_type": "bookmarks"})

class OpenFilesShowHiddenFiles(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("open_files", {"key": "tab"})

class OpenRecentFilesChooseMenuCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command(
            "open_list", {"key": "right", "list_type": "recent_files"})

class OpenRecentFilesBackwardCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command(
            "open_list", {"key": "left", "list_type": "recent_files"})

class OpenRecentFoldersChooseMenuCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command(
            "open_list", {"key": "right", "list_type": "recent_folders"})

class OpenRecentFoldersBackwardCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command(
            "open_list", {"key": "left", "list_type": "recent_folders"})
