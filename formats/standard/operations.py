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
import reader
from veusz import utils
import linked

def _(text, disambiguation=None, context="Operations"):
    """Translate text."""
    return unicode(
        qt4.QCoreApplication.translate(context, text, disambiguation))

class OperationDataImport(OperationDataImportBase):
    """Import 1D data from text files."""

    descr = _('import data')

    def __init__(self, params):
        """Setup operation.
        """

        OperationDataImportBase.__init__(self, params)
        self.simpleread = reader.SimpleRead(params.descriptor)

    def doImport(self, document):
        """Import data.
        
        Returns a list of datasets which were imported.
        """

        p = self.params
        # open stream to import data from
        if p.filename is not None:
            stream = reader.FileStream(
                utils.openEncoding(p.filename, p.encoding))
        elif p.datastr is not None:
            stream = reader.StringStream(p.datastr)
        else:
            raise RuntimeError, "No filename or string"

        # do the import
        self.simpleread.clearState()
        self.simpleread.readData(stream, useblocks=p.useblocks,
                                 ignoretext=p.ignoretext)

        # associate linked file
        LF = None
        if p.linked:
            assert p.filename
            LF = linked.LinkedFile(p)

        # actually set the data in the document
        self.outdatasets = self.simpleread.setInDocument(
            document, linkedfile=LF, prefix=p.prefix, suffix=p.suffix)
        self.outinvalids = self.simpleread.getInvalidConversions()
