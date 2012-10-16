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

"""Operations for 2d file import"""

import veusz.qtall as qt4
from veusz.document.operations import OperationDataImportBase
from veusz.document import simpleread
from veusz import utils

from veusz.formats.data2d import linked
from veusz.formats.data2d import reader

def _(text, disambiguation=None, context="Operations"):
    """Translate text."""
    return unicode(
        qt4.QCoreApplication.translate(context, text, disambiguation))

class OperationDataImport2D(OperationDataImportBase):
    """Import a 2D matrix from a file."""

    descr = _('import 2d data')

    def doImport(self, document):
        """Import data."""

        p = self.params

        # get stream
        if p.filename is not None:
            stream = simpleread.FileStream(
                utils.openEncoding(p.filename, p.encoding))
        elif p.datastr is not None:
            stream = simpleread.StringStream(p.datastr)
        else:
            assert False

        # linked file
        LF = None
        if p.linked:
            assert p.filename
            LF = linked.LinkedFile2D(p)

        for name in p.datasetnames:
            sr = reader.SimpleRead2D(name, p)
            sr.readData(stream)
            self.outdatasets += sr.setInDocument(document, linkedfile=LF)
