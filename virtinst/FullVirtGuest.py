#
# Fullly virtualized guest support
#
# Copyright 2006-2007  Red Hat, Inc.
# Jeremy Katz <katzj@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free  Software Foundation; either version 2 of the License, or
# (at your option)  any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301 USA.

import _util
import DistroInstaller

from Guest import Guest
from VirtualDevice import VirtualDevice
from VirtualInputDevice import VirtualInputDevice

class FullVirtGuest(Guest):

    def __init__(self, type=None, arch=None, connection=None,
                 hypervisorURI=None, emulator=None, installer=None):
        if not installer:
            installer = DistroInstaller.DistroInstaller(type = type,
                                                        os_type = "hvm",
                                                        conn=connection)
        Guest.__init__(self, type, connection, hypervisorURI, installer)

        self.disknode = "hd"
        self._diskbus = "ide"

        self.features = { "acpi": None, "pae":
            _util.is_pae_capable(self.conn), "apic": None }

        self.emulator = emulator
        if arch:
            self.arch = arch

        self.loader = None
        guest = self._caps.guestForOSType(type=self.installer.os_type,
                                          arch=self.arch)
        if (not self.emulator) and guest:
            for dom in guest.domains:
                if dom.hypervisor_type == self.installer.type:
                    self.emulator = dom.emulator
                    self.loader = dom.loader

        # Fall back to default hardcoding
        if self.emulator is None:
            if self.type == "xen":
                if self._caps.host.arch in ("x86_64"):
                    self.emulator = "/usr/lib64/xen/bin/qemu-dm"
                else:
                    self.emulator = "/usr/lib/xen/bin/qemu-dm"

        if (not self.loader) and self.type == "xen":
            self.loader = "/usr/lib/xen/boot/hvmloader"


    def os_features(self):
        """Determine the guest features, based on explicit settings in FEATURES
        and the OS_TYPE and OS_VARIANT. FEATURES takes precedence over the OS
        preferences"""
        if self.features is None:
            return None

        # explicitly disabling apic and acpi will override OS_TYPES values
        features = dict(self.features)
        for f in ["acpi", "apic"]:
            val = self._lookup_osdict_key(f)
            features[f] = val
        return features

    def _get_input_device(self):
        typ = self._lookup_device_param("input", "type")
        bus = self._lookup_device_param("input", "bus")
        dev = VirtualInputDevice(self.conn)
        dev.type = typ
        dev.bus = bus
        return dev

    def _get_features_xml(self):
        ret = "  <features>\n"
        features = self.os_features()
        if features:
            ret += "    "
            for k in sorted(features.keys()):
                v = features[k]
                if v:
                    ret += "<%s/>" %(k,)
            ret += "\n"
        return ret + "  </features>"

    def _get_clock_xml(self):
        val = self._lookup_osdict_key("clock")
        return """  <clock offset="%s"/>""" % val

    def _get_device_xml(self, install=True):
        emu_xml = ""
        if self.emulator is not None:
            emu_xml = "    <emulator>%s</emulator>\n" % self.emulator

        return (emu_xml +
                """    <console type='pty'/>\n""" +
                Guest._get_device_xml(self, install))

    def _set_defaults(self):
        disk_bus  = self._lookup_device_param("disk", "bus")
        net_model = self._lookup_device_param("net", "model")

        # Only overwrite params if they weren't already specified
        for net in self._get_install_devs(VirtualDevice.VIRTUAL_DEV_NET):
            if net_model and not net.model:
                net.model = net_model
        for disk in self._get_install_devs(VirtualDevice.VIRTUAL_DEV_DISK):
            if disk_bus and not disk.bus:
                disk.bus = disk_bus

        # Run this last, so we get first crack at disk attributes
        Guest._set_defaults(self)
