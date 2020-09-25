# = LICENSE HEADER ============================================================================= {{{
#
# (c) 2011, Marius Tomaschewski <mt@suse.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module implements a simple IP Match Filter.

@author: Marius Tomaschewski
@contact: mt@suse.de
"""


import netaddr.ip


class IPMatchFilter(object):
    """
    Simple IP Match filter with a list of allowed subnets with optional list of disallowed ranges
    or networks:

    Example:
        [(subnet, [range, ...]), ...)
    """

    def __init__(self, version=None):
        super(IPMatchFilter, self).__init__()

        if version is not None and version != 4 and version != 6:
            raise ValueError("Invalid IP Protocol version {}".format(version))
        self._ver = version
        self._ipf = []

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self._ipf)

    @property
    def version(self):
        """The IP Protocol version used by this instance."""
        return self._ver

    def empty(self):
        """Return true when the filter is empty, otherwise false."""
        return not self._ipf

    def add_subnet(self, subnet):
        """Add an allowed subnet to the filter."""
        sn = netaddr.ip.IPNetwork(subnet)
        if self.version is not None and sn.version != self.version:
            raise ValueError("IP Protocol version missmatch")

        for s in reversed(self._ipf):
            if sn == s[0]:
                return False
        self._ver = sn.version
        self._ipf.append((sn, []))
        return True

    def add_range(self, beg, end=None):
        """
        Add a range to matching subnet giving either its begin and end or also as network in
        begin.
        """
        if end is None:
            rn = netaddr.ip.IPNetwork(beg)
            if rn.version != self.version:
                raise ValueError("IP Protocol version missmatch")
            for s in reversed(self._ipf):
                if s[0].__contains__(rn):
                    s[1].append(rn)
                    return True
        else:
            b = netaddr.ip.IPAddress(beg)
            e = netaddr.ip.IPAddress(end)
            if b.version != self.version or e.version != self.version:
                raise ValueError("IP Protocol version missmatch")
            for s in reversed(self._ipf):
                if s[0].__contains__(b) and s[0].__contains__(e):
                    s[1].append(netaddr.ip.IPRange(b, e))
                    return True
        return False

    def match(self, ip):
        """
        Test if the IP address matches an allowed subnet but none of the disallowed ranges in it.
        """
        a = netaddr.ip.IPAddress(ip)
        if a.version != self.version:
            raise ValueError("IP Protocol version missmatch")
        for s in self._ipf:
            if s[0].__contains__(a):
                for r in s[1]:
                    if r.__contains__(a):
                        return False
                return True
        return False
