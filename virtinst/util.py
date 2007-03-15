#!/usr/bin/python -tt
#
# Utility functions used for guest installation
#
# Copyright 2006  Red Hat, Inc.
# Jeremy Katz <katzj@redhat.com>
#
# This software may be freely redistributed under the terms of the GNU
# general public license.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import random
import os.path
from sys import stderr

def default_bridge():
    route_file = "/proc/net/route"
    d = file(route_file)

    defn = 0
    for line in d.xreadlines():
        info = line.split()
        if (len(info) != 11): # 11 = typlical num of fields in the file
            print >> stderr, "Invalid line lenght while parsing %s."%(route_file)
            print >> stderr, " Defaulting bridge to xenbr%d"%(defn)
            break
        try:
            route = int(info[1],16)
            if route == 0:
                defn = int(info[0][-1])
                break 
        except ValueError:
            continue

    return "xenbr%d"%(defn)

def get_cpu_flags():
    f = open("/proc/cpuinfo")
    lines = f.readlines()
    f.close()
    for line in lines:
        if not line.startswith("flags"):
            continue
        # get the actual flags
        flags = line[:-1].split(":", 1)[1]
        # and split them
        flst = flags.split(" ")
        return flst
    return []

def is_pae_capable():
    """Determine if a machine is PAE capable or not."""
    flags = get_cpu_flags()
    if "pae" in flags:
        return True
    return False

def is_hvm_capable():
    """Determine if a machine is HVM capable or not."""

    caps = ""
    if os.path.exists("/sys/hypervisor/properties/capabilities"):
        caps = open("/sys/hypervisor/properties/capabilities").read()
    if caps.find("hvm") != -1:
        return True
    return False

def is_kqemu_capable():
    return os.path.exists("/dev/kqemu")

def is_kvm_capable():
    return os.path.exists("/dev/kvm")

def is_blktap_capable():
    #return os.path.exists("/dev/xen/blktapctrl")
    f = open("/proc/modules")
    lines = f.readlines()
    f.close()
    for line in lines:
        if line.startswith("blktap "):
            return True
    return False


# this function is directly from xend/server/netif.py and is thus
# available under the LGPL,
# Copyright 2004, 2005 Mike Wray <mike.wray@hp.com>
# Copyright 2005 XenSource Ltd
def randomMAC():
    """Generate a random MAC address.

    Uses OUI (Organizationally Unique Identifier) 00-16-3E, allocated to
    Xensource, Inc. The OUI list is available at
    http://standards.ieee.org/regauth/oui/oui.txt.

    The remaining 3 fields are random, with the first bit of the first
    random field set 0.

    @return: MAC address string
    """
    mac = [ 0x00, 0x16, 0x3e,
            random.randint(0x00, 0x7f),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff) ]
    return ':'.join(map(lambda x: "%02x" % x, mac))

# the following three functions are from xend/uuid.py and are thus
# available under the LGPL,
# Copyright 2005 Mike Wray <mike.wray@hp.com>
# Copyright 2005 XenSource Ltd
def randomUUID():
    """Generate a random UUID."""

    return [ random.randint(0, 255) for _ in range(0, 16) ]

def uuidToString(u):
    return "-".join(["%02x" * 4, "%02x" * 2, "%02x" * 2, "%02x" * 2,
                     "%02x" * 6]) % tuple(u)

def uuidFromString(s):
    s = s.replace('-', '')
    return [ int(s[i : i + 2], 16) for i in range(0, 32, 2) ]

# the following function quotes from python2.5/uuid.py
def get_host_network_devices():
    device = []
    for dir in ['', '/sbin/', '/usr/sbin']:
        executable = os.path.join(dir, "ifconfig")
        if not os.path.exists(executable):
            continue
        try:
            cmd = 'LC_ALL=C %s -a 2>/dev/null' % (executable)
            pipe = os.popen(cmd)
        except IOError:
            continue
        for line in pipe:
            words = line.lower().split()
            for i in range(len(words)):
                if words[i] == "hwaddr":
                    device.append(words)
    return device
