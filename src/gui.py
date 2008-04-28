#
#    Copyright (C) 2008  Gaudenz Steinlin <gaudenz@soziologie.ch>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
gui.py - classes for the graphical user interface. This is not an actual GUI
         application but a collection of helper classes
"""

import wx
import wx.html

class UpdateableHtmlPanel(wx.html.HtmlWindow):
    """Panel to display HTML content. This panel updates it's content on
    calls to update(event). UpdateHtmlPanels are typically used to show rankings and
    connected to an EventObserver to automatically update.
    """

    def __init__(self, parent, content = None):
        super(type(self), self).__init__(parent)

        self._content = content

        # bug? call this for acceptable fonts
        self.SetStandardFonts()
        self.update(None)

    def update(self, event):
        """Update the content of the panel."""
        if self._content is not None:
            self.SetPage(unicode(self._content))
        else:
            self.SetPage('')

    def _set_content(self, content):
        self._content = content
        self.update(None)

    def _get_content(self):
        return self._content

    content = property(_get_content, _set_content)

