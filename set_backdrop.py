# -*- coding: utf-8 -*-
import nuke

def set_rendered():
    tn = nuke.thisNode()
    tn_name = tn.name()
    version = tn['currVersion'].value()
    bkd_class = tn_name + '_back'
    bkd_nodes = nuke.allNodes(filter="BackdropNode")

    for node in bkd_nodes:
        if node.knob("class") and node["class"].value() == bkd_class:
            backdrop = node

    backdrop['tile_color'].setValue(0x2a8400ff)
    backdrop['label'].setValue("cache\n" + version)


def set_unrendered():
    tn = nuke.thisNode()
    tn_name = tn.name()
    bkd_nodes = nuke.allNodes(filter="BackdropNode")
    version = tn['currVersion'].value()
    bkd_class = tn_name + '_back'
    backdrop = None

    for node in bkd_nodes:
        if node.knob("class") and node["class"].value() == bkd_class:
            backdrop = node

    backdrop['tile_color'].setValue(0x9bff)
    backdrop['label'].setValue("cache\n" + version)