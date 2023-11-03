# -*- coding: utf-8 -*-

import sys

from datetime import datetime
from datetime import timedelta
from traceback import format_exception

import wx
import wx.grid

from sireader import SIReaderCardChanged
from sireader import SIReaderException
from sireader import SIReaderTimeout
from wx.lib.embeddedimage import PyEmbeddedImage

from bosco.editor import Reports
from bosco.editor import RunEditor
from bosco.editor import RunEditorException
from bosco.editor import RunFinder
from bosco.editor import TeamEditor
from bosco.editor import TeamFinder
from bosco.gui import wxglade
from bosco.util import load_config

conf = load_config()

sicard = PyEmbeddedImage(
    "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"
    "QmCC")


def fix_searchctrl_min_size(ctrl):
    """ Fix MinSize of SearchCtrl widgets on GTK3
    Something is wrong with the bestsize of the SearchCtrl, so for now
    let's set it based on the size of a TextCtrl.
    """
    if 'gtk3' in wx.PlatformInfo:
        txt = wx.TextCtrl(ctrl.GetParent())
        bs = txt.GetBestSize()
        txt.DestroyLater()
        ctrl.SetMinSize((200, bs.height+4))


class ReportsPanel(wxglade.ReportsPanel):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._reports = Reports(conf.store, conf.event)

        # populate reports list
        for r in self._reports.list_reports():
            self.report_combo.Append(r[1], r[0])

    def update(self):
        busy = wx.BusyCursor()

        try:
            runs = self._reports.runs
            grid_size = self.run_grid.GetNumberRows()
            if len(runs) > grid_size:
                self.run_grid.AppendRows(numRows=len(runs) - grid_size)
            elif len(runs) < grid_size:
                self.run_grid.DeleteRows(numRows=grid_size - len(runs))

            for row, r in enumerate(runs):
                for col, v in enumerate(r):
                    self.run_grid.SetCellValue(row, col, v)

            self.run_grid.AutoSize()
            self.Layout()
        finally:
            del busy

    def ChangeReport(self, event):
        report = self.report_combo.GetClientData(
            self.report_combo.GetSelection()
        )
        self._reports.set_report(report)

        # update run list
        self.update()


class RunnerPanel(wxglade.RunnerPanel):
    pass


class TeamPanel(wxglade.TeamPanel):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.editor = TeamEditor(conf.store, conf.event)
        self.editor.add_observer(self)

        self._finder = TeamFinder(conf.store)
        self._finder.add_observer(self)

        fix_searchctrl_min_size(self.searchbox)

        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.SetSearchTerm,
                  self.searchbox)
        self.Bind(wx.EVT_TEXT, self.SetSearchTerm,
                  self.searchbox)

        self.update(self.editor, None)

    def update(self, observable, event, message=None):
        def update_itemfinder():
            first_selected = self.searchresults.GetFirstSelected()
            if first_selected < 0:
                current_item = None
            else:
                current_item = self.searchresults.GetItemData(
                    first_selected,
                )
            self.searchresults.DeleteAllItems()
            results = self._finder.get_results()
            for item in results:
                index = self.searchresults.InsertItem(
                    sys.maxsize,
                    str(item[0]),
                )
                self.searchresults.SetItemData(index, item[0])
                for col, v in enumerate(item[0:]):
                    self.searchresults.SetItem(index, col, str(v))
                    # activate if it's the current run
                    if item[0] == current_item:
                        self.searchresults.SetItemState(
                            index,
                            wx.LIST_STATE_SELECTED,
                            wx.LIST_STATE_SELECTED,
                        )

        try:
            busy = wx.BusyCursor()

            # Disable Event handling while updating
            self.SetEvtHandlerEnabled(False)

            if type(observable) == TeamFinder:
                update_itemfinder()

            else:

                self.SetValidationLabel(self.validation, self.editor.validation)

                self.score.SetLabel(self.editor.score)

                runs = self.editor.runs
                grid_size = self.run_grid.GetNumberRows()
                if len(runs) > grid_size:
                    self.run_grid.AppendRows(numRows=len(runs) - grid_size)
                elif len(runs) < grid_size:
                    self.run_grid.DeleteRows(numRows=grid_size - len(runs))

                for row, r in enumerate(runs):
                    for col, v in enumerate(r):
                        self.run_grid.SetCellValue(row, col, v)

                self.run_grid.AutoSize()
                self.Layout()
        finally:
            # Enable Event handling after updating
            self.SetEvtHandlerEnabled(True)

            # delete the busy cursor even if an exception occurs
            del busy

    def SetTeam(self, event):
        self.editor.load(self.searchresults.GetItemData(event.Index))

    def SetSearchTerm(self, event):
        self._finder.set_search_term(event.GetString())


