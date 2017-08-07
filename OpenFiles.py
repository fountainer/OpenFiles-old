import sublime, sublime_plugin
import os
from os.path import join


class OpenFilesCommand(sublime_plugin.TextCommand):
    def run(self, edit, path = None):
        files, folders, path = self.get_files_folders(path)
        entries = folders + files
        # show in the quick panel
        entries_display = [folder + "/" for folder in folders] + files
        is_root_dir = True
        path_parent = os.path.dirname(path)
        if path != path_parent:
            is_root_dir = False
            # insert a placeholder
            entries = [""] + entries
            # parent directory symbol
            entries_display = [".."] + entries_display
        window = self.view.window()

        def on_done(index):
            # open files
            if index > (len(folders) - is_root_dir):
                window.open_file(join(path, entries[index]))
            # open subdirectory
            elif index > 0:
                next_path = join(path, entries[index])
                window.run_command("open_files", {"path": next_path})
            # open subdirectory
            elif index == 0 and is_root_dir:
                next_path = join(path, entries[index])
                window.run_command("open_files", {"path": next_path})
            # open parent directory
            elif index == 0 and not is_root_dir:
                next_path = path_parent
                window.run_command("open_files", {"path": next_path})
            else:
                pass

        window.show_quick_panel(entries_display, on_done)

    def get_files_folders(self, path = None):
        if path is None:
            path = os.path.dirname(self.view.file_name())
        entries = os.listdir(path)
        files = [file for file in entries if os.path.isfile(join(path, file))]
        folders = list(set(entries) - set(files))
        # can not place it in the global environment, because it run only once?
        settings = sublime.load_settings("OpenFiles.sublime-settings")
        ignored_extensions = tuple(settings.get("ignored_extensions", ()))
        # must after folders = list(set(entries) - set(files))
        files = [file for file in files if not file.lower().endswith(ignored_extensions)]
        return((files, folders, path))


