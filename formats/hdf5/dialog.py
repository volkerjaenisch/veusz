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
import tables

from veusz.dialogs.importtab import ImportTab
import veusz.qtall as qt4
from veusz.dialogs.veuszdialog import VeuszDialog
from veusz import utils

from veusz.formats.hdf5 import params
from veusz.formats.hdf5 import operations
from veusz.formats.hdf5 import reader

def _(text, disambiguation=None, context="ImportDialog"):
    """Translate text."""
    return unicode(
        qt4.QCoreApplication.translate(context, text, disambiguation))

class ImportTabHDF5(ImportTab):
    """For importing data from CSV files."""

    resource = 'dialog.ui'

    def loadUi(self):
        """Load user interface and setup panel."""
        #TODO: Find better solution for importing the resource file
        qt4.loadUi(os.path.join(utils.veuszDirectory, 'formats', 'hdf5',
                                self.resource), self)
        self.uiloaded = True

        self.connect(self.hdf5helpbutton, qt4.SIGNAL('clicked()'),
                      self.slotHelp)
        self.connect(self.hdf5delimitercombo,
                      qt4.SIGNAL('editTextChanged(const QString&)'),
                      self.dialog.slotUpdatePreview)
        self.connect(self.hdf5textdelimitercombo,
                      qt4.SIGNAL('editTextChanged(const QString&)'),
                      self.dialog.slotUpdatePreview)
        self.hdf5delimitercombo.default = [
            ',', '{tab}', '{space}', '|', ':', ';']
        self.hdf5textdelimitercombo.default = ['"', "'"]
        self.hdf5datefmtcombo.default = [
            'YYYY-MM-DD|T|hh:mm:ss',
            'DD/MM/YY| |hh:mm:ss',
            'M/D/YY| |hh:mm:ss'
            ]
        self.hdf5numfmtcombo.defaultlist = [_('System'), _('English'), _('European')]
        self.hdf5headermodecombo.defaultlist = [_('Multiple'), _('1st row'), _('None')]

    def reset(self):
        """Reset controls."""
        self.hdf5delimitercombo.setEditText(",")
        self.hdf5textdelimitercombo.setEditText('"')
        self.hdf5directioncombo.setCurrentIndex(0)
        self.hdf5ignorehdrspin.setValue(0)
        self.hdf5ignoretopspin.setValue(0)
        self.hdf5blanksdatacheck.setChecked(False)
        self.hdf5numfmtcombo.setCurrentIndex(0)
        self.hdf5datefmtcombo.setEditText(
            params.ImportParamsHDF5.defaults['dateformat'])
        self.hdf5headermodecombo.setCurrentIndex(0)

    def slotHelp(self):
        """Asked for help."""
        d = VeuszDialog(self.dialog.mainwindow, 'importhelphdf5.ui')
        self.dialog.mainwindow.showDialog(d)

    def getCSVDelimiter(self):
        """Get CSV delimiter, converting friendly names."""
        delim = str(self.hdf5delimitercombo.text())
        if delim == '{space}':
            delim = ' '
        elif delim == '{tab}':
            delim = '\t'
        return delim

    def clearView(self):
        """If invalid filename, clear preview."""
        return

#def _recurse_hdf5_nodes( hdf_file, tree_position):                                                                                                                                                                                                 
#        """recurses the hdf5 tree recursivly and generate a QT Treeview"""                                                                                                                                                                         
#        for group in hdf_file.listNodes(tree_position, classname="Group"):                                                                                                                                                                         
#            print group._v_name                                                                                                                                                                                                                    
#            # parent_item.appendRow(item)                                                                                                                                                                                                          
#            _show_tables( hdf_file, group._v_pathname )                                                                                                                                                                                            
#            _recurse_hdf5_nodes(hdf_file, group._v_pathname )                                                                                                                                                                                      

    def _show_tables(self, hdf_file, tree_position, parent_item):
        for table in hdf_file.listNodes(tree_position):
            item = qt4.QStandardItem(qt4.QString("%0").arg(table._v_name))
            parent_item.appendRow(item)

    def _recurse_hdf5_nodes(self, hdf_file, tree_position, parent_item):
        """recurses the hdf5 tree recursivly and generate a QT Treeview"""
        for group in hdf_file.listNodes(tree_position, classname='Group'):
            item = qt4.QStandardItem(qt4.QString("%0").arg(group._v_name))
            parent_item.appendRow(item)
            self._show_tables(hdf_file, group._v_pathname, item)



    def doPreview(self, filename, encoding):
        """preview - show HDF structure"""

        self.model = qt4.QStandardItemModel()

        tree = self.previewtreehdf5

        try :
            hdf5_file = tables.openFile(filename)
        except :
            self.clearView()
            return False

        rootItem = self.model.invisibleRootItem()
        self._recurse_hdf5_nodes(hdf5_file, "/", rootItem)

        self.previewtreehdf5.setModel(self.model)
#        self.previewtreehdf5.setDragDropMode(qt4.QAbstractItemView.InternalMove)

        return True

    def doImport(self, doc, filename, linked, encoding, prefix, suffix, tags):
        """Import from HDF5 file."""

        # get various values
        inrows = self.hdf5directioncombo.currentIndex() == 1

        try:
            delimiter = self.getCSVDelimiter()
            textdelimiter = str(self.hdf5textdelimitercombo.currentText())
        except UnicodeEncodeError:
            return

        numericlocale = (str(qt4.QLocale().name()),
                          'en_US',
                          'de_DE')[self.hdf5numfmtcombo.currentIndex()]
        headerignore = self.hdf5ignorehdrspin.value()
        rowsignore = self.hdf5ignoretopspin.value()
        blanksaredata = self.hdf5blanksdatacheck.isChecked()
        dateformat = unicode(self.hdf5datefmtcombo.currentText())
        headermode = ('multi', '1st', 'none')[
            self.hdf5headermodecombo.currentIndex()]

        # create import parameters and operation objects
        parameters = params.ImportParamsHDF5(
            filename=filename,
            readrows=inrows,
            encoding=encoding,
            delimiter=delimiter,
            textdelimiter=textdelimiter,
            headerignore=headerignore,
            rowsignore=rowsignore,
            blanksaredata=blanksaredata,
            numericlocale=numericlocale,
            dateformat=dateformat,
            headermode=headermode,
            prefix=prefix, suffix=suffix,
            tags=tags,
            linked=linked,
            )
        op = operations.OperationDataImportHDF5(parameters)

        # actually import the data
        doc.applyOperation(op)

        # update output, showing what datasets were imported
        lines = self.dialog.retnDatasetInfo(op.outdatasets, linked, filename)

        t = self.previewtablehdf5
        t.verticalHeader().hide()
        t.horizontalHeader().hide()
        t.horizontalHeader().setStretchLastSection(True)

        t.clear()
        t.setColumnCount(1)
        t.setRowCount(len(lines))
        for i, l in enumerate(lines):
            item = qt4.QTableWidgetItem(l)
            t.setItem(i, 0, item)

    def isFiletypeSupported(self, ftype):
        """Is the filetype supported by this tab?"""
        return ftype in ('.tsv', '.hdf5')
