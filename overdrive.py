import os

import sublime, sublime_plugin
import q
import ghost

import odutils
import odfile


files = {}


class OverdriveJoinCommand(sublime_plugin.WindowCommand):

  def run(self):
    self.window.show_input_panel("Open File:", "", self.on_done, None, None)

  def on_done(self, file_id):
    if not file_id:
      return
    od_view = OverdriveView(self.window.new_file())
    od_view.open()
    files[od_view.id] = od_file = odfile.OverdriveFile(od_view)
    od_file.open(file_id)


class OverdriveShareCommand(sublime_plugin.TextCommand):

  def run(self, edit):
    od_view = OverdriveView(self.view)
    od_view.save()
    files[od_view.id] = od_file = odfile.OverdriveFile(od_view)
    od_file.save_file(od_view.get_name(), od_view.get_text())


class OverdriveEventListener(sublime_plugin.EventListener):

  def on_modified(self, view):
    od_file = files.get(view.id())
    if not od_file:
      return
    cmd = view.command_history(0, True)
    if cmd[0] == 'overdrive_edit':
      return
    curr_text = odutils.get_text(view)
    od_file.set_text(curr_text)

  def on_close(self, view):
    od_file = files.pop(view.id(), None)
    if od_file:
      od_file.od_view.view = None


class OverdriveView(object):

  def __init__(self, view):
    self.view = view
    self.id = view.id()
    self.is_opened = False

  def open(self):
    self.view.set_status("Overdrive", "Loading file...")
    self.view.set_read_only(True)
    self.view.set_name('Loading file...')
    self.view.set_scratch(True)
    self.is_opened = True

  def save(self):
    self.view.set_status("Overdrive", "Sharing file...")

  def get_name(self):
    return os.path.basename(self.view.file_name())

  def get_text(self):
    return odutils.get_text(self.view)

  def begin_edit(self):
    return self.view.begin_edit('overdrive_edit')

  @odutils.auto_main_threaded
  def set_text(self, text):
    if self.view is None:
      return
    if self.is_opened:
      self.view.erase_status('Overdrive')
      self.view.set_read_only(False)
      edit = self.begin_edit()
      self.view.insert(edit, 0, text)
      self.view.end_edit(edit)

  @odutils.auto_main_threaded
  def set_metadata(self, metadata):
    if self.view is None:
      return
    if self.is_opened:
      self.view.set_name(metadata['title'])
    else:
      self.view.erase_status('Overdrive')
      sublime.message_dialog('File shared! Others can join in this file through this ID:\n%s' % metadata['id'])

  @odutils.auto_main_threaded
  def insert_text(self, index, text):
    if self.view is None:
      return
    edit = self.begin_edit()
    self.view.insert(edit, index, text)
    self.view.end_edit(edit)

  @odutils.auto_main_threaded
  def delete_text(self, index, text):
    if self.view is None:
      return
    region = sublime.Region(index, index + len(text))
    edit = self.begin_edit()
    self.view.erase(edit, region)
    self.view.end_edit(edit)

  @odutils.auto_main_threaded
  def close(self):
    q('close')
    window = self.view.window()
    window.focus_view(self.view)
    window.run_command('close_file')
    self.view = None

