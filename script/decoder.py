#!/usr/bin/python
# Modiefied version of https://github.com/svinota/pyroute2/blob/master/tests/decoder/decoder.py
'''
Usage::
    ./decoder.py nl_([0-9]+)_([0-9]+)_(snd|rec)

Sample::
    ./decoder.py nl_000000_00000016_snd

'''
import sys, argparse, re, struct, os
import pprint
from importlib import import_module
from pyroute2.common import load_dump
from pyroute2.common import hexdump
from pyroute2.netlink import rtnl
from pyroute2.netlink import *
from pyroute2.netlink.nlsocket import Marshal
from pyroute2.netlink.rtnl.tcmsg import tcmsg
from pyroute2.netlink.rtnl.rtmsg import rtmsg
from pyroute2.netlink.rtnl.ndmsg import ndmsg
from pyroute2.netlink.rtnl.ndtmsg import ndtmsg
from pyroute2.netlink.rtnl.fibmsg import fibmsg
from pyroute2.netlink.rtnl.ifinfmsg import ifinfmsg
from pyroute2.netlink.rtnl.ifaddrmsg import ifaddrmsg
from pyroute2.netlink.rtnl import RTM_VALUES
from pyroute2.netlink.nl80211 import *

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="count", default=0)
parser.add_argument("-C", "--nocolor", action="count", help="prevent coloring", default=0)
parser.add_argument("-D", "--nodecode", action="count", help="stringify constants/flags", default=0)
parser.add_argument('files', nargs='*', default=[])
opts = parser.parse_args()

try:
    from sty import fg, bg, ef, rs
    def setcolor(a):
        if opts.nocolor: # && not (os.isatty(1))
            return a
        return bg.blue+a+bg.rs
except:
    def setcolor(a):
        return a

nlm_f = (
    (NLM_F_REQUEST, 'NLM_F_REQUEST'),
    (NLM_F_MULTI, 'NLM_F_MULTI'),
    (NLM_F_ACK, 'NLM_F_ACK'),
    (NLM_F_ECHO, 'NLM_F_ECHO'));

# Modifiers to GET request
nlm_f_get = (
    (NLM_F_DUMP, 'NLM_F_DUMP'),
    (NLM_F_ROOT, 'NLM_F_ROOT'),
    (NLM_F_MATCH, 'NLM_F_MATCH'),
    (NLM_F_ATOMIC, 'NLM_F_ATOMIC'));

# Modifiers to NEW request
nlm_f_new = (
    (NLM_F_REPLACE, 'NLM_F_REPLACE'),
    (NLM_F_EXCL, 'NLM_F_EXCL'),
    (NLM_F_CREATE, 'NLM_F_CREATE'),
    (NLM_F_APPEND, 'NLM_F_APPEND'));

msg_map = {rtnl.RTM_NEWLINK: ifinfmsg,
           rtnl.RTM_DELLINK: ifinfmsg,
           rtnl.RTM_GETLINK: ifinfmsg,
           rtnl.RTM_SETLINK: ifinfmsg,
           rtnl.RTM_NEWADDR: ifaddrmsg,
           rtnl.RTM_DELADDR: ifaddrmsg,
           rtnl.RTM_GETADDR: ifaddrmsg,
           rtnl.RTM_NEWROUTE: rtmsg,
           rtnl.RTM_DELROUTE: rtmsg,
           rtnl.RTM_GETROUTE: rtmsg,
           rtnl.RTM_NEWRULE: fibmsg,
           rtnl.RTM_DELRULE: fibmsg,
           rtnl.RTM_GETRULE: fibmsg,
           rtnl.RTM_NEWNEIGH: ndmsg,
           rtnl.RTM_DELNEIGH: ndmsg,
           rtnl.RTM_GETNEIGH: ndmsg,
           rtnl.RTM_NEWQDISC: tcmsg,
           rtnl.RTM_DELQDISC: tcmsg,
           rtnl.RTM_GETQDISC: tcmsg,
           rtnl.RTM_NEWTCLASS: tcmsg,
           rtnl.RTM_DELTCLASS: tcmsg,
           rtnl.RTM_GETTCLASS: tcmsg,
           rtnl.RTM_NEWTFILTER: tcmsg,
           rtnl.RTM_DELTFILTER: tcmsg,
           rtnl.RTM_GETTFILTER: tcmsg,
           rtnl.RTM_NEWNEIGHTBL: ndtmsg,
           rtnl.RTM_GETNEIGHTBL: ndtmsg,
           rtnl.RTM_SETNEIGHTBL: ndtmsg}

