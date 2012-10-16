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

"""linked text files"""

from veusz.document.linked import LinkedFileBase

class LinkedFile2D(LinkedFileBase):
    """Class representing a file linked to a 2d dataset."""

    def createOperation(self):
        """Return operation to recreate self."""
        import operations
        return operations.OperationDataImport2D

    def saveToFile(self, fileobj, relpath=None):
        """Save the link to the document file."""

        args = [ repr(self._getSaveFilename(relpath)),
                 repr(self.params.datasetnames) ]
        for par in ("xrange", "yrange", "invertrows", "invertcols", "transpose",
                    "prefix", "suffix", "encoding"):
            v = getattr(self.params, par)
            if v is not None and v != "" and v != self.params.defaults[par]:
                args.append("%s=%s" % (par, repr(v)))
        args.append("linked=True")

        fileobj.write("ImportFile2D(%s)\n" % ", ".join(args))
