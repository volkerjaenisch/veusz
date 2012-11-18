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
#import tables

from PyQt4.QtCore import Qt

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

class NodeData(object):
    """
    Lightweight class for storing information on hdf5 nodes in treeview items
    """
    def __init__(self, path, isTable=False):
        self.isTable = isTable
        self.path = path

class ImportTabHDF5(ImportTab):
    """For importing data from CSV files."""

    resource = 'dialog.ui'

    def loadUi(self):
        """Load user interface and setup panel."""
        self.filename = None
        self.encoding = None
        #TODO: Find better solution for importing the resource file
        qt4.loadUi(os.path.join(utils.veuszDirectory, 'formats', 'hdf5',
                                self.resource), self)
        self.uiloaded = True

        self.connect(self.hdf5helpbutton, qt4.SIGNAL('clicked()'),
                      self.slotHelp)
        self.connect(self.hdf5previewtree,
                      qt4.SIGNAL('clicked ( const QModelIndex& )'),
                      self.updatePreviewTable)

        self.hdf5datefmtcombo.default = [
            'YYYY-MM-DD|T|hh:mm:ss',
            'DD/MM/YY| |hh:mm:ss',
            'M/D/YY| |hh:mm:ss'
            ]
        self.hdf5numfmtcombo.defaultlist = [_('System'), _('English'), _('European')]

    def reset(self):
        """Reset controls."""
        self.hdf5datefmtcombo.setEditText(
            params.ImportParamsHDF5.defaults['dateformat'])

    def slotHelp(self):
        """Asked for help."""
        d = VeuszDialog(self.dialog.mainwindow, 'importhelphdf5.ui', path='formats/hdf5')
        self.dialog.mainwindow.showDialog(d)

    def clearView(self):
        """If invalid filename, clear preview."""
        return

    def updatePreviewTable(self, index):
        """
        Handler for click into the treeview
        """
        # retrieve the NodeData object
        node_data = index.data(Qt.UserRole).toPyObject()
        # return if we are not on a table node 
        if not node_data.isTable :
            return
        self.hdf5_path = node_data.path
        self.drawPreviewTable()

    def drawPreviewTable(self):

        t = self.hdf5previewtable
        t.verticalHeader().show() # restore from a previous import
        t.horizontalHeader().show()
        t.horizontalHeader().setStretchLastSection(False)
#        t.clear()
        t.setColumnCount(0)
        t.setRowCount(0)

        table = self.hdf5_file.getNode(self.hdf5_path)
        col_names = table.description._v_names
        numcols = len(col_names)
        numrows = min(100, table.nrows)
        t.setColumnCount(numcols)
        t.setRowCount(numrows + 1)

        # set the header
        headers = qt4.QStringList()
        for col_name in col_names:
            headers.append(qt4.QString(col_name))

        t.setHorizontalHeaderLabels(headers)

        # fill up table
        row_nr = 0
        for row in table.read(start=0, stop=numrows):
            col_nr = 0
            for col_name in col_names:
                item = qt4.QTableWidgetItem(unicode(row[col_name]))
                t.setItem(row_nr, col_nr, item)
                col_nr += 1
            row_nr += 1

        t.resizeColumnsToContents()

    def _recurse_hdf5_nodes(self, tree_position, parent_item):
        """recurses the hdf5 tree recursivly and generate a QT Treeview"""
        # fetch current node in hdf5 file
        node = self.hdf5_file.getNode(tree_position)
        # iterate over the subgrous
        for group_name in node._v_groups:
            # generate display text for tree item
            item = qt4.QStandardItem(qt4.QString("%0").arg(group_name))
            # store the nodes path as user data into the tree item
            item.setData(NodeData(node._v_pathname + group_name), Qt.UserRole)
            # append tree item under the current parent item
            parent_item.appendRow(item)
            # recursion
            self._recurse_hdf5_nodes(node._v_pathname + group_name + "/", item)

        # generate nodes for the tables
        for table_name in node._v_leaves:
            # generate display text for tree item
            item = qt4.QStandardItem(qt4.QString("%0").arg(table_name))
            # store the nodes path as user data into the tree item
            item.setData(NodeData(node._v_pathname + table_name, isTable=True), Qt.UserRole)
            # append tree item under the current parent item            
            parent_item.appendRow(item)

    def doPreview(self, filename, encoding):
        """preview - show HDF structure"""

        try:
            import tables
        except ImportError:
            raise RuntimeError, ('PyTables is required to import '
                                  'data from hdf5 files')

        if self.filename and self.encoding :
            if self.filename == filename and self.encoding == encoding:
                return True
        self.filename = filename
        self.encoding = encoding
        self.model = qt4.QStandardItemModel()

        try :
            self.hdf5_file = tables.openFile(filename)
        except :
            self.clearView()
            return False

        rootItem = self.model.invisibleRootItem()
        self._recurse_hdf5_nodes("/", rootItem)

        self.hdf5previewtree.setModel(self.model)

        return True

    def doImport(self, doc, filename, linked, encoding, prefix, suffix, tags):
        """Import from HDF5 file."""

        dateformat = unicode(self.hdf5datefmtcombo.currentText())

        # create import parameters and operation objects
        parameters = params.ImportParamsHDF5(
            filename=filename,
            encoding=encoding,
            dateformat=dateformat,
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
        return ftype in ('.h5', '.hdf5')
