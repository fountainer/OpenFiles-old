import sublime, sublime_plugin
import os
from os.path import join
import subprocess

active_menu = False

class OpenFilesCommand(sublime_plugin.TextCommand):
    active = False
    index_highlighted = 0
    command_list = ["Open in Explorer", "Placeholder"]
    action_folder = ["Open Folder in Explorer", "Copy Path to Clipboard", 
                     "Copy Folder Name to Clipboard"]
    action_file = ["Open Containing Folder", "Copy File Path to Clipboard", 
                   "Copy File Name to Clipboard", "Open with Application"]
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
        print("@@@@", path, "@@@@")
        type(self).active = True
        # do not use self.view.window(), otherwise None for backward action
        type(self).window = sublime.active_window()
        if not key:
            print("test")
            self.open(path, ignore)
        elif key == "right":
            self.tab_action()
        elif key == "left":
            self.backward()
    
    def tab_action(self):
        type(self).window.run_command("hide_overlay")
        type(self).active = True
        # type(self).active_menu = True
        global active_menu
        active_menu = True
        if type(self).index_highlighted > type(self).length_folders:
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
        print(active_menu)
        type(self).window.show_quick_panel(action_list, on_done)

    def act_folder(self, index):
        full_path = type(self).entries_path[type(self).index_highlighted]
        if index == 0:
            subprocess.call(["explorer", full_path])
        elif index == 1:
            sublime.set_clipboard(full_path)
        elif index == 2:
            sublime.set_clipboard(os.path.basename(full_path))
        else:
            # further path action
            pass

    def act_file(self, index):
        full_path = type(self).entries_path[type(self).index_highlighted]
        if index == 0:
            subprocess.call(["explorer", type(self).path_current])
        elif index == 1:
            sublime.set_clipboard(full_path)
        elif index == 2:
            sublime.set_clipboard(os.path.basename(full_path))
        elif index == 3:
            if full_path.endswith(".pdf"):
                pdf_reader = self.settings.get("pdf_reader", "")
                if pdf_reader:
                    subprocess.call([pdf_reader, full_path])
            elif full_path.endswith((".csv", ".CSV", ".xslx", ".xsl")):
                excel = self.settings.get("excel", "")
                if excel:
                    subprocess.call([excel, full_path])
            else:
                # furthor 
                pass
        else:
            # further file action
            pass

    def open(self, path = None, ignore = True):
        print("$$", path, "$$")
        global active_menu
        active_menu = False
        self.set_files_folders(path, ignore)
        # window = self.view.window()
        print(">>>>", self.view.id(), "<<<<<<")
        print("---", type(self).window, "-----")
        def on_done(index):
            # open files
            if index > type(self).length_folders:
                # delete index - 1
                type(self).window.open_file(type(self).entries_path[index])
            # open subdirectory
            elif index > 0:
                # delete - 1
                print("not run")
                print(type(self).entries_path[index])
                print("^^^^", self.view.id(), "^^^^^^")
                # subprocess.call(["explorer", type(self).entries_path[index]])
                self.view.run_command("open_files", {"path": type(self).entries_path[index]})
                print("run after")
            # open parent directory
            elif index == 0:
                self.view.run_command("open_files", {"path": type(self).path_parent})
            else:
                pass
                # reset?
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
        type(self).entries_display = ['..'] + [folder + '/' for folder in folders] + files
        type(self).entries_path = [type(self).path_parent] \
            + [join(path, folder_file) for folder_file in folders_files]

    def backward(self):
        print(sublime.quickPanelView.id(), self.view.id())
        # print(type(self).active_menu)
        type(self).window.run_command("hide_overlay")
        # check quick panel file view or menu view
        print(active_menu)
        if active_menu:
            self.view.run_command("open_files", {"path": type(self).path_current})
            print("menu is active")
        else:
            print("file list")
        # print(type(self).active_menu)


class OpenBookMarksCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        sublime_plugin.TextCommand.__init__(self, view)
        self.settings = sublime.load_settings("OpenFiles.sublime-settings")

    def run(self, edit):
        bookmarks = self.settings.get("bookmarks", [])
        if not bookmarks:
            sublime.message_dialog("Empty bookmark")
        names_bm = [list(bookmark.keys())[0] for bookmark in bookmarks]
        path_bm = [list(bookmark.values())[0] for bookmark in bookmarks]
        pkg_path = sublime.packages_path()
        path_bm = [path if os.path.isabs(path) else join(pkg_path, path) for path in path_bm]
        window = sublime.active_window()

        def on_done(index):
            if index >= 0:
                window.run_command("open_files", {"path": path_bm[index]})
            else:
                pass
        window.show_quick_panel(names_bm, on_done)


class OpenFilesListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        group, index = view.window().get_view_index(view)
        # print(group, index, OpenFilesCommand.active)
        if group == -1 and index == -1 and OpenFilesCommand.active:
            sublime.quickPanelView = view
        else:
            OpenFilesCommand.reset()
            sublime.quickPanelView = None

    def on_query_context(self, view, key, operator, operand, match_all):
        if (view == sublime.quickPanelView):
            if key == "open_files_backward":
                return True
            if not active_menu:
                if key == "open_files_choose_menu":
                    return True
        return None

class OpenFilesChooseMenu(sublime_plugin.TextCommand):
    def run(self, edit):
        # path: current directory
        self.view.run_command("open_files", {"key": "right"})

class OpenFilesBackward(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("open_files", {"key": "left"})
