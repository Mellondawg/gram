# Set of utilities for helping with VMOC functionailty and testing

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.openflow import *
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.vlan import vlan
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.arp import arp
from pox.lib.packet.tcp import tcp

log = core.getLogger()

# Send an OF command to flood a packet out a connection
def flood_packet(event, connection):
    log.debug("Flooding " + str(event))
    msg = of.ofp_packet_out()
    msg.data = event.ofp
    msg.in_port = event.port
    msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
    connection.send(msg)

# Send an OF command to install a flow-mod to send packets 
# matching given packet out given port
def send_flowmod_for_packet(event, connection, packet, out_port):
    msg = of.ofp_flow_mod()
    msg.match = of.ofp_match.from_packet(packet, event.port)
    msg.idle_timeout = 10
    msg.hard_timeout = 30
    msg.actions.append(of.ofp_action_output(port=out_port))
    connection.send(msg)
    log.debug("Setting flow mod " + str(msg))

# Send an OF command to send a packet out a given port
def send_packet_out(connection, packet, in_port, out_port):
    msg = of.ofp_packet_out(data=packet.raw, in_port = in_port)
    msg.actions.append(of.ofp_action_output(port=out_port))
    connection.send(msg)
    log.debug("Sending packet_out " + str(msg))

# Create a new ethernet packet with vlan tag fields added
def add_vlan_to_packet(ethernet_packet, vlan_id):
    # Grab the ethernet packet = E
    new_ethernet_packet = ethernet(ethernet_packet.raw)
    new_ethernet_packet.type = ethernet.VLAN_TYPE
    E = new_ethernet_packet.hdr('')
    # Create the vlan packet = V
    vlan_packet = vlan()
    vlan_packet.id = vlan_id
    vlan_packet.pcp = 0
    vlan_packet.eth_type = ethernet_packet.type
    V = vlan_packet.hdr('')
    # Grab the rest of the packet = R
    R = ethernet_packet.raw[ethernet.MIN_LEN:]
    # Construct E + V + R
    new_raw = E + V + R
    new_ethernet_packet = ethernet(new_raw)
    return new_ethernet_packet

                  