NL80211_map = {
    NL80211_CMD_UNSPEC : 'NL80211_CMD_UNSPEC',
    NL80211_CMD_GET_WIPHY : 'NL80211_CMD_GET_WIPHY',
    NL80211_CMD_SET_WIPHY : 'NL80211_CMD_SET_WIPHY',
    NL80211_CMD_NEW_WIPHY : 'NL80211_CMD_NEW_WIPHY',
    NL80211_CMD_DEL_WIPHY : 'NL80211_CMD_DEL_WIPHY',
    NL80211_CMD_GET_INTERFACE : 'NL80211_CMD_GET_INTERFACE',
    NL80211_CMD_SET_INTERFACE : 'NL80211_CMD_SET_INTERFACE',
    NL80211_CMD_NEW_INTERFACE : 'NL80211_CMD_NEW_INTERFACE',
    NL80211_CMD_DEL_INTERFACE : 'NL80211_CMD_DEL_INTERFACE',
    NL80211_CMD_GET_KEY : 'NL80211_CMD_GET_KEY',
    NL80211_CMD_SET_KEY : 'NL80211_CMD_SET_KEY',
    NL80211_CMD_NEW_KEY : 'NL80211_CMD_NEW_KEY',
    NL80211_CMD_DEL_KEY : 'NL80211_CMD_DEL_KEY',
    NL80211_CMD_GET_BEACON : 'NL80211_CMD_GET_BEACON',
    NL80211_CMD_SET_BEACON : 'NL80211_CMD_SET_BEACON',
    NL80211_CMD_START_AP : 'NL80211_CMD_START_AP|NL80211_CMD_NEW_BEACON',
    NL80211_CMD_STOP_AP : 'NL80211_CMD_STOP_AP|NL80211_CMD_DEL_BEACON',
    NL80211_CMD_GET_STATION : 'NL80211_CMD_GET_STATION',
    NL80211_CMD_SET_STATION : 'NL80211_CMD_SET_STATION',
    NL80211_CMD_NEW_STATION : 'NL80211_CMD_NEW_STATION',
    NL80211_CMD_DEL_STATION : 'NL80211_CMD_DEL_STATION',
    NL80211_CMD_GET_MPATH : 'NL80211_CMD_GET_MPATH',
    NL80211_CMD_SET_MPATH : 'NL80211_CMD_SET_MPATH',
    NL80211_CMD_NEW_MPATH : 'NL80211_CMD_NEW_MPATH',
    NL80211_CMD_DEL_MPATH : 'NL80211_CMD_DEL_MPATH',
    NL80211_CMD_SET_BSS : 'NL80211_CMD_SET_BSS',
    NL80211_CMD_SET_REG : 'NL80211_CMD_SET_REG',
    NL80211_CMD_REQ_SET_REG : 'NL80211_CMD_REQ_SET_REG',
    NL80211_CMD_GET_MESH_CONFIG : 'NL80211_CMD_GET_MESH_CONFIG',
    NL80211_CMD_SET_MESH_CONFIG : 'NL80211_CMD_SET_MESH_CONFIG',
    NL80211_CMD_SET_MGMT_EXTRA_IE : 'NL80211_CMD_SET_MGMT_EXTRA_IE',
    NL80211_CMD_GET_REG : 'NL80211_CMD_GET_REG',

    NL80211_CMD_GET_SCAN : 'NL80211_CMD_GET_SCAN',
    NL80211_CMD_TRIGGER_SCAN : 'NL80211_CMD_TRIGGER_SCAN',
    NL80211_CMD_NEW_SCAN_RESULTS : 'NL80211_CMD_NEW_SCAN_RESULTS',
    NL80211_CMD_SCAN_ABORTED : 'NL80211_CMD_SCAN_ABORTED',
    NL80211_CMD_REG_CHANGE : 'NL80211_CMD_REG_CHANGE',
    NL80211_CMD_AUTHENTICATE : 'NL80211_CMD_AUTHENTICATE',
    NL80211_CMD_ASSOCIATE : 'NL80211_CMD_ASSOCIATE',
    NL80211_CMD_DEAUTHENTICATE : 'NL80211_CMD_DEAUTHENTICATE',
    NL80211_CMD_DISASSOCIATE : 'NL80211_CMD_DISASSOCIATE',
    NL80211_CMD_MICHAEL_MIC_FAILURE : 'NL80211_CMD_MICHAEL_MIC_FAILURE',
    NL80211_CMD_REG_BEACON_HINT : 'NL80211_CMD_REG_BEACON_HINT',
    NL80211_CMD_JOIN_IBSS : 'NL80211_CMD_JOIN_IBSS',
    NL80211_CMD_LEAVE_IBSS : 'NL80211_CMD_LEAVE_IBSS',
    NL80211_CMD_TESTMODE : 'NL80211_CMD_TESTMODE',
    NL80211_CMD_CONNECT : 'NL80211_CMD_CONNECT',
    NL80211_CMD_ROAM : 'NL80211_CMD_ROAM',
    NL80211_CMD_DISCONNECT : 'NL80211_CMD_DISCONNECT',
    NL80211_CMD_SET_WIPHY_NETNS : 'NL80211_CMD_SET_WIPHY_NETNS',
    NL80211_CMD_GET_SURVEY : 'NL80211_CMD_GET_SURVEY',
    NL80211_CMD_NEW_SURVEY_RESULTS : 'NL80211_CMD_NEW_SURVEY_RESULTS',
    NL80211_CMD_SET_PMKSA : 'NL80211_CMD_SET_PMKSA',

    NL80211_CMD_DEL_PMKSA : 'NL80211_CMD_DEL_PMKSA',
    NL80211_CMD_FLUSH_PMKSA : 'NL80211_CMD_FLUSH_PMKSA',
    NL80211_CMD_REMAIN_ON_CHANNEL : 'NL80211_CMD_REMAIN_ON_CHANNEL',
    NL80211_CMD_CANCEL_REMAIN_ON_CHANNEL : 'NL80211_CMD_CANCEL_REMAIN_ON_CHANNEL',
    NL80211_CMD_SET_TX_BITRATE_MASK : 'NL80211_CMD_SET_TX_BITRATE_MASK',
    NL80211_CMD_REGISTER_FRAME : 'NL80211_CMD_REGISTER_FRAME|NL80211_CMD_REGISTER_ACTION',
    NL80211_CMD_FRAME : 'NL80211_CMD_FRAME|NL80211_CMD_ACTION',

    NL80211_CMD_FRAME_TX_STATUS : 'NL80211_CMD_FRAME_TX_STATUS|NL80211_CMD_ACTION_TX_STATUS',

    NL80211_CMD_SET_POWER_SAVE : 'NL80211_CMD_SET_POWER_SAVE',
    NL80211_CMD_GET_POWER_SAVE : 'NL80211_CMD_GET_POWER_SAVE',
    NL80211_CMD_SET_CQM : 'NL80211_CMD_SET_CQM',
    NL80211_CMD_NOTIFY_CQM : 'NL80211_CMD_NOTIFY_CQM',
    NL80211_CMD_SET_CHANNEL : 'NL80211_CMD_SET_CHANNEL',
    NL80211_CMD_SET_WDS_PEER : 'NL80211_CMD_SET_WDS_PEER',
    NL80211_CMD_FRAME_WAIT_CANCEL : 'NL80211_CMD_FRAME_WAIT_CANCEL',
    NL80211_CMD_JOIN_MESH : 'NL80211_CMD_JOIN_MESH',
    NL80211_CMD_LEAVE_MESH : 'NL80211_CMD_LEAVE_MESH',
    NL80211_CMD_UNPROT_DEAUTHENTICATE : 'NL80211_CMD_UNPROT_DEAUTHENTICATE',
    NL80211_CMD_UNPROT_DISASSOCIATE : 'NL80211_CMD_UNPROT_DISASSOCIATE',
    NL80211_CMD_NEW_PEER_CANDIDATE : 'NL80211_CMD_NEW_PEER_CANDIDATE',
    NL80211_CMD_GET_WOWLAN : 'NL80211_CMD_GET_WOWLAN',
    NL80211_CMD_SET_WOWLAN : 'NL80211_CMD_SET_WOWLAN',
    NL80211_CMD_START_SCHED_SCAN : 'NL80211_CMD_START_SCHED_SCAN',
    NL80211_CMD_STOP_SCHED_SCAN : 'NL80211_CMD_STOP_SCHED_SCAN',
    NL80211_CMD_SCHED_SCAN_RESULTS : 'NL80211_CMD_SCHED_SCAN_RESULTS',
    NL80211_CMD_SCHED_SCAN_STOPPED : 'NL80211_CMD_SCHED_SCAN_STOPPED',
    NL80211_CMD_SET_REKEY_OFFLOAD : 'NL80211_CMD_SET_REKEY_OFFLOAD',
    NL80211_CMD_PMKSA_CANDIDATE : 'NL80211_CMD_PMKSA_CANDIDATE',
    NL80211_CMD_TDLS_OPER : 'NL80211_CMD_TDLS_OPER',
    NL80211_CMD_TDLS_MGMT : 'NL80211_CMD_TDLS_MGMT',
    NL80211_CMD_UNEXPECTED_FRAME : 'NL80211_CMD_UNEXPECTED_FRAME',
    NL80211_CMD_PROBE_CLIENT : 'NL80211_CMD_PROBE_CLIENT',
    NL80211_CMD_REGISTER_BEACONS : 'NL80211_CMD_REGISTER_BEACONS',
    NL80211_CMD_UNEXPECTED_4ADDR_FRAME : 'NL80211_CMD_UNEXPECTED_4ADDR_FRAME',
    NL80211_CMD_SET_NOACK_MAP : 'NL80211_CMD_SET_NOACK_MAP',
    NL80211_CMD_CH_SWITCH_NOTIFY : 'NL80211_CMD_CH_SWITCH_NOTIFY',
    NL80211_CMD_START_P2P_DEVICE : 'NL80211_CMD_START_P2P_DEVICE',
    NL80211_CMD_STOP_P2P_DEVICE : 'NL80211_CMD_STOP_P2P_DEVICE',
    NL80211_CMD_CONN_FAILED : 'NL80211_CMD_CONN_FAILED',
    NL80211_CMD_SET_MCAST_RATE : 'NL80211_CMD_SET_MCAST_RATE',
    NL80211_CMD_SET_MAC_ACL : 'NL80211_CMD_SET_MAC_ACL',

    NL80211_CMD_RADAR_DETECT : 'NL80211_CMD_RADAR_DETECT',
    NL80211_CMD_GET_PROTOCOL_FEATURES : 'NL80211_CMD_GET_PROTOCOL_FEATURES',
    NL80211_CMD_UPDATE_FT_IES : 'NL80211_CMD_UPDATE_FT_IES',
    NL80211_CMD_FT_EVENT : 'NL80211_CMD_FT_EVENT',
    NL80211_CMD_CRIT_PROTOCOL_START : 'NL80211_CMD_CRIT_PROTOCOL_START',
    NL80211_CMD_CRIT_PROTOCOL_STOP : 'NL80211_CMD_CRIT_PROTOCOL_STOP',
    NL80211_CMD_GET_COALESCE : 'NL80211_CMD_GET_COALESCE',
    NL80211_CMD_SET_COALESCE : 'NL80211_CMD_SET_COALESCE',
    NL80211_CMD_CHANNEL_SWITCH : 'NL80211_CMD_CHANNEL_SWITCH',
    NL80211_CMD_VENDOR : 'NL80211_CMD_VENDOR',
    NL80211_CMD_SET_QOS_MAP : 'NL80211_CMD_SET_QOS_MAP',
    NL80211_CMD_ADD_TX_TS : 'NL80211_CMD_ADD_TX_TS',
    NL80211_CMD_DEL_TX_TS : 'NL80211_CMD_DEL_TX_TS',
    NL80211_CMD_GET_MPP : 'NL80211_CMD_GET_MPP',
    NL80211_CMD_JOIN_OCB : 'NL80211_CMD_JOIN_OCB',
    NL80211_CMD_LEAVE_OCB : 'NL80211_CMD_LEAVE_OCB',

    NL80211_CMD_CH_SWITCH_STARTED_NOTIFY : 'NL80211_CMD_CH_SWITCH_STARTED_NOTIFY',
    NL80211_CMD_TDLS_CHANNEL_SWITCH : 'NL80211_CMD_TDLS_CHANNEL_SWITCH',
    NL80211_CMD_TDLS_CANCEL_CHANNEL_SWITCH : 'NL80211_CMD_TDLS_CANCEL_CHANNEL_SWITCH',
    NL80211_CMD_WIPHY_REG_CHANGE : 'NL80211_CMD_WIPHY_REG_CHANGE'
}

