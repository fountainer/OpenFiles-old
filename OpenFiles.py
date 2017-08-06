import sublime, sublime_plugin
import os
from os.path import join

settings = sublime.load_settings("OpenFiles.sublime-settings")
ignored_extensions = tuple(settings.get("ignored_extensions", ()))


class OpenFilesCommand(sublime_plugin.TextCommand):
    def run(self, edit, path = None):
        files, folders, path = self.get_files_folders(path)
        entries = [folder + "/" for folder in folders] + files
        if not entries:
            sublime.message_dialog("Empty folder!")
            return 
        window = self.view.window()

        def on_done(index):
            if index >= len(folders):
                window.open_file(join(path, entries[index]))
            elif (index >= 0):
                sub_path = join(path, entries[index])
                window.run_command("open_files", {"path": sub_path})
            else:
                pass

        window.show_quick_panel(entries, on_done)

    def get_files_folders(self, path = None):
        if path is None:
            path = os.path.dirname(self.view.file_name())
        entries = os.listdir(path)
        files = [file for file in entries if os.path.isfile(join(path, file))]
        folders = list(set(entries) - set(files))
        # must after folders = list(set(entries) - set(files))
        files = [file for file in files if not file.lower().endswith(ignored_extensions)]
        return((files, folders, path))