class RunPanel(wxglade.RunPanel):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        fix_searchctrl_min_size(self.searchbox)

        # set searchresult column headers
        self.searchresults.InsertColumn(0, "ID")
        self.searchresults.SetColumnWidth(0, 30)
        self.searchresults.InsertColumn(1, "Course")
        self.searchresults.SetColumnWidth(1, 60)
        self.searchresults.InsertColumn(2, "Readout time")
        self.searchresults.SetColumnWidth(2, 100)
        self.searchresults.InsertColumn(3, "Number")
        self.searchresults.SetColumnWidth(3, 60)
        self.searchresults.InsertColumn(4, "Runner")
        self.searchresults.SetColumnWidth(4, 220)
        self.searchresults.InsertColumn(5, "Team/Club")
        self.searchresults.SetColumnWidth(5, 220)
        self.searchresults.InsertColumn(6, "Category")
        self.searchresults.SetColumnWidth(6, 60)

        self.manual_start_time.Bind(wx.EVT_KILL_FOCUS, self.SetManualStartTime)
        self.manual_finish_time.Bind(
            wx.EVT_KILL_FOCUS,
            self.SetManualFinishTime,
        )
        self.runner_number.Bind(wx.EVT_KILL_FOCUS, self.SetRunnerNumber)
        self.runner_category.Bind(wx.EVT_KILL_FOCUS, self.SetRunnerCategory)
        self.runner_given_name.Bind(wx.EVT_KILL_FOCUS, self.SetRunnerGivenName)
        self.runner_surname.Bind(wx.EVT_KILL_FOCUS, self.SetRunnerSurname)
        self.runner_dateofbirth.Bind(
            wx.EVT_KILL_FOCUS,
            self.SetRunnerDateofbirth,
        )
        self.runner_club.Bind(wx.EVT_KILL_FOCUS, self.SetRunnerClub)

        # To avoid updates if the field is not changed and the focus just
        # enters the field and leaves it again without the user changeing any
        # text, track if the field was changed: self.ResetFieldChanged sets
        # self.field_changed = False and self.FieldChanged  which is called on
        # any EVT_TEXT event sets it to True. All the callbacks called on
        # EVT_KILL_FOCUS first check this self.field_changed.
        for field in (
                self.manual_start_time,
                self.manual_finish_time,
                self.runner_number,
                self.runner_category,
                self.runner_given_name,
                self.runner_surname,
                self.runner_dateofbirth,
                self.runner_club,
        ):
            field.Bind(wx.EVT_SET_FOCUS, self.ResetFieldChanged)

        self.field_changed = False
        self._punch_changed = False

        self.finder = RunFinder(conf.store)
        self.finder.add_observer(self)
        self.searchbox.SetFinder(self.finder)
        self.update(self.finder, None)
        self.update(self.editor, 'run')

        self.UpdateCombo(
            self.run_runner_combo,
            None,
            self.editor.get_runnerlist(),
        )
        self.UpdateCombo(self.runner_team, None, self.editor.get_teamlist())

        self.Layout()

    @staticmethod
    def GetComboData(combo):
        return combo.GetClientData(combo.GetSelection())

    def ResetFieldChanged(self, e):
        self.field_changed = False

    def FieldChanged(self, e):
        self.field_changed = True

    def SetRunRunner(self, event):
        self.editor.set_runner(self.GetComboData(self.run_runner_combo))

    def SetCourse(self, event):
        self.editor.set_course(self.course.GetValue().upper().strip())

    def SetManualStartTime(self, event):
        if not self.field_changed:
            return

        try:
            self.editor.set_manual_start_time(
                self.manual_start_time.GetValue().strip(),
            )
        except ValueError as msg:
            self.GetGrandParent().ErrorDialog(str(msg), 'invalid time format')
            self.manual_start_time.SetFocus()

    def SetManualFinishTime(self, event):
        if not self.field_changed:
            return

        try:
            self.editor.set_manual_finish_time(
                self.manual_finish_time.GetValue().strip(),
            )
        except ValueError as msg:
            self.GetGrandParent().ErrorDialog(str(msg), 'invalid time format')
            self.manual_finish_time.SetFocus()

    def SetRunnerNumber(self, event):
        if not self.field_changed:
            return

        try:
            self.editor.set_runner_number(
                self.runner_number.GetValue().strip(),
            )
        except RunEditorException as e:
            dlg = wx.MessageDialog(
                self,
                f'{e} Only one runner may have this number. Do you want to '
                f'assign the number to this runner?',
                'duplicate number',
                style=wx.YES_NO | wx.ICON_QUESTION,
            )
            answer = dlg.ShowModal()
            dlg.Destroy()
            if answer == wx.ID_YES:
                self.editor.set_runner_number(
                    self.runner_number.GetValue().strip(),
                    force=True,
                )
            elif answer == wx.ID_NO:
                self.runner_number.SetValue(self.editor.runner_number)
                self.runner_number.SetFocus()

    def SetRunnerCategory(self, event):
        if not self.field_changed:
            return

        self.editor.set_runner_category(
            self.runner_category.GetValue().upper().strip(),
        )

    def SetRunnerGivenName(self, event):
        if not self.field_changed:
            return

        self.editor.set_runner_given_name(
            self.runner_given_name.GetValue().strip(),
        )

    def SetRunnerSurname(self, event):
        if not self.field_changed:
            return

        self.editor.set_runner_surname(self.runner_surname.GetValue().strip())

    def SetRunnerDateofbirth(self, event):
        if not self.field_changed:
            return

        try:
            self.editor.set_runner_dateofbirth(
                self.runner_dateofbirth.GetValue().strip(),
            )
        except ValueError as msg:
            self.GetGrandParent().ErrorDialog(str(msg), 'invalid date format')
            self.runner_dateofbirth.SetFocus()

    def SetRunnerTeam(self, event):
        self.editor.set_runner_team(self.GetComboData(self.runner_team))

    def SetRunnerClub(self, event):
        if not self.field_changed:
            return

        try:
            self.editor.set_runner_club(self.runner_club.GetValue().strip())
        except ValueError as msg:
            self.GetGrandParent().ErrorDialog(str(msg), 'invalid club')
            self.runner_club.SetFocus()

    def SetOverride(self, event):
        self.editor.set_override(self.override.GetSelection())

    def SetComplete(self, event):
        self.editor.set_complete(self.complete.GetValue())

    def Commit(self, event):
        try:
            self.editor.commit()
        except Exception as msg:
            self.editor.rollback()
            self.GetGrandParent().ErrorDialog(str(msg), 'Error saving changes')

    def AddRun(self, event):
        self.editor.new()

    def EditPunch(self, event):

        def FindLastPunchtime(punch):
            if punch == 0:
                return ''

            last_manual = self.punches_grid.GetCellValue(punch-1, 4)
            last_card = self.punches_grid.GetCellValue(punch-1, 3)

            if last_manual != '':
                return last_manual
            elif last_card != '':
                return last_card
            else:
                return FindLastPunchtime(punch-1)

        punch = event.GetRow()
        col = event.GetCol()

        # Set default value if no value is set
        if col == 4 and self.punches_grid.GetCellValue(punch, 4) == '':
            if self.punches_grid.GetCellValue(punch, 6) == 'missing':
                punchtime = self.editor.parse_time(FindLastPunchtime(punch))
                if punchtime is not None:
                    # Add 1 second for new punch
                    punchtime += timedelta(seconds=1)
                else:
                    punchtime = str(datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S',
                    ))
                wx.CallAfter(
                    self.punches_grid.SetCellValue,
                    punch,
                    col,
                    str(punchtime),
                )
                self._punch_changed = True
            elif col == 4:
                self.punches_grid.SetCellValue(
                    punch,
                    col,
                    self.punches_grid.GetCellValue(punch, 3),
                )
                self._punch_changed = True

    def ExitPunch(self, event):
        if self._punch_changed:
            self._punch_changed = False
            self.ChangePunch(event)

    def ChangePunch(self, event):
        punch = event.GetRow()
        col = event.GetCol()

        if col == 4:
            try:
                self.editor.set_punchtime(
                    punch,
                    self.punches_grid.GetCellValue(punch, col).strip(),
                )
            except ValueError as msg:
                self.GetGrandParent().ErrorDialog(
                    str(msg),
                    'invalid time format',
                )
                event.Veto()
                return
        elif col == 5:
            self.editor.set_ignore(punch,
                                   self.punches_grid.GetCellValue(punch, col))

    def Rollback(self, event):
        self.editor.rollback()

    def SetRun(self, event):
        self.editor.load(self.searchresults.GetItemData(event.Index))

    def update(self, observable, event, message=None):

        def update_runfinder():
            if self.finder is not None:
                first_selected = self.searchresults.GetFirstSelected()
                if first_selected < 0:
                    current_run = None
                else:
                    current_run = self.searchresults.GetItemData(
                        first_selected,
                    )
                self.searchresults.DeleteAllItems()
                results = self.finder.get_results()
                for row, run in enumerate(results):
                    index = self.searchresults.InsertItem(
                        sys.maxsize,
                        str(run[0]),
                    )
                    self.searchresults.SetItemData(index, run[0])
                    for col, v in enumerate(run[0:]):
                        self.searchresults.SetItem(index, col, str(v))
                    # activate if it's the current run
                    if run[0] == current_run:
                        self.searchresults.SetItemState(
                            index,
                            wx.LIST_STATE_SELECTED,
                            wx.LIST_STATE_SELECTED,
                        )

        try:
            busy = wx.BusyCursor()

            # Disable Event handling while updating
            self.SetEvtHandlerEnabled(False)

            if type(observable) == RunFinder:
                update_runfinder()

            elif type(observable) == RunEditor and event == 'run':
                self.UpdateRun()
                self.course.SetValue(self.editor.run_course)
                self.override.SetSelection(self.editor.run_override)
                self.readout_time.SetLabel(self.editor.run_readout_time)
                self.card_start_time.SetLabel(self.editor.run_card_start_time)
                self.card_finish_time.SetLabel(
                    self.editor.run_card_finish_time,
                )
                self.manual_start_time.SetValue(
                    self.editor.run_manual_start_time,
                )
                self.manual_finish_time.SetValue(
                    self.editor.run_manual_finish_time,
                )
                self.complete.SetValue(self.editor.run_complete)

                self.runner_number.SetValue(self.editor.runner_number)
                self.runner_category.SetValue(self.editor.runner_category)
                self.runner_given_name.SetValue(self.editor.runner_given_name)
                self.runner_surname.SetValue(self.editor.runner_surname)
                self.runner_dateofbirth.SetValue(
                    self.editor.runner_dateofbirth,
                )
                self.runner_team.SetValue(self.editor.runner_team)
                self.runner_club.SetValue(self.editor.runner_club)

                ctrl_list = (
                    self.run_runner_combo,
                    self.runner_number,
                    self.runner_category,
                    self.runner_given_name,
                    self.runner_surname,
                    self.runner_dateofbirth,
                    self.runner_team,
                    self.course,
                    self.manual_start_time,
                    self.manual_finish_time,
                    self.override,
                    self.complete,
                    self.punches_grid,
                )
                if not self.editor.has_run():
                    # Disable all controls if there is no run in the editor
                    for ctrl in ctrl_list:
                        ctrl.Disable()
                else:
                    for ctrl in ctrl_list:
                        ctrl.Enable()

                # also update the runfinder, names may have changed or a run
                # may have been deleted
                # TODO make this more conditional on when the results actually
                # change...
                update_runfinder()

                self.Layout()

            elif type(observable) == RunEditor and event == 'reader':
                if (
                    self.GetGrandParent().notebook.GetCurrentPage() == self
                    and self.registration.GetValue()
                    and observable.sicard is not None
                ):
                    observable.new_from_reader()
                    self.runner_number.SetFocus()

        finally:
            # Enable Event handling after updating
            self.SetEvtHandlerEnabled(True)

            # delete the busy cursor even if an exception occurs
            del busy

    @staticmethod
    def UpdateCombo(combo, choice, choice_list):
        combo.Clear()
        choice_index = 0
        for i, c in enumerate(choice_list):
            combo.Append(c[1], c[0])
            if c[0] == choice:
                choice_index = i
        combo.SetSelection(choice_index)

    def OnPrint(self, event):
        self.editor.print_run()

    def DeleteRun(self, event):
        self.editor.delete()


