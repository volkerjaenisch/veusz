# -*- coding: utf-8 -*-
#    Copyright (C) 2011 Jeremy S. Sanders
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

"""linked FITS files"""

from veusz.document.linked import LinkedFileBase

class LinkedFileFITS(LinkedFileBase):
    """Links a FITS file to the data."""

    def createOperation(self):
        """Return operation to recreate self."""
        import operations
        return operations.OperationDataImportFITS

    def saveToFile(self, fileobj, relpath=None):
        """Save the link to the document file."""

        p = self.params
        args = [p.dsname, self._getSaveFilename(relpath), p.hdu]
        args = [repr(i) for i in args]
        for param, column in (("datacol", p.datacol),
                               ("symerrcol", p.symerrcol),
                               ("poserrcol", p.poserrcol),
                               ("negerrcol", p.negerrcol)):
            if column is not None:
                args.append("%s=%s" % (param, repr(column)))
        args.append("linked=True")

        fileobj.write("ImportFITSFile(%s)\n" % ", ".join(args))

