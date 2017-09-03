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
        type(self).active = True
        # do not use self.view.window(), otherwise None for backward action
        type(self).window = sublime.active_window()
        if not key:
            self.open(path, ignore)
        elif key == "right":
            self.tab_action()
        elif key == "left":
            self.backward()
        else:
            pass
    
    def tab_action(self):
        type(self).window.run_command("hide_overlay")
        type(self).active = True
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
                else:
                    sublime.message_dialog("Please the path of pdf reader.")
            elif full_path.endswith((".csv", ".CSV", ".xslx", ".xsl")):
                excel = self.settings.get("excel", "")
                if excel:
                    subprocess.call([excel, full_path])
                else:
                    sublime.message_dialog("Please the path of Excel.")
            else:
                # furthor 
                pass
        else:
            # further file action
            pass

    def open(self, path = None, ignore = True):
        global active_menu
        active_menu = False
        self.set_files_folders(path, ignore)
        def on_done(index):
            # open files
            if index > type(self).length_folders:
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
        type(self).entries_display = ['..'] + [folder + '/' for folder in folders] + files
        type(self).entries_path = [type(self).path_parent] \
            + [join(path, folder_file) for folder_file in folders_files]

    def backward(self):
        type(self).active = True
        # hide quick panel
        type(self).window.run_command("hide_overlay")
        if active_menu:
            self.view.run_command("open_files", {"path": type(self).path_current})
        else:
            self.view.run_command("open_files", {"path": type(self).path_parent})


class OpenBookMarksCommand(sublime_plugin.TextCommand):
    active = False
    index_highlighted = None
    window = None

    @classmethod
    def reset(cls):
        cls.active = False

    def __init__(self, view):
        sublime_plugin.TextCommand.__init__(self, view)
        settings = sublime.load_settings("OpenFiles.sublime-settings")
        bookmarks = settings.get("bookmarks", [])
        # window = sublime.active_window()
        if bookmarks:
            self.names_bm = [list(bookmark.keys())[0] for bookmark in bookmarks]
            path_bm = [list(bookmark.values())[0] for bookmark in bookmarks]
            pkg_path = sublime.packages_path()
            path_bm = [path if os.path.isabs(path) else join(pkg_path, path) for path in path_bm]
            self.path_bm = [path.replace("/", "\\") for path in path_bm]
        else:
            self.names_bm = None
            self.path_bm = None


    def run(self, edit, key = None):
        type(self).active = True
        type(self).window = sublime.active_window()
        if not key:
            self.open()
        elif key == "left":
            self.backward()
        elif key == "right":
            self.tab_action()

    def open(self):
        def on_highlighted(index):
            type(self).index_highlighted = index

        def on_done(index):
            if index >= 0:
                # do not use self.view, otherwise do not work after left key?
                sublime.active_window().active_view().run_command(
                    "open_files", {"path": self.path_bm[index]})
            else:
                pass
        # do not use self.view.window()
        type(self).window.show_quick_panel(
            self.names_bm, on_done, sublime.MONOSPACE_FONT, 0, on_highlighted)

    def act_folder(self, index):
        full_path = self.path_bm[type(self).index_highlighted]
        if index == 0:
            subprocess.call(["explorer", full_path])
        elif index == 1:
            sublime.set_clipboard(full_path)
        elif index == 2:
            sublime.set_clipboard(os.path.basename(full_path))
        else:
            # further path action
            pass

    def tab_action(self):
        type(self).window.run_command("hide_overlay")
        # must after type(self).window.run_command("hide_overlay")
        # otherwise active become false. why?
        type(self).active = True
        action_folder = ["Open Folder in Explorer", "Copy Path to Clipboard", 
                         "Copy Folder Name to Clipboard"]
        action_list = [[action, self.path_bm[type(self).index_highlighted]] 
            for action in action_folder]

        on_done = self.act_folder

        type(self).window.show_quick_panel(action_list, on_done)

    def backward(self):
        type(self).window.run_command("hide_overlay")
        self.view.run_command("open_book_marks")



class OpenFilesListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        group, index = view.window().get_view_index(view)
        if group == -1 and index == -1 and OpenFilesCommand.active:
            sublime.quickPanelView = view
        else:
            OpenFilesCommand.reset()
            sublime.quickPanelView = None
        if group == -1 and index == -1 and OpenBookMarksCommand.active:
            sublime.quickPanelViewBookMarks = view
        else:
            OpenBookMarksCommand.reset()
            sublime.quickPanelViewBookMarks = None

    def on_query_context(self, view, key, operator, operand, match_all):
        if view == sublime.quickPanelView:
            if key == "open_files_backward":
                return True
            if not active_menu:
                if key == "open_files_choose_menu":
                    return True
        if view == sublime.quickPanelViewBookMarks:
            if key == "open_book_marks_choose_menu":
                return True
            if key == "open_book_marks_backward":
                return True
        return None

class OpenFilesChooseMenuCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # path: current directory
        self.view.run_command("open_files", {"key": "right"})

class OpenFilesBackwardCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("open_files", {"key": "left"})

class OpenBookMarksChooseMenuCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("open_book_marks", {"key": "right"})

class OpenBookMarksBackwardCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("open_book_marks", {"key": "left"})