class ReadoutRunPanel(wxglade.ReadoutRunPanel):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.update(self.editor, 'progress')
        self.update(self.editor, 'run')

    def update(self, observable, event, message=None):

        try:
            busy = wx.BusyCursor()

            # Disable Event handling while updating
            self.SetEvtHandlerEnabled(False)

            if type(observable) == RunEditor and event == 'run':
                self.UpdateRun()

                self.runner_number.SetLabel(self.editor.runner_number)
                self.runner_category.SetLabel(self.editor.runner_category)
                self.runner_name.SetLabel(self.editor.runner_name)
                self.runner_team.SetLabel(self.editor.runner_team)

                self.start_time.SetLabel(self.editor.run_start_time[11:])
                self.finish_time.SetLabel(self.editor.run_finish_time[11:])
                self.course.SetLabel(self.editor.run_course)

                if not (self.editor.has_runner() and self.editor.has_course()):
                    # change to edit run page
                    if self.GetParent().GetPageCount() > 0:
                        self.GetParent().SetSelection(0)

            elif type(observable) == RunEditor and event == 'reader':
                if (
                    self.GetGrandParent().notebook.GetCurrentPage() == self
                    and observable.sicard is not None
                ):

                    try:
                        observable.load_run_from_card()
                    except (SIReaderException,
                            SIReaderTimeout,
                            SIReaderCardChanged) as msg:
                        self.GetGrandParent().ErrorDialog(
                            str(msg),
                            'Error communicating to the SI-Reader',
                        )
                    else:
                        if (
                            self.print_checkbox.GetValue()
                            and self.GetParent().GetCurrentPage() == self
                        ):
                            # the current page might change if the run is not
                            # complete
                            observable.print_run()

            elif type(observable) == RunEditor and event == 'progress':
                p = observable.progress
                self.progress_bar.SetValue(p[0])
                self.progress_text.SetLabel(p[1])
                wx.GetApp().Yield()

        finally:
            # Enable Event handling after updating
            self.SetEvtHandlerEnabled(True)

            # delete the busy cursor even if an exception occurs
            del busy


