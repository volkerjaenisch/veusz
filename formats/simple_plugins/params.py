# params for standard data import dialog

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

"""params for simple_plugin data import dialog."""

from veusz.document.importparams import ImportParamsBase

class ImportParamsPlugin(ImportParamsBase):
    """Parameters for import plugins.

    Additional parameter:
     plugin: name of plugin

    Plugins have their own parameters."""

    defaults = {
        'plugin': None,
        }
    defaults.update(ImportParamsBase.defaults)

    def __init__(self, **argsv):
        """Initialise plugin parameters, splitting up default parameters
        and plugin parameters."""

        pluginpars = {}
        upvars = {}
        for n, v in argsv.iteritems():
            if n in self.defaults:
                upvars[n] = v
            else:
                pluginpars[n] = v

        ImportParamsBase.__init__(self, **upvars)
        self.pluginpars = pluginpars
        self._extras.append('pluginpars')
