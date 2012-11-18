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

"""Operations for FITS file import"""

import veusz.qtall as qt4
from veusz.document import datasets
from veusz.document.operations import OperationDataImportBase
from veusz.document import simpleread
from veusz import utils

from veusz.formats.fits import linked
from veusz.formats.fits import reader


def _(text, disambiguation=None, context="Operations"):
    """Translate text."""
    return unicode(
        qt4.QCoreApplication.translate(context, text, disambiguation))


class OperationDataImportHDF5(OperationDataImportBase):
    """Import data from a hdf5 file."""

    descr = _('import HDF5 file')

    def doImport(self, document):
        """Do the import."""

        try:
            import tables
        except ImportError:
            raise RuntimeError, ('PyTables is required to import '
                                  'data from hdf5 files')

        p = self.params

        self.hdf5_file = openFile(p.filename, 'r')
        table = self.hdf5_file.getNode(p.hdf5_path)
        col_names = table.description._v_names

        if p.linked:
            ds.linked = linked.LinkedFileHDF5(self.params)
        if p.dsname in document.data:
            self.olddataset = document.data[p.dsname]
        else:
            self.olddataset = None
        document.setData(p.dsname, ds)
        self.outdatasets.append(p.dsname)

