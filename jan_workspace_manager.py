import wx


class JanWorkspaceManagerFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Jan Workspace Manager", size=(900, 600))
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

        settings_grid.Add(wx.StaticText(panel, label="GitHub repo path"), 0)
        self.github_repo_input = wx.TextCtrl(panel)
        self.github_repo_browse_button = wx.Button(panel, label="Browse")
        self.github_repo_input.Bind(wx.EVT_TEXT, self.on_github_repo_changed)
        self.github_repo_browse_button.Bind(wx.EVT_BUTTON, self.on_browse_github_repo)
        github_path_sizer = wx.BoxSizer(wx.VERTICAL)
        github_path_sizer.Add(self.github_repo_input, 0, wx.EXPAND)
        github_path_sizer.Add(self.github_repo_browse_button, 0, wx.TOP, 6)
        settings_grid.Add(github_path_sizer, 0, wx.EXPAND)

        settings_sizer.Add(settings_grid, 0, wx.EXPAND | wx.ALL, 12)

        workspaces_box = wx.StaticBox(panel, label="Workspaces")
        workspaces_sizer = wx.StaticBoxSizer(workspaces_box, wx.VERTICAL)
        self.workspaces_list = wx.ListCtrl(
            panel,
            style=wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_SINGLE_SEL,
        )
        self.workspaces_list.InsertColumn(0, "Workspace", width=360)
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
        self.push_button = wx.Button(panel, label="Push workspaces to GitHub")
        self.pull_button = wx.Button(panel, label="Pull workspaces from GitHub")
        self.edit_config_button = wx.Button(panel, label="Edit config")
        self.quit_button = wx.Button(panel, label="Quit")

        self.change_button.Bind(wx.EVT_BUTTON, self.on_change_workspace)
        self.create_button.Bind(wx.EVT_BUTTON, self.on_create_workspace)
        self.rename_button.Bind(wx.EVT_BUTTON, self.on_rename_workspace)
        self.push_button.Bind(wx.EVT_BUTTON, self.on_push_workspaces)
        self.pull_button.Bind(wx.EVT_BUTTON, self.on_pull_workspaces)
        self.edit_config_button.Bind(wx.EVT_BUTTON, self.on_edit_config)
        self.quit_button.Bind(wx.EVT_BUTTON, self.on_quit)

        actions_sizer.Add(self.change_button, 0, wx.EXPAND | wx.ALL, 6)
        actions_sizer.Add(self.create_button, 0, wx.EXPAND | wx.ALL, 6)
        actions_sizer.Add(self.rename_button, 0, wx.EXPAND | wx.ALL, 6)
        actions_sizer.Add(self.push_button, 0, wx.EXPAND | wx.ALL, 6)
        actions_sizer.Add(self.pull_button, 0, wx.EXPAND | wx.ALL, 6)
        actions_sizer.Add(self.edit_config_button, 0, wx.EXPAND | wx.ALL, 6)
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

        self.populate_dummy_workspaces()

    def populate_dummy_workspaces(self):
        dummy = [
            "Example Workspace A",
            "Example Workspace B",
        ]
        for name in dummy:
            self.workspaces_list.InsertItem(self.workspaces_list.GetItemCount(), name)

    def on_data_path_changed(self, event):
        path = self.data_path_input.GetValue().strip()
        self.dummy_set_data_path(path)

    def on_browse_data_path(self, event):
        with wx.DirDialog(self, "Select data path") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.data_path_input.SetValue(dialog.GetPath())

    def on_change_workspace(self, event):
        selected = self.get_selected_workspace()
        self.dummy_change_workspace(selected)

    def on_github_repo_changed(self, event):
        repo_path = self.github_repo_input.GetValue().strip()
        self.dummy_set_github_repo_path(repo_path)

    def on_browse_github_repo(self, event):
        with wx.DirDialog(self, "Select GitHub repo path") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.github_repo_input.SetValue(dialog.GetPath())

    def on_create_workspace(self, event):
        name = self.prompt_for_workspace_name()
        if name:
            self.dummy_create_workspace(name)

    def on_rename_workspace(self, event):
        selected = self.get_selected_workspace()
        if not selected:
            return
        name = self.prompt_for_workspace_name(prompt="Enter new workspace name:")
        if name:
            self.dummy_rename_workspace(selected, name)

    def on_push_workspaces(self, event):
        self.dummy_push_workspaces()

    def on_pull_workspaces(self, event):
        self.dummy_pull_workspaces()

    def on_edit_config(self, event):
        self.dummy_edit_config()

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

    def dummy_set_data_path(self, path):
        pass

    def dummy_change_workspace(self, workspace):
        pass

    def dummy_set_github_repo_path(self, repo_path):
        pass

    def dummy_create_workspace(self, name):
        pass

    def dummy_rename_workspace(self, workspace, new_name):
        pass

    def dummy_push_workspaces(self):
        pass

    def dummy_pull_workspaces(self):
        pass

    def dummy_edit_config(self):
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
