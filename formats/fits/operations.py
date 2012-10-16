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


class OperationDataImportFITS(OperationDataImportBase):
    """Import 1d or 2d data from a fits file."""

    descr = _('import FITS file')

    def _import1d(self, hdu):
        """Import 1d data from hdu."""

        data = hdu.data
        datav = None
        symv = None
        posv = None
        negv = None

        # read the columns required
        p = self.params
        if p.datacol is not None:
            datav = data.field(p.datacol)
        if p.symerrcol is not None:
            symv = data.field(p.symerrcol)
        if p.poserrcol is not None:
            posv = data.field(p.poserrcol)
        if p.negerrcol is not None:
            negv = data.field(p.negerrcol)

        # actually create the dataset
        return datasets.Dataset(data=datav, serr=symv, perr=posv, nerr=negv)

    def _import1dimage(self, hdu):
        """Import 1d image data form hdu."""
        return datasets.Dataset(data=hdu.data)

    def _import2dimage(self, hdu):
        """Import 2d image data from hdu."""

        p = self.params
        if (p.datacol is not None or p.symerrcol is not None
             or p.poserrcol is not None
             or p.negerrcol is not None):
            print "Warning: ignoring columns as import 2D dataset"

        header = hdu.header
        data = hdu.data

        try:
            # try to read WCS for image, and work out x/yrange
            wcs = [header[i] for i in ('CRVAL1', 'CRPIX1', 'CDELT1',
                                       'CRVAL2', 'CRPIX2', 'CDELT2')]

            rangex = ((data.shape[1] - wcs[1]) * wcs[2] + wcs[0],
                       (0 - wcs[1]) * wcs[2] + wcs[0])
            rangey = ((0 - wcs[4]) * wcs[5] + wcs[3],
                       (data.shape[0] - wcs[4]) * wcs[5] + wcs[3])

            rangex = (rangex[1], rangex[0])

        except KeyError:
            # no / broken wcs
            rangex = None
            rangey = None

        return datasets.Dataset2D(data, xrange=rangex, yrange=rangey)

    def doImport(self, document):
        """Do the import."""

        try:
            import pyfits
        except ImportError:
            raise RuntimeError, ('PyFITS is required to import '
                                  'data from FITS files')

        p = self.params
        f = pyfits.open(str(p.filename), 'readonly')
        hdu = f[p.hdu]

        try:
            # raise an exception if this isn't a table therefore is an image
            hdu.get_coldefs()
            ds = self._import1d(hdu)

        except AttributeError:
            naxis = hdu.header.get('NAXIS')
            if naxis == 1:
                ds = self._import1dimage(hdu)
            elif naxis == 2:
                ds = self._import2dimage(hdu)
            else:
                raise RuntimeError, "Cannot import images with %i dimensions" % naxis
        f.close()

        if p.linked:
            ds.linked = linked.LinkedFileFITS(self.params)
        if p.dsname in document.data:
            self.olddataset = document.data[p.dsname]
        else:
            self.olddataset = None
        document.setData(p.dsname, ds)
        self.outdatasets.append(p.dsname)

