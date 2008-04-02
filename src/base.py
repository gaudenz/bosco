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
base.py - Base classes
"""

from storm.locals import *

class MyStorm(Storm):
    """
    @todo: Find a better name for this class.
    """

    def _get_store(self):
        store = Store.of(self)
        if store is None:
            raise NoStoreError('Operation not possible without a store.')
        return store

    def _set_store(self, store):
        store.add(self)
        
    _store = property(_get_store, _set_store)