GENCTRL_VALUES = {
    CTRL_CMD_UNSPEC : 'CTRL_CMD_UNSPEC',
    CTRL_CMD_NEWFAMILY : 'CTRL_CMD_NEWFAMILY',
    CTRL_CMD_DELFAMILY : 'CTRL_CMD_DELFAMILY',
    CTRL_CMD_GETFAMILY : 'CTRL_CMD_GETFAMILY',
    CTRL_CMD_NEWOPS : 'CTRL_CMD_NEWOPS',
    CTRL_CMD_DELOPS : 'CTRL_CMD_DELOPS',
    CTRL_CMD_GETOPS : 'CTRL_CMD_GETOPS',
    CTRL_CMD_NEWMCAST_GRP : 'CTRL_CMD_NEWMCAST_GRP',
    CTRL_CMD_DELMCAST_GRP : 'CTRL_CMD_DELMCAST_GRP'
};

GENCTRL_NAMES = {
    'CTRL_CMD_UNSPEC':       CTRL_CMD_UNSPEC,
    'CTRL_CMD_NEWFAMILY':    CTRL_CMD_NEWFAMILY,
    'CTRL_CMD_DELFAMILY':    CTRL_CMD_DELFAMILY,
    'CTRL_CMD_GETFAMILY':    CTRL_CMD_GETFAMILY,
    'CTRL_CMD_NEWOPS':       CTRL_CMD_NEWOPS,      
    'CTRL_CMD_DELOPS':       CTRL_CMD_DELOPS,       
    'CTRL_CMD_GETOPS':       CTRL_CMD_GETOPS,       
    'CTRL_CMD_NEWMCAST_GRP': CTRL_CMD_NEWMCAST_GRP, 
    'CTRL_CMD_DELMCAST_GRP': CTRL_CMD_DELMCAST_GRP 
};

