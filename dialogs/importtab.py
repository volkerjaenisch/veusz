import os.path

import veusz.qtall as qt4

import veusz.utils as utils

class ImportTab(qt4.QWidget):
    """Tab for a particular import type."""

    resource = ''

    def __init__(self, importdialog, *args):
        """Initialise dialog. importdialog is the import dialog itself."""
        qt4.QWidget.__init__(self, *args)
        self.dialog = importdialog
        self.uiloaded = False

    def loadUi(self):
        """Load up UI file."""
        qt4.loadUi(os.path.join(utils.veuszDirectory, 'dialogs',
                                self.resource), self)
        self.uiloaded = True

    def reset(self):
        """Reset controls to initial conditions."""
        pass

    def doPreview(self, filename, encoding):
        """Update the preview window, returning whether import
        should be attempted."""
        pass

    def doImport(self, filename, linked, encoding, prefix, suffix, tags):
        """Do the import iteself."""
        pass

    def okToImport(self):
        """Secondary check (after preview) for enabling import button."""
        return True

    def isFiletypeSupported(self, ftype):
        """Is the filetype supported by this tab?"""
        return False

    def useFiletype(self, ftype):
        """If the tab can do something with the selected filetype,
        update itself."""
        pass



