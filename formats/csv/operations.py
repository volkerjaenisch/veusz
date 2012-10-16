#    Copyright (C) 2006 Jeremy S. Sanders
#    Email: Jeremy Sanders <jeremy@jeremysanders.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
###############################################################################

"""Operations for text file import"""

import veusz.qtall as qt4
from veusz.document.operations import OperationDataImportBase
from veusz.document import simpleread

import reader
from veusz import utils
import linked

def _(text, disambiguation=None, context="Operations"):
    """Translate text."""
    return unicode(
        qt4.QCoreApplication.translate(context, text, disambiguation))


class OperationDataImportCSV(OperationDataImportBase):
    """Import data from a CSV file."""

    descr = _('import CSV data')

    def doImport(self, document):
        """Do the data import."""

        csvr = reader.ReadCSV(self.params)
        csvr.readData()

        LF = None
        if self.params.linked:
            LF = linked.LinkedFileCSV(self.params)

        # set the data
        self.outdatasets = csvr.setData(document, linkedfile=LF)
