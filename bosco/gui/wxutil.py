import wx

from wx.lib.scrolledpanel import ScrolledPanel

from bosco.editor import RunEditor
from bosco.util import load_config

conf = load_config()

class EditingPanel(ScrolledPanel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.SetupScrolling()

    @staticmethod
    def SetValidationLabel(label, result):
        label.SetLabel(result)
        if result == 'OK':
            label.SetForegroundColour('Green')
        elif result == 'NA':
            label.SetForegroundColour('Gray')
        else:
            label.SetForegroundColour('Red')


class BaseRunPanel(EditingPanel):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.editor = RunEditor(conf.store, conf.event)
        self.editor.add_observer(self)

    def UpdateRun(self):
        self.runner_sicard.SetLabel(self.editor.runner_sicard)

        self.run_id.SetLabel(self.editor.run_id)
        self.SetValidationLabel(
            self.run_validation,
            self.editor.run_validation,
        )
        self.SetValidationLabel(
            self.team_validation,
            self.editor.team_validation,
        )
        self.run_score.SetLabel(self.editor.run_score)
        self.team_score.SetLabel(self.editor.team_score)

        self.clear_time.SetLabel(self.editor.run_clear_time)
        self.check_time.SetLabel(self.editor.run_check_time)

        punchlist = self.editor.punchlist
        grid_size = self.punches_grid.GetNumberRows()
        if len(punchlist) > grid_size:
            self.punches_grid.AppendRows(numRows=len(punchlist) - grid_size)
        elif len(punchlist) < grid_size:
            self.punches_grid.DeleteRows(numRows=grid_size - len(punchlist))
        for row, p in enumerate(punchlist):
            self.punches_grid.SetReadOnly(row, 0)
            self.punches_grid.SetReadOnly(row, 1)
            self.punches_grid.SetReadOnly(row, 2)
            self.punches_grid.SetReadOnly(row, 3)
            self.punches_grid.SetCellRenderer(
                row,
                3,
                wx.grid.GridCellDateTimeRenderer(),
            )
            self.punches_grid.SetCellRenderer(
                row,
                4,
                wx.grid.GridCellDateTimeRenderer(),
            )
            self.punches_grid.SetCellRenderer(
                row,
                5,
                wx.grid.GridCellBoolRenderer(),
            )
            # The GridCellBoolEditor does not work as expected
            # bool_editor = wx.grid.GridCellBoolEditor()
            # bool_editor.UseStringValues(valueTrue='1', valueFalse='0')
            # self.punches_grid.SetCellEditor(
            #     row,
            #     5,
            #     bool_editor,
            # )
            self.punches_grid.SetReadOnly(row, 6)
            for col, v in enumerate(p):
                self.punches_grid.SetCellValue(row, col, v)

                if p[6] == 'missing':
                    self.punches_grid.SetCellTextColour(row, col, 'Red')
                elif p[6] == 'additional' or p[6] == 'ignored':
                    self.punches_grid.SetCellTextColour(row, col, 'Gray')
                elif p[6] == 'ok':
                    self.punches_grid.SetCellTextColour(row, col, 'Green')
                else:
                    self.punches_grid.SetCellTextColour(row, col, 'Black')

                if p[6] == 'missing' and col == 5:
                    self.punches_grid.SetReadOnly(row, col)
                elif col == 5:
                    self.punches_grid.SetReadOnly(row, col, False)

        self.punches_grid.AutoSize()
        # Ensure a scroll bar is added to the parent Panel if needed
        self.punches_grid.GetParent().Layout()
        self.Layout()


class RunSearchWidget(wx.SearchCtrl):

    def __init__(self, *args, **kwargs):
        super(RunSearchWidget, self).__init__(*args, **kwargs)
        self._finder = None
        self.Disable()

        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.SetSearchTerm, self)
        self.Bind(wx.EVT_TEXT, self.SetSearchTerm, self)

    def SetFinder(self, finder):
        self._finder = finder
        if finder is not None:
            self.Enable()
        else:
            self.Disable()

    def SetSearchTerm(self, event):
        self._finder.set_search_term(self.GetValue())
