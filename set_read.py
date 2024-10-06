import nuke
import os
import re
import time
from set_backdrop import set_rendered, set_unrendered

def set_read_node(tn):
    tn_name = tn.name()
    tn_path_file = tn['file'].getValue()
    read_name = tn_name + '_Read'

    # get the current node position
    tn_xpos = int(tn.xpos())
    tn_ypos = int(tn.ypos())
    
    # create read node
    def create_read():
        wn = nuke.createNode('Read', inpanel=False)
        wn.setXYpos(tn_xpos, tn_ypos + 60)
        wn['name'].setValue(read_name)
        wn['file'].setValue(tn_path_file)
        wn['localizationPolicy'].setValue('onDemand')
        wn['on_error'].setValue('black')
        wn['raw'].setValue(True)
        wn['auto_alpha'].setValue(True)
        wn['postage_stamp'].setValue(False)

        # get frame range
        file_dir = os.path.dirname(tn_path_file)
        file_pattern = r".*\.(\d+)\.exr"

        seq_files = os.listdir(file_dir)
        seq_frames = []
        first_frame = None
        last_frame = None

        if seq_files:
            for file in seq_files:
                match = re.match(file_pattern, file)
                if match:
                    frame = int(match.group(1))
                    seq_frames.append(frame)
            
            first_frame = min(seq_frames)
            last_frame = max(seq_frames)

        # set frame range
        if first_frame and last_frame:
            wn['first'].setValue(first_frame)
            wn['last'].setValue(last_frame)
            wn['origfirst'].setValue(first_frame)
            wn['origlast'].setValue(last_frame)
            set_rendered()
            
        # set out dot
        out_dt = nuke.toNode(tn_name + '_OUT')
        out_dt.setInput(0, wn)
        nuke.connectViewer(0, out_dt)

    # validate if node exists
    if nuke.exists(read_name):
        rn = nuke.toNode(read_name)
        nuke.delete(rn)
        create_read()
    else:
        create_read()

def set_readgeo_node(tn):
    tn_name = tn.name()
    tn_path_file = tn['file'].getValue()
    read_name = tn_name + '_Read'

    # get the current node position
    tn_xpos = int(tn.xpos())
    tn_ypos = int(tn.ypos())

    # create georead
    def create_read_geo():
        rn = nuke.createNode('ReadGeo2', inpanel=False)
        rn.setXYpos(tn_xpos, tn_ypos + 60)
        rn['name'].setValue(read_name)
        rn['file'].setValue(tn_path_file)
        rn['localizationPolicy'].setValue('onDemand')
        set_rendered()

        # set out dot
        out_dt = nuke.toNode(tn_name + '_OUT')
        out_dt.setInput(0, rn)
        nuke.connectViewer(0, out_dt)

    # validate if node exists
    if nuke.exists(read_name):
        rn = nuke.toNode(read_name)
        nuke.delete(rn)
        create_read_geo()
    else:
        create_read_geo()


def set_particleache_node(tn):
    tn_name = tn.name()
    tn['particle_cache_read_from_file'].setValue(True)

    # set out dot
    out_dt = nuke.toNode(tn_name + '_OUT')
    out_dt.setInput(0, tn)
    nuke.connectViewer(0, out_dt)


def set_read():
    tn = nuke.thisNode()
    tn_class = tn.Class()

    if tn_class == 'Write' or tn_class == 'DeepWrite':
        set_read_node(tn)
    elif tn_class == 'WriteGeo':
        set_readgeo_node(tn)
    elif tn_class == 'ParticleCache':
        set_particleache_node(tn)