def ExceptionHook(etype, value, trace):
    """
    Handler for all unhandled exceptions.
    """
    message = ''.join(format_exception(etype, value, trace))
    frame = wx.GetApp().GetTopWindow()
    frame.ErrorDialog(message, 'Unhandled Exception')


class RunEditorFrame(wxglade.RunEditorFrame):
    """This is the main application window."""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Create a notebook to contain the application panels
        # This is done manually because it uses the child classes defined here.
        self.notebook = wx.Notebook(self, wx.ID_ANY, style=0)

        # Create notebook pages
        self.run_page = RunPanel(self.notebook, wx.ID_ANY)
        self.runner_page = RunnerPanel(self.notebook, wx.ID_ANY)
        self.team_page = TeamPanel(self.notebook, wx.ID_ANY)
        self.readout_run_page = ReadoutRunPanel(self.notebook, wx.ID_ANY)
        self.reports_page = ReportsPanel(self.notebook, wx.ID_ANY)

        self.notebook.AddPage(self.run_page, 'Run')
        self.notebook.AddPage(self.runner_page, 'Runner')
        self.notebook.AddPage(self.team_page, 'Team')
        self.notebook.AddPage(self.readout_run_page, 'Read SI-Card')
        self.notebook.AddPage(self.reports_page, 'Reports')
        notebook_sizer = wx.BoxSizer(wx.VERTICAL)
        notebook_sizer.Add(self.notebook, 1, wx.EXPAND, 0)
        self.SetSizer(notebook_sizer)
        self.Layout()

        # Connect RunEditor instance
        self.editor = RunEditor(conf.store, conf.event)
        self.editor.add_observer(self)
        self.update(self.editor, 'reader')

        # Add timer to periodically poll the si reader
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self._timer = wx.Timer(self)
        self._timer.Start(milliseconds=500, oneShot=False)
        self.Bind(wx.EVT_CLOSE, self.OnWindowClose)

    def __set_properties(self):

        super().__set_properties()

        self.SetIcon(sicard.GetIcon())

    def OnWindowClose(self, event):
        self._timer.Stop()
        del self._timer
        self.Destroy()

    def OnTimer(self, event):
        try:
            self.editor.poll_reader()
        except SIReaderException as msg:
            self.ErrorDialog(str(msg), 'Error communicating to the SI-Reader')

    def update(self, observable, event, message=None):

        if type(observable) == RunEditor and event == 'reader':
            self.statusbar.SetStatusText(observable.status, 0)
            self.statusbar.SetStatusText(observable.port, 1)
            wx.GetApp().Yield()
        elif event == 'error':
            self.ErrorDialog(str(message), 'Error')

    def Quit(self, event):
        self.Close(True)

    def ConnectReader(self, event):
        try:
            self.editor.connect_reader()
        except RunEditorException as e:
            self.ErrorDialog(str(e), 'Error Connecting SI-Reader')

    def ErrorDialog(self, msg, title):
        dlg = wx.MessageDialog(
            self,
            msg,
            title,
            wx.OK | wx.ICON_ERROR,
        )
        dlg.ShowModal()
        dlg.Destroy()

    def SetPrintCommand(self, event):
        dlg = wx.TextEntryDialog(
            self,
            'Command used to print:',
            'Print command',
        )
        dlg.SetValue(self.editor.print_command)
        answer = dlg.ShowModal()
        if answer == wx.ID_OK:
            self.editor.set_print_command(dlg.GetValue())
        dlg.Destroy()

    def OpenRuns(self, event):
        print('Event handler "OpenRuns" not implemented!')
        event.Skip()

    def OrphanRuns(self, event):
        print('Event handler "OrphanRuns" not implemented!')
        event.Skip()
