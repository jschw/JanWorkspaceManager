import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
import appdirs

import wx


class JanWorkspaceManagerFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Jan Workspace Manager", size=(900, 600))

        # Define config paths
        config_dir = Path(appdirs.user_config_dir(appname="jan-wsmanager"))
        self.appconfig = config_dir / "appconfig.json"
        self.ensure_appconfig()

        panel = wx.Panel(self)

        self.data_path_input = wx.TextCtrl(panel)
        self.data_path_browse_button = wx.Button(panel, label="Browse")
        self.data_path_input.Bind(wx.EVT_TEXT, self.on_data_path_changed)
        self.data_path_browse_button.Bind(wx.EVT_BUTTON, self.on_browse_data_path)

        header = wx.StaticText(panel, label="Jan Workspace Manager")
        header_font = header.GetFont()
        header_font.PointSize += 6
        header_font = header_font.Bold()
        header.SetFont(header_font)

        subheader = wx.StaticText(panel, label="Manage workspaces, sync to GitHub, and switch contexts")

        settings_box = wx.StaticBox(panel, label="Settings")
        settings_sizer = wx.StaticBoxSizer(settings_box, wx.VERTICAL)
        settings_grid = wx.FlexGridSizer(rows=4, cols=1, hgap=8, vgap=8)
        settings_grid.AddGrowableCol(0, 1)

        settings_grid.Add(wx.StaticText(panel, label="Data path"), 0)
        data_path_sizer = wx.BoxSizer(wx.VERTICAL)
        data_path_sizer.Add(self.data_path_input, 0, wx.EXPAND)
        data_path_sizer.Add(self.data_path_browse_button, 0, wx.TOP, 6)
        settings_grid.Add(data_path_sizer, 0, wx.EXPAND)

        settings_grid.Add(wx.StaticText(panel, label="GitHub repo URL"), 0)
        self.github_repo_input = wx.TextCtrl(panel)
        self.github_repo_input.Bind(wx.EVT_TEXT, self.on_github_repo_changed)
        github_path_sizer = wx.BoxSizer(wx.VERTICAL)
        github_path_sizer.Add(self.github_repo_input, 0, wx.EXPAND)
        settings_grid.Add(github_path_sizer, 0, wx.EXPAND)

        settings_sizer.Add(settings_grid, 0, wx.EXPAND | wx.ALL, 12)

        workspaces_box = wx.StaticBox(panel, label="Workspaces")
        workspaces_sizer = wx.StaticBoxSizer(workspaces_box, wx.VERTICAL)
        self.workspaces_list = wx.ListCtrl(
            panel,
            style=wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_SINGLE_SEL,
        )
        self.workspaces_list.InsertColumn(0, "Workspace", width=300)
        self.workspaces_list.InsertColumn(1, "Created", width=220)
        self.workspaces_list.InsertColumn(2, "Last modified", width=220)
        workspaces_sizer.Add(self.workspaces_list, 1, wx.EXPAND | wx.ALL, 12)

        notes_box = wx.StaticBox(panel, label="Workspace notes")
        notes_sizer = wx.StaticBoxSizer(notes_box, wx.VERTICAL)
        self.notes_field = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_RICH2)
        notes_sizer.Add(self.notes_field, 1, wx.EXPAND | wx.ALL, 12)

        actions_box = wx.StaticBox(panel, label="Actions")
        actions_sizer = wx.StaticBoxSizer(actions_box, wx.VERTICAL)
        self.change_button = wx.Button(panel, label="Change to selected workspace")
        self.create_button = wx.Button(panel, label="Create new workspace")
        self.rename_button = wx.Button(panel, label="Rename workspace")
        self.snapshot_button = wx.Button(panel, label="Create workspace snapshot")
        self.push_button = wx.Button(panel, label="Push workspaces to GitHub")
        self.pull_button = wx.Button(panel, label="Pull workspaces from GitHub")
        self.quit_button = wx.Button(panel, label="Quit")

        self.change_button.Bind(wx.EVT_BUTTON, self.on_change_workspace)
        self.create_button.Bind(wx.EVT_BUTTON, self.on_create_workspace)
        self.rename_button.Bind(wx.EVT_BUTTON, self.on_rename_workspace)
        self.snapshot_button.Bind(wx.EVT_BUTTON, self.on_snapshot_workspace)
        self.push_button.Bind(wx.EVT_BUTTON, self.on_push_workspaces)
        self.pull_button.Bind(wx.EVT_BUTTON, self.on_pull_workspaces)
        self.quit_button.Bind(wx.EVT_BUTTON, self.on_quit)

        actions_sizer.Add(self.change_button, 0, wx.EXPAND | wx.ALL, 6)
        actions_sizer.Add(self.create_button, 0, wx.EXPAND | wx.ALL, 6)
        actions_sizer.Add(self.rename_button, 0, wx.EXPAND | wx.ALL, 6)
        actions_sizer.Add(self.snapshot_button, 0, wx.EXPAND | wx.ALL, 6)
        actions_sizer.Add(self.push_button, 0, wx.EXPAND | wx.ALL, 6)
        actions_sizer.Add(self.pull_button, 0, wx.EXPAND | wx.ALL, 6)
        actions_sizer.Add(self.quit_button, 0, wx.EXPAND | wx.ALL, 6)

        left_column = wx.BoxSizer(wx.VERTICAL)
        left_column.Add(settings_sizer, 0, wx.EXPAND | wx.BOTTOM, 12)
        left_column.Add(actions_sizer, 0, wx.EXPAND)

        right_column = wx.BoxSizer(wx.VERTICAL)
        right_column.Add(workspaces_sizer, 1, wx.EXPAND | wx.BOTTOM, 12)
        right_column.Add(notes_sizer, 0, wx.EXPAND)

        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        content_sizer.Add(left_column, 0, wx.EXPAND | wx.RIGHT, 16)
        content_sizer.Add(right_column, 1, wx.EXPAND)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(header, 0, wx.LEFT | wx.RIGHT | wx.TOP, 16)
        main_sizer.Add(subheader, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        main_sizer.Add(content_sizer, 1, wx.EXPAND | wx.ALL, 16)

        panel.SetSizer(main_sizer)
        self.Center()

        self.load_appconfig()
        self.populate_workspaces()

    def populate_workspaces(self):
        self.workspaces_list.DeleteAllItems()
        data_path = getattr(self, "data_path", "")
        if not data_path:
            return
        workspaces_dir = os.path.join(data_path, "workspaces")
        os.makedirs(workspaces_dir, exist_ok=True)
        for entry in sorted(os.listdir(workspaces_dir)):
            entry_path = os.path.join(workspaces_dir, entry)
            if not os.path.isdir(entry_path):
                continue
            definition_path = os.path.join(entry_path, "ws_definition.json")
            if not os.path.isfile(definition_path):
                continue
            try:
                with open(definition_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue
            name = data.get("name", entry)
            created_at = data.get("created_at", "")
            modified_at = data.get("modified_at", "")
            index = self.workspaces_list.InsertItem(self.workspaces_list.GetItemCount(), name)
            self.workspaces_list.SetItem(index, 1, created_at)
            self.workspaces_list.SetItem(index, 2, modified_at)

    def on_data_path_changed(self, event):
        path = self.data_path_input.GetValue().strip()
        self.set_data_path(path)

    def on_browse_data_path(self, event):
        data_path = self.data_path_input.GetValue().strip()
        if not data_path:
            with wx.DirDialog(self, "Select data path") as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                data_path = dialog.GetPath()
                self.data_path_input.SetValue(data_path)
        workspaces_dir = os.path.join(data_path, "workspaces")
        os.makedirs(workspaces_dir, exist_ok=True)
        wx.LaunchDefaultApplication(workspaces_dir)

    def on_change_workspace(self, event):
        selected = self.get_selected_workspace()
        self.change_workspace(selected)

    def on_github_repo_changed(self, event):
        repo_path = self.github_repo_input.GetValue().strip()
        self.set_github_repo_path(repo_path)

    def on_create_workspace(self, event):
        if not getattr(self, "data_path", ""):
            return
        save_dialog = wx.MessageDialog(
            self,
            "Do you want to save the current workspace before creating a new one?",
            "Save current workspace",
            style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        save_current = save_dialog.ShowModal() == wx.ID_YES
        save_dialog.Destroy()
        if save_current:
            current_name = self.prompt_for_required_name("Enter a name for the current workspace:")
            if not current_name:
                return
            new_name = self.prompt_for_required_name("Enter a name for the new workspace:")
            if not new_name:
                return
            self.create_workspace(current_name, copy_from_data=True, set_selected=False)
            self.clear_workspace_data()
            self.create_workspace(new_name, copy_from_data=False, set_selected=True)
        else:
            new_name = self.prompt_for_required_name("Enter a name for the new workspace:")
            if not new_name:
                return
            self.clear_workspace_data()
            self.create_workspace(new_name, copy_from_data=False, set_selected=True)

    def on_rename_workspace(self, event):
        selected = self.get_selected_workspace()
        if not selected:
            return
        name = self.prompt_for_workspace_name(prompt="Enter new workspace name:")
        if name:
            self.rename_workspace(selected, name)

    def on_snapshot_workspace(self, event):
        confirm_dialog = wx.MessageDialog(
            self,
            "Create a snapshot of the current workspace? This will copy assistants and threads into the selected workspace.",
            "Create snapshot",
            style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        confirmed = confirm_dialog.ShowModal() == wx.ID_YES
        confirm_dialog.Destroy()
        if not confirmed:
            return
        self.snapshot_current_workspace()

    def on_push_workspaces(self, event):
        self.push_workspaces()

    def on_pull_workspaces(self, event):
        self.pull_workspaces()

    def on_quit(self, event):
        self.Close()

    def get_selected_workspace(self):
        index = self.workspaces_list.GetFirstSelected()
        if index == -1:
            return None
        name = self.workspaces_list.GetItemText(index)
        return {"name": name}

    def prompt_for_workspace_name(self, prompt="Enter new workspace name:", title="Workspace"):
        dialog = wx.TextEntryDialog(self, prompt, title)
        if dialog.ShowModal() == wx.ID_OK:
            name = dialog.GetValue().strip()
        else:
            name = ""
        dialog.Destroy()
        return name

    def prompt_for_required_name(self, prompt, title="Workspace"):
        while True:
            name = self.prompt_for_workspace_name(prompt=prompt, title=title)
            if name:
                return name
            retry_dialog = wx.MessageDialog(
                self,
                "Name cannot be empty. Try again?",
                "Invalid name",
                style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
            )
            retry = retry_dialog.ShowModal() == wx.ID_YES
            retry_dialog.Destroy()
            if not retry:
                return ""

    def set_data_path(self, path):
        self.data_path = path
        if not path:
            self.save_appconfig()
            return
        workspaces_dir = os.path.join(path, "workspaces")
        os.makedirs(workspaces_dir, exist_ok=True)
        self.populate_workspaces()
        self.save_appconfig()

    def change_workspace(self, workspace):
        if not workspace:
            return
        data_path = getattr(self, "data_path", "")
        if not data_path:
            return
        selected_name = workspace.get("name") or ""
        if not selected_name:
            return
        selected_workspace_dir = self.get_workspace_dir_by_name(selected_name)
        if not selected_workspace_dir:
            return

        current_name = getattr(self, "selected_workspace", "")
        if current_name:
            current_dir = self.get_workspace_dir_by_name(current_name)
            if current_dir:
                confirm_dialog = wx.MessageDialog(
                    self,
                    "Create a snapshot of the current workspace before switching?",
                    "Create snapshot",
                    style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                )
                confirmed = confirm_dialog.ShowModal() == wx.ID_YES
                confirm_dialog.Destroy()
                if confirmed:
                    self.snapshot_current_workspace()

        self.clear_workspace_data()
        self.restore_workspace_data(selected_workspace_dir)
        self.selected_workspace = selected_name
        self.save_appconfig()
        success_dialog = wx.MessageDialog(
            self,
            f"Switched to workspace '{selected_name}'.",
            "Workspace changed",
            style=wx.OK | wx.ICON_INFORMATION,
        )
        success_dialog.ShowModal()
        success_dialog.Destroy()

    def set_github_repo_path(self, repo_path):
        self.github_repo_path = repo_path
        self.save_appconfig()

    def create_workspace(self, name, copy_from_data=True, set_selected=True):
        if not name:
            return
        data_path = getattr(self, "data_path", "")
        if not data_path:
            return
        workspaces_dir = os.path.join(data_path, "workspaces")
        os.makedirs(workspaces_dir, exist_ok=True)
        workspace_id = str(uuid.uuid4())
        workspace_dir = os.path.join(workspaces_dir, workspace_id)
        os.makedirs(workspace_dir, exist_ok=True)
        timestamp = datetime.now().isoformat()
        definition = {
            "name": name,
            "created_at": timestamp,
            "modified_at": timestamp,
        }
        definition_path = os.path.join(workspace_dir, "ws_definition.json")
        with open(definition_path, "w", encoding="utf-8") as handle:
            json.dump(definition, handle, indent=2)
        if copy_from_data:
            for folder_name in ("threads", "assistants"):
                source = os.path.join(data_path, folder_name)
                destination = os.path.join(workspace_dir, folder_name)
                if not os.path.isdir(source):
                    continue
                if os.path.exists(destination):
                    continue
                shutil.copytree(source, destination)
        if set_selected:
            self.selected_workspace = name
            self.save_appconfig()
        self.populate_workspaces()

    def snapshot_current_workspace(self):
        data_path = getattr(self, "data_path", "")
        if not data_path:
            return
        selected_name = getattr(self, "selected_workspace", "")
        if not selected_name:
            return
        workspace_dir = self.get_workspace_dir_by_name(selected_name)
        if not workspace_dir:
            return
        for folder_name in ("threads", "assistants"):
            source = os.path.join(data_path, folder_name)
            destination = os.path.join(workspace_dir, folder_name)
            if not os.path.isdir(source):
                continue
            if os.path.exists(destination):
                try:
                    shutil.rmtree(destination)
                except OSError:
                    continue
            shutil.copytree(source, destination)
        self.update_workspace_modified_at(workspace_dir)
        self.populate_workspaces()

    def restore_workspace_data(self, workspace_dir):
        data_path = getattr(self, "data_path", "")
        if not data_path:
            return
        for folder_name in ("threads", "assistants"):
            source = os.path.join(workspace_dir, folder_name)
            destination = os.path.join(data_path, folder_name)
            if os.path.isdir(source):
                if os.path.exists(destination):
                    try:
                        shutil.rmtree(destination)
                    except OSError:
                        continue
                try:
                    shutil.copytree(source, destination)
                except OSError:
                    continue
            else:
                os.makedirs(destination, exist_ok=True)

    def get_workspace_dir_by_name(self, name):
        data_path = getattr(self, "data_path", "")
        if not data_path:
            return ""
        workspaces_dir = os.path.join(data_path, "workspaces")
        if not os.path.isdir(workspaces_dir):
            return ""
        for entry in os.listdir(workspaces_dir):
            entry_path = os.path.join(workspaces_dir, entry)
            if not os.path.isdir(entry_path):
                continue
            definition_path = os.path.join(entry_path, "ws_definition.json")
            if not os.path.isfile(definition_path):
                continue
            try:
                with open(definition_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("name") == name:
                return entry_path
        return ""

    def update_workspace_modified_at(self, workspace_dir):
        definition_path = os.path.join(workspace_dir, "ws_definition.json")
        if not os.path.isfile(definition_path):
            return
        try:
            with open(definition_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return
        data["modified_at"] = datetime.now().isoformat()
        try:
            with open(definition_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
        except OSError:
            return

    def rename_workspace(self, workspace, new_name):
        if not workspace:
            return
        data_path = getattr(self, "data_path", "")
        if not data_path:
            return
        old_name = workspace.get("name") or ""
        if not old_name:
            return
        if not new_name:
            return
        if new_name == old_name:
            return
        if self.get_workspace_dir_by_name(new_name):
            dialog = wx.MessageDialog(
                self,
                f"A workspace named '{new_name}' already exists.",
                "Rename workspace",
                style=wx.OK | wx.ICON_WARNING,
            )
            dialog.ShowModal()
            dialog.Destroy()
            return
        workspace_dir = self.get_workspace_dir_by_name(old_name)
        if not workspace_dir:
            return
        definition_path = os.path.join(workspace_dir, "ws_definition.json")
        if not os.path.isfile(definition_path):
            return
        try:
            with open(definition_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return
        data["name"] = new_name
        data["modified_at"] = datetime.now().isoformat()
        try:
            with open(definition_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
        except OSError:
            return
        if getattr(self, "selected_workspace", "") == old_name:
            self.selected_workspace = new_name
            self.save_appconfig()
        self.populate_workspaces()
        dialog = wx.MessageDialog(
            self,
            f"Workspace '{old_name}' renamed to '{new_name}'.",
            "Rename workspace",
            style=wx.OK | wx.ICON_INFORMATION,
        )
        dialog.ShowModal()
        dialog.Destroy()

    def push_workspaces(self):
        pass

    def pull_workspaces(self):
        pass

    def clear_workspace_data(self):
        data_path = getattr(self, "data_path", "")
        if not data_path:
            return
        for folder_name in ("assistants", "threads"):
            folder_path = os.path.join(data_path, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                continue
            for entry in os.listdir(folder_path):
                entry_path = os.path.join(folder_path, entry)
                try:
                    if os.path.isdir(entry_path):
                        shutil.rmtree(entry_path)
                    else:
                        os.remove(entry_path)
                except OSError:
                    continue

    def ensure_appconfig(self):
        config_dir = self.appconfig.parent
        config_dir.mkdir(parents=True, exist_ok=True)
        if not self.appconfig.exists():
            initial = {
                "data_path": "",
                "github_repo_path": "",
                "selected_workspace": "",
            }
            self.appconfig.write_text(json.dumps(initial, indent=2), encoding="utf-8")

    def load_appconfig(self):
        try:
            data = json.loads(self.appconfig.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        self.data_path = data.get("data_path", "")
        self.github_repo_path = data.get("github_repo_path", "")
        self.selected_workspace = data.get("selected_workspace", "")
        if self.data_path:
            self.data_path_input.ChangeValue(self.data_path)
        if self.github_repo_path:
            self.github_repo_input.ChangeValue(self.github_repo_path)

    def save_appconfig(self):
        data = {
            "data_path": getattr(self, "data_path", ""),
            "github_repo_path": getattr(self, "github_repo_path", ""),
            "selected_workspace": getattr(self, "selected_workspace", ""),
        }
        try:
            self.appconfig.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass


class JanWorkspaceManagerApp(wx.App):
    def OnInit(self):
        frame = JanWorkspaceManagerFrame()
        frame.Show()
        return True


def main():
    app = JanWorkspaceManagerApp(False)
    app.MainLoop()


if __name__ == "__main__":
    main()