def error(a):
    sys.stderr.write(a+"\n")
    exit(1)

for fn in opts.files:

    with open(fn, mode='rb') as file:
        data = file.read()

    proto = 0
    direction = "rec"

    m = re.match("nl_([0-9]+)_([0-9]+)_(snd|rec)", os.path.basename(fn))
    if (m):
        proto = int(m.group(2))
        direction = m.group(3)

    offset = 0
    inbox = []

    while offset < len(data):
        typ, = struct.unpack_from("h",data,offset+4)
        flg, = struct.unpack_from("h",data,offset+6)
        met=None
        cmd=None
        # select decoder
        if (proto==0):
            # routing protocol
            if typ in msg_map:
                if (opts.verbose):
                    print("Lookup routing protocol %s(%d)" %(RTM_VALUES[typ],typ))
                met = msg_map[typ]
            else:
                error("--------- Unknown router cmd %d --------" %(typ))
        elif (proto==16):
            if (typ==16):
                # ctrl messages
                cmd, = struct.unpack_from("B",data,offset+16)
                if (opts.verbose):
                    print("Lookup generic protocol %s(%d)" %(GENCTRL_VALUES[cmd],cmd))
                met = ctrlmsg
            elif (typ==28):
                # nl80211 messages
                m = import_module('pyroute2.netlink.nl80211')
                met = nl80211cmd
            else:
                print("--------- Generic protocol type %d unimpl --------" %(typ))
        else:
            print("--------- unimpl protocol cmd %d --------" %(proto))

        if (met == None):
            met = genlmsg

        msg = met(data[offset:])
        msg.decode()

        # add some extra info
        if not (opts.nodecode):
            if (proto == 16):
                if (typ == 28):
                    if 'cmd' in msg and msg['cmd'] in NL80211_map:
                        msg['cmd'] = NL80211_map[msg['cmd']]
                if (typ == 16):
                    if cmd != None and cmd in GENCTRL_VALUES:
                        msg['cmd'] = GENCTRL_VALUES[cmd]
                
            elif (proto == 0):
                if msg['header']['type'] in RTM_VALUES:
                    msg['cmd'] = RTM_VALUES[msg['header']['type']]

            fa = [ ("0x%x"%(msg['header']['flags']))]
            f = msg['header']['flags']

            def fsub(a, f):
                for fl in a:
                    if (f & fl[0]):
                        f = f & ~ fl[0];
                        fa.append(fl[1])
                return f

            f = fsub(nlm_f, f)
            if ('cmd' in msg and isinstance(msg['cmd'], str)):
                if (msg['cmd'].find("_GET") != -1):
                    f = fsub(nlm_f_get, f)
                elif (msg['cmd'].find("_NEW") != -1):
                    f = fsub(nlm_f_new, f)
                msg['cmd'] = msg['cmd']
            if (f != 0):
                fa.append("0x%x" %(f))
            msg['header']['flags'] = "|".join(fa)


            
        o = pprint.pformat(msg)
        o2 = ""
        if (direction == 'snd'):
            while len(o):
                m = re.match(r"(.*?)('[a-zA-Z0-9]+_CMD_[a-zA-Z_0-9]+')", o, re.MULTILINE | re.DOTALL);
                if (m):
                    o2+=(m.group(1))
                    o2+=(setcolor(m.group(2)));
                    o = o[len(m.group(0)):]
                else:
                    break;

        o2+=(o)
        print(o2)
        offset += msg['header']['length']
