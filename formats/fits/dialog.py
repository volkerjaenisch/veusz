# standard data import dialog

#    Copyright (C) 2004 Jeremy S. Sanders
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
##############################################################################

"""Dialog box for FITS import."""

import os.path

from veusz.dialogs.importtab import ImportTab
import veusz.qtall as qt4
from veusz.dialogs.veuszdialog import VeuszDialog
from veusz import utils

from veusz.formats.fits import params
from veusz.formats.fits import operations
from veusz.formats.fits import reader

def _(text, disambiguation=None, context="ImportDialog"):
    """Translate text."""
    return unicode(
        qt4.QCoreApplication.translate(context, text, disambiguation))

pyfits = None
class ImportTabFITS(ImportTab):
    """Tab for importing from a FITS file."""

    resource = 'dialog.ui'

    def loadUi(self):
        #TODO: Find better solution for importing the resource file
        qt4.loadUi(os.path.join(utils.veuszDirectory, 'formats', 'hdf5',
                                self.resource), self)
        self.uiloaded = True

        # if different items are selected in fits tab
        self.connect(self.fitshdulist, qt4.SIGNAL('itemSelectionChanged()'),
                      self.slotFitsUpdateCombos)
        self.connect(self.fitsdatasetname,
                      qt4.SIGNAL('editTextChanged(const QString&)'),
                      self.dialog.enableDisableImport)
        self.connect(self.fitsdatacolumn,
                      qt4.SIGNAL('currentIndexChanged(int)'),
                      self.dialog.enableDisableImport)

    def reset(self):
        """Reset controls."""
        self.fitsdatasetname.setEditText("")
        for c in ('data', 'sym', 'pos', 'neg'):
            cntrl = getattr(self, 'fits%scolumn' % c)
            cntrl.setCurrentIndex(0)

    def doPreview(self, filename, encoding):
        """Set up controls for FITS file."""

        # load pyfits if available
        global pyfits
        if pyfits is None:
            try:
                import pyfits as PF
                pyfits = PF
            except ImportError:
                pyfits = None

        # if it isn't
        if pyfits is None:
            self.fitslabel.setText(
                _('FITS file support requires that PyFITS is installed.'
                  ' You can download it from'
                  ' http://www.stsci.edu/resources/software_hardware/pyfits'))
            return False

        # try to identify fits file
        try:
            ifile = open(filename, 'rU')
            line = ifile.readline()
            # is this a hack?
            if line.find('SIMPLE  =                    T') == -1:
                raise EnvironmentError
            ifile.close()
        except EnvironmentError:
            self.clearFITSView()
            return False

        self.updateFITSView(filename)
        return True

    def clearFITSView(self):
        """If invalid filename, clear fits preview."""
        self.fitshdulist.clear()
        for c in ('data', 'sym', 'pos', 'neg'):
            cntrl = getattr(self, 'fits%scolumn' % c)
            cntrl.clear()
            cntrl.setEnabled(False)

    def updateFITSView(self, filename):
        """Update the fits file details in the import dialog."""
        f = pyfits.open(str(filename), 'readonly')
        l = self.fitshdulist
        l.clear()

        # this is so we can lookup item attributes later
        self.fitsitemdata = []
        items = []
        for hdunum, hdu in enumerate(f):
            header = hdu.header
            hduitem = qt4.QTreeWidgetItem([str(hdunum), hdu.name])
            data = []
            try:
                # if this fails, show an image
                cols = hdu.get_coldefs()

                # it's a table
                data = ['table', cols]
                rows = header['NAXIS2']
                descr = _('Table (%i rows)') % rows

            except AttributeError:
                # this is an image
                naxis = header['NAXIS']
                if naxis == 1 or naxis == 2:
                    data = ['image']
                else:
                    data = ['invalidimage']
                dims = [ str(header['NAXIS%i' % (i + 1)])
                         for i in xrange(naxis) ]
                dims = '*'.join(dims)
                if dims:
                    dims = '(%s)' % dims
                descr = _('%iD image %s') % (naxis, dims)

            hduitem = qt4.QTreeWidgetItem([str(hdunum), hdu.name, descr])
            items.append(hduitem)
            self.fitsitemdata.append(data)

        if items:
            l.addTopLevelItems(items)
            l.setCurrentItem(items[0])

    def slotFitsUpdateCombos(self):
        """Update list of fits columns when new item is selected."""

        items = self.fitshdulist.selectedItems()
        if len(items) != 0:
            item = items[0]
            hdunum = int(str(item.text(0)))
        else:
            item = None
            hdunum = -1

        cols = ['N/A']
        enablecolumns = False
        if hdunum >= 0:
            data = self.fitsitemdata[hdunum]
            if data[0] == 'table':
                enablecolumns = True
                cols = ['None']
                cols += ['%s (%s)' %
                         (i.name, i.format) for i in data[1]]

        for c in ('data', 'sym', 'pos', 'neg'):
            cntrl = getattr(self, 'fits%scolumn' % c)
            cntrl.setEnabled(enablecolumns)
            cntrl.clear()
            cntrl.addItems(cols)

        self.dialog.enableDisableImport()

    def okToImport(self):
        """Check validity of Fits import."""

        items = self.fitshdulist.selectedItems()
        if len(items) != 0:
            item = items[0]
            hdunum = int(str(item.text(0)))

            # any name for the dataset?
            if not unicode(self.fitsdatasetname.text()):
                return False

            # if a table, need selected item
            data = self.fitsitemdata[hdunum]
            if data[0] != 'image' and self.fitsdatacolumn.currentIndex() == 0:
                return False

            return True
        return False

    def doImport(self, doc, filename, linked, encoding, prefix, suffix, tags):
        """Import fits file."""

        item = self.fitshdulist.selectedItems()[0]
        hdunum = int(str(item.text(0)))
        data = self.fitsitemdata[hdunum]

        name = prefix + unicode(self.fitsdatasetname.text()) + suffix

        if data[0] == 'table':
            # get list of appropriate columns
            cols = []

            # get data from controls
            for c in ('data', 'sym', 'pos', 'neg'):
                cntrl = getattr(self, 'fits%scolumn' % c)

                i = cntrl.currentIndex()
                if i == 0:
                    cols.append(None)
                else:
                    cols.append(data[1][i - 1].name)

        else:
            # item is an image, so no columns
            cols = [None] * 4

        # construct operation to import fits
        parameters = params.ImportParamsFITS(
            dsname=name,
            filename=filename,
            hdu=hdunum,
            datacol=cols[0],
            symerrcol=cols[1],
            poserrcol=cols[2],
            negerrcol=cols[3],
            tags=tags,
            linked=linked,
            )

        op = operations.OperationDataImportFITS(parameters)

        # actually do the import
        doc.applyOperation(op)

        # inform user
        self.fitsimportstatus.setText(_("Imported dataset '%s'") % name)
        qt4.QTimer.singleShot(2000, self.fitsimportstatus.clear)

    def isFiletypeSupported(self, ftype):
        """Is the filetype supported by this tab?"""
        return ftype in ('.fit', '.fits')


