# -*- coding: utf-8 -*-
import nuke
import os
import glob

from set_backdrop import set_rendered, set_unrendered

def increase_version():
    wn = nuke.thisNode() 
    wn_name = wn.name()
    wn_file = wn['file'].getValue()
    new_version = wn['which'].getValue()
    curr_version = wn['currVersion'].value()

    # new path version
    new_version = int(new_version) + 1
    new_version_str = 'v' + str(new_version).zfill(3)
    wn['which'].setValue(new_version)
    wn['currVersion'].setValue(new_version_str)
    new_file_path = wn_file.replace(curr_version, new_version_str)

    # set new pathS
    wn['file'].setValue(new_file_path)

    current_path, current_extension = os.path.splitext(new_file_path)
    file_extension = current_extension[1:]

    geometry_extensions = ['abc','fbx', 'mxf', 'obj']

    if file_extension == 'exr':
        glob_path = new_file_path.replace("%4d", "*")
        glob_result = glob.glob(glob_path)
        if glob_result:
            set_rendered()
        else:
            set_unrendered()
    elif file_extension in geometry_extensions:
        if os.path.isfile():
            set_rendered()
        else:
            set_unrendered()
    elif file_extension == 'nkpc':
        if os.path.isfile(new_file_path):
            set_rendered()
        else:
            set_unrendered()
    else:
        nuke.message('Unknown file extension')




