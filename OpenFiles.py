import sublime, sublime_plugin
import os
from os.path import join
import subprocess


class OpenFilesCommand(sublime_plugin.TextCommand):
    active = False
    index_highlighted = 0
    command_list = ["Open in Explorer", "Placeholder"]
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

    def run(self, edit, path = None, tab = False):
        self.__class__.active = True
        self.__class__.window = self.view.window()
        if not tab:
            self.open(path)
        else:
            self.tab_action()
    
    def tab_action(self):
        self.__class__.window.run_command("hide_overlay")

        def on_done(index):
            if index == 0:
                if self.__class__.index_highlighted > self.__class__.length_folders:
                    subprocess.call(["explorer", self.__class__.path_current])
                elif self.__class__.index_highlighted > 0:
                    subprocess.call(["explorer", self.__class__.entries_path[self.__class__.index_highlighted - 1]])
                elif self.__class__.index_highlighted == 0:
                    subprocess.call(["explorer", self.__class__.path_parent])
                else:
                    pass
            elif index == -1:
                pass
            else:
                sublime.message_dialog('placeholder')
                
        command_list = [[command, self.__class__.entries_path[self.__class__.index_highlighted - 1]]
            for command in self.__class__.command_list]
        self.__class__.window.show_quick_panel(command_list, 
            on_done)

    def open(self, path = None):
        self.set_files_folders(path)
        window = self.view.window()

        def on_done(index):
            # open files
            if index > self.__class__.length_folders:
                window.open_file(self.__class__.entries_path[index - 1])
            # open subdirectory
            elif index > 0:
                window.run_command("open_files", {"path": self.__class__.entries_path[index - 1]})
            # open parent directory
            elif index == 0:
                window.run_command("open_files", {"path": self.__class__.path_parent})
            else:
                pass
                # reset?
        window.show_quick_panel(self.__class__.entries_display, on_done, sublime.MONOSPACE_FONT,
            0, OpenFilesCommand.on_highlighted)


    def set_files_folders(self, path = None):
        if path is None:
            path = os.path.dirname(self.view.file_name())
        try:
            entries = os.listdir(path)
        except FileNotFoundError as fnfe:
            sublime.error_message(str(fnfe))
        self.__class__.path_current = path
        self.__class__.path_parent = os.path.dirname(path)
        files = [file for file in entries if os.path.isfile(join(path, file))]
        folders = list(set(entries) - set(files))
        self.__class__.length_folders = len(folders)
        # can not place it in the global environment, because it run only once?
        ignored_extensions = tuple(self.settings.get("ignored_extensions", ()))
        # must after folders = list(set(entries) - set(files))
        files = [file for file in files if not file.lower().endswith(ignored_extensions)]
        folders_files = folders + files
        self.__class__.entries_display = ['..'] + [folder + '/' for folder in folders] + files
        self.__class__.entries_path = [join(path, folder_file) for folder_file in folders_files]


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
        window = self.view.window()

        def on_done(index):
            if index >= 0:
                window.run_command("open_files", {"path": path_bm[index]})
            else:
                pass
        window.show_quick_panel(names_bm, on_done)


class OpenFilesListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        group, index = view.window().get_view_index(view)
        if group == -1 and index == -1 and OpenFilesCommand.active:
            sublime.quickPanelView = view
        else:
            OpenFilesCommand.reset()
            sublime.quickPanelView = None

    def on_query_context(self, view, key, operator, operand, match_all):
        if (view == sublime.quickPanelView):
            if key == "open_files_choose_menu":
                return True
        return None

class OpenFilesChooseMenu(sublime_plugin.TextCommand):
    def run(self, edit):
        # path: current directory
        self.view.run_command("open_files", {"path": None, "tab": True})
