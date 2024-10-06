import nuke
import os
import re
import hashlib
import random
import string

from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QDialogButtonBox, QLineEdit
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile, Qt, QObject, QEvent


file_dir = os.path.dirname(os.path.realpath(__file__))
ui_file = os.path.join(file_dir, "CompCacheWindow.ui")
global_ui_object = None

# custom event filter
class EnterKeyFilter(QObject):
    # define props
    def __init__(self, parent=None, on_submit=None):
        super(EnterKeyFilter, self).__init__(parent)
        # set on_sumbit trigger
        self.on_submit = on_submit

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter):
            # trigger onSubmit
            self.on_submit()
            return True
        return super(EnterKeyFilter, self).eventFilter(obj, event)        

def MainUI():
    global global_ui_object
    loader = QUiLoader()
    file = QFile(ui_file)
    file.open(QFile.ReadOnly)
    window = loader.load(file)
    file.close()

    # always on top
    window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)

    # write buttons
    writeBtn = window.findChild(QPushButton, 'writeBtn')
    geoBtn = window.findChild(QPushButton, 'geoBtn')
    deepBtn = window.findChild(QPushButton, 'deepBtn')
    particleBtn = window.findChild(QPushButton, 'particleBtn')
    writeBtns = [writeBtn, geoBtn, deepBtn, particleBtn]

    # mask buttons
    maskAllBtn = window.findChild(QPushButton, 'maskAllBtn')
    maskRGBABtn = window.findChild(QPushButton, 'maskRGBABtn')
    maskRGBBtn = window.findChild(QPushButton, 'maskRGBBtn')
    maskAlphaBtn = window.findChild(QPushButton, 'maskAlphaBtn')
    maskButtons = [maskAllBtn, maskRGBABtn, maskRGBBtn, maskAlphaBtn]

    # bits buttons
    _16BitBtn = window.findChild(QPushButton, '_16BitBtn')
    _32BitBtn = window.findChild(QPushButton, '_32BitBtn')
    bitsButtons = [_16BitBtn, _32BitBtn]

    # textbox
    cacheNameTxt = window.findChild(QLineEdit, 'cacheName')

    # submit button
    submitBtns = window.findChild(QDialogButtonBox, "submitBtns")

    window.previous_write_btn = writeBtn
    window.previous_mask_btn = maskAllBtn
    window.previous_bit_btn = _16BitBtn

    # user press enter and pass the onSubmit function
    enter_key_filter = EnterKeyFilter(parent=window, on_submit=lambda: onSubmit(window, cacheNameTxt, writeBtns, maskButtons, bitsButtons))
    window.installEventFilter(enter_key_filter)

    writeBtn.clicked.connect(lambda: select_write(window, writeBtn, maskButtons, bitsButtons))
    geoBtn.clicked.connect(lambda: select_write(window, geoBtn, maskButtons, bitsButtons))
    deepBtn.clicked.connect(lambda: select_write(window, deepBtn, maskButtons, bitsButtons))
    particleBtn.clicked.connect(lambda: select_write(window, particleBtn, maskButtons, bitsButtons))

    maskAllBtn.clicked.connect(lambda: select_mask(window, maskAllBtn))
    maskRGBABtn.clicked.connect(lambda: select_mask(window, maskRGBABtn))
    maskRGBBtn.clicked.connect(lambda: select_mask(window, maskRGBBtn))
    maskAlphaBtn.clicked.connect(lambda: select_mask(window, maskAlphaBtn))

    _16BitBtn.clicked.connect(lambda: select_bits(window, _16BitBtn))
    _32BitBtn.clicked.connect(lambda: select_bits(window, _32BitBtn))

    submitBtns.accepted.connect(lambda: onSubmit(window, cacheNameTxt, writeBtns, maskButtons, bitsButtons))
    submitBtns.rejected.connect(lambda: onReject(window))

    global_ui_object = window
    return window

# python write buttons code
python_decrease = 'decrease_version.decrease_version()'
python_increase = 'increase_version.increase_version()'
python_delete = 'nuke.message("delete")'
python_set_read = 'set_read.set_read()'

def create_backdrop(nodes):
    # deselect nodes
    nuke.selectAll()
    nuke.invertSelection()

    for node in nodes:
        node.setSelected(True)

    # calc bounds
    sel = nuke.selectedNodes()
    bdX = min([node.xpos() for node in sel])
    bdY = min([node.ypos() for node in sel])
    bdW = max([node.xpos() + node.screenWidth() for node in sel]) - bdX
    bdH = max([node.ypos() + node.screenHeight() for node in sel]) - bdY

    # backdrop offset
    ofst = 50
    left, top, right, bottom = (-ofst, -(ofst * 2), ofst, ofst)
    bdX += left
    bdY += top
    bdW += (right - left)
    bdH += (bottom - top)
    bckDp = nuke.nodes.BackdropNode(xpos=bdX, bdwidth=bdW, ypos=bdY, bdheight=bdH, note_font_size=30)
    bckDp['label'].setValue("cache\nv001")
    bckDp['note_font'].setValue("Verdana Bold")
    bckDp['note_font_size'].setValue(21)
    bckDp['tile_color'].setValue(0x9bff)

    for node in nodes:
        node.setSelected(False)
    
    return bckDp


def generate_id_hash():
    def generate_hash(s):
        md5 = hashlib.md5()
        md5.update(s.encode('utf-8'))
        return md5.hexdigest()[:8]

    g_id = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    g_hash = generate_hash(g_id)

    return g_id, g_hash


def get_cache_file(cacheNameTxt, writeBtns):
    g_id, g_hash = generate_id_hash() # generate hash
    sel_write = get_selected_write_opt(writeBtns)

    # get current script folder
    sp = nuke.root().name()
    sdir = os.path.dirname(sp) # script dir
    sname = os.path.basename(sp) # script name name.nk
    sname = sname.split('.')[0] # script name no '.nk'
    cn = "" # cache name var

    if cacheNameTxt.text():
        cn = str(cacheNameTxt.text())
    else:
        cn = str(g_hash)

    # select the file path
    if sel_write == 'Write':
        cf = sdir + '/cache/' + sname + '/' + cn + '/v001/' + cn + '.%4d.exr'
        return cf, cn
    elif sel_write == 'DeepWrite':
        cf = sdir + '/cache/' + sname + '/' + cn + '/v001/' + cn + '.%4d.exr'
        return cf, cn
    elif sel_write == 'GeoWrite':
        cf = sdir + '/cache/' + sname + '/' + cn + '/v001/' + cn + '.abc'
        return cf, cn
    elif sel_write == 'ParticleCache':
        cf = sdir + '/cache/' + sname + '/' + cn + '/v001/' + cn + '.%4d.nkpc'
        return cf, cn


def set_write_node(dt_node, cacheNameTxt, maskButtons, bitsButtons, writeBtns):
    # file path
    cf, cn = get_cache_file(cacheNameTxt, writeBtns)
    sel_channels = get_selected_channels_opt(maskButtons)
    sel_bits = get_selected_bits_opt(bitsButtons)

    # create a write node and connect it to the dot
    dt_xpos = int(dt_node.xpos())
    dt_ypos = int(dt_node.ypos())
    wn = nuke.createNode("Write", inpanel=False)
    wn.setXYpos(dt_xpos - 180, dt_ypos - 20) # write node position
    wn.setInput(0, dt_node)
    wn['tile_color'].setValue(0x9e6182ff)
    wn['label'].setValue('cache')
    wn['raw'].setValue(True)
    wn['create_directories'].setValue(True)
    wn['file'].setValue(cf)
    wn['channels'].setValue(sel_channels.lower())
    wn['file_type'].setValue('exr')

    # create write cache tab
    cache_tab = nuke.Tab_Knob('cache_tab','cache')
    wn.addKnob(cache_tab)

    # add cache knobs
    cache_name_knob = nuke.Text_Knob('currName', 'name')
    cache_name_knob.setValue(cn)
    wn.addKnob(cache_name_knob)
    cache_version_knob = nuke.Text_Knob('currVersion', 'version')
    cache_version_knob.setValue('v001')
    wn.addKnob(cache_version_knob)
    div_knob = nuke.Text_Knob('div', '')
    wn.addKnob(div_knob)
    which_knob = nuke.Int_Knob('which', 'which')
    which_knob.setValue(1)
    wn.addKnob(which_knob)
    decrease_knob = nuke.PyScript_Knob('dec_version', '-', """{}""".format(python_decrease))
    wn.addKnob(decrease_knob)
    increase_knob = nuke.PyScript_Knob('inc_version', '+', """{}""".format(python_increase))
    wn.addKnob(increase_knob)
    delete_knob = nuke.PyScript_Knob('del_version', 'delete', """{}""".format(python_delete))
    wn.addKnob(delete_knob)

    # create OUT dot
    wn_name = wn.name()
    dt_out = nuke.createNode('Dot', inpanel=False)
    dt_out.setXYpos(dt_xpos, dt_ypos + 60)
    dt_out.setInput(0, dt_node)
    dt_out['name'].setValue(wn_name + '_OUT')
    dt_out['label'].setValue('OUT')
    
    # write bits
    if sel_bits == '16 bit':
        wn['datatype'].setValue('16 bit half')
    elif sel_bits == '32 bit':
        wn['datatype'].setValue('32 bit float')

    # create backdrop and backdrop class
    bckDp = create_backdrop([dt_node, wn, dt_out])
    class_btn = nuke.Text_Knob('class', 'class')
    bckDp.addKnob(class_btn)
    class_btn.setValue(wn_name + '_back')

    # set after render knob
    wn['afterRender'].setValue(python_set_read)


def set_deepwrite_node(dt_node, cacheNameTxt, maskButtons, bitsButtons, writeBtns):
    # file path
    cf, cn = get_cache_file(cacheNameTxt, writeBtns)
    sel_channels = get_selected_channels_opt(maskButtons)
    sel_bits = get_selected_bits_opt(bitsButtons)

    # create a write node and connect it to the dot
    dt_xpos = int(dt_node.xpos())
    dt_ypos = int(dt_node.ypos())
    wn = nuke.createNode("DeepWrite", inpanel=False)
    wn.setXYpos(dt_xpos - 180, dt_ypos - 20) # write node position
    wn.setInput(0, dt_node)
    wn['tile_color'].setValue(0x9e6182ff)
    wn['label'].setValue('cache')
    wn['file'].setValue(cf)
    wn['channels'].setValue(sel_channels.lower())
    wn['file_type'].setValue('exr')

    # create write cache tab
    cache_tab = nuke.Tab_Knob('cache_tab','cache')
    wn.addKnob(cache_tab)

    # add cache knobs
    cache_name_knob = nuke.Text_Knob('currName', 'name')
    cache_name_knob.setValue(cn)
    wn.addKnob(cache_name_knob)
    cache_version_knob = nuke.Text_Knob('currVersion', 'version')
    cache_version_knob.setValue('v001')
    wn.addKnob(cache_version_knob)
    div_knob = nuke.Text_Knob('div', '')
    wn.addKnob(div_knob)
    which_knob = nuke.Int_Knob('which', 'which')
    which_knob.setValue(1)
    wn.addKnob(which_knob)
    decrease_knob = nuke.PyScript_Knob('dec_version', '-', """{}""".format(python_decrease))
    wn.addKnob(decrease_knob)
    increase_knob = nuke.PyScript_Knob('inc_version', '+', """{}""".format(python_increase))
    wn.addKnob(increase_knob)
    delete_knob = nuke.PyScript_Knob('del_version', 'delete', """{}""".format(python_delete))
    wn.addKnob(delete_knob)

    # create OUT dot
    wn_name = wn.name()
    dt_out = nuke.createNode('Dot', inpanel=False)
    dt_out.setXYpos(dt_xpos, dt_ypos + 60)
    dt_out.setInput(0, dt_node)
    dt_out['name'].setValue(wn_name + '_OUT')
    dt_out['label'].setValue('OUT')
    
    # write bits
    if sel_bits == '16 bit':
        wn['datatype'].setValue('16 bit half')
    elif sel_bits == '32 bit':
        wn['datatype'].setValue('32 bit float')

    # create backdrop and backdrop class
    bckDp = create_backdrop([dt_node, wn, dt_out])
    class_btn = nuke.Text_Knob('class', 'class')
    bckDp.addKnob(class_btn)
    class_btn.setValue(wn_name + '_back')

    # set after render knob
    wn['afterRender'].setValue(python_set_read)


def set_geowrite_node(dt_node, cacheNameTxt, writeBtns):
    # file path
    cf, cn = get_cache_file(cacheNameTxt, writeBtns)

    # create a write node and connect it to the dot
    dt_xpos = int(dt_node.xpos())
    dt_ypos = int(dt_node.ypos())
    wn = nuke.createNode("WriteGeo", inpanel=False)
    wn.setXYpos(dt_xpos - 180, dt_ypos - 14) # write node position
    wn.setInput(0, dt_node)
    wn['tile_color'].setValue(0x9e6182ff)
    wn['label'].setValue('cache')
    wn['file'].setValue(cf)
    wn['file_type'].setValue('abc')

    # create write cache tab
    cache_tab = nuke.Tab_Knob('cache_tab','cache')
    wn.addKnob(cache_tab)

    # add cache knobs
    cache_name_knob = nuke.Text_Knob('currName', 'name')
    cache_name_knob.setValue(cn)
    wn.addKnob(cache_name_knob)
    cache_version_knob = nuke.Text_Knob('currVersion', 'version')
    cache_version_knob.setValue('v001')
    wn.addKnob(cache_version_knob)
    div_knob = nuke.Text_Knob('div', '')
    wn.addKnob(div_knob)
    which_knob = nuke.Int_Knob('which', 'which')
    which_knob.setValue(1)
    wn.addKnob(which_knob)
    decrease_knob = nuke.PyScript_Knob('dec_version', '-', """{}""".format(python_decrease))
    wn.addKnob(decrease_knob)
    increase_knob = nuke.PyScript_Knob('inc_version', '+', """{}""".format(python_increase))
    wn.addKnob(increase_knob)
    delete_knob = nuke.PyScript_Knob('del_version', 'delete', """{}""".format(python_delete))
    wn.addKnob(delete_knob)

    # create OUT dot
    wn_name = wn.name()
    dt_out = nuke.createNode('Dot', inpanel=False)
    dt_out.setXYpos(dt_xpos, dt_ypos + 60)
    dt_out.setInput(0, dt_node)
    dt_out['name'].setValue(wn_name + '_OUT')
    dt_out['label'].setValue('OUT')

    # create backdrop and backdrop class
    bckDp = create_backdrop([dt_node, wn, dt_out])
    class_btn = nuke.Text_Knob('class', 'class')
    bckDp.addKnob(class_btn)
    class_btn.setValue(wn_name + '_back')

    # set after render knob
    wn['afterRender'].setValue(python_set_read)


def set_particlecache_node(dt_node, cacheNameTxt, writeBtns):
    # file path
    cf, cn = get_cache_file(cacheNameTxt, writeBtns)

    # create a write node and connect it to the dot
    dt_xpos = int(dt_node.xpos())
    dt_ypos = int(dt_node.ypos())
    wn = nuke.createNode("ParticleCache", inpanel=False)
    wn.setXYpos(dt_xpos - 180, dt_ypos - 8) # write node position
    wn.setInput(0, dt_node)
    wn['tile_color'].setValue(0x9e6182ff)
    wn['label'].setValue('cache')
    wn['file'].setValue(cf)

    # create write cache tab
    cache_tab = nuke.Tab_Knob('cache_tab','cache')
    wn.addKnob(cache_tab)

    # add cache knobs
    cache_name_knob = nuke.Text_Knob('currName', 'name')
    cache_name_knob.setValue(cn)
    wn.addKnob(cache_name_knob)
    cache_version_knob = nuke.Text_Knob('currVersion', 'version')
    cache_version_knob.setValue('v001')
    wn.addKnob(cache_version_knob)
    div_knob = nuke.Text_Knob('div', '')
    wn.addKnob(div_knob)
    which_knob = nuke.Int_Knob('which', 'which')
    which_knob.setValue(1)
    wn.addKnob(which_knob)
    decrease_knob = nuke.PyScript_Knob('dec_version', '-', """{}""".format(python_decrease))
    wn.addKnob(decrease_knob)
    increase_knob = nuke.PyScript_Knob('inc_version', '+', """{}""".format(python_increase))
    wn.addKnob(increase_knob)
    delete_knob = nuke.PyScript_Knob('del_version', 'delete', """{}""".format(python_delete))
    wn.addKnob(delete_knob)

    # create OUT dot
    wn_name = wn.name()
    dt_out = nuke.createNode('Dot', inpanel=False)
    dt_out.setXYpos(dt_xpos, dt_ypos + 60)
    dt_out.setInput(0, dt_node)
    dt_out['name'].setValue(wn_name + '_OUT')
    dt_out['label'].setValue('OUT')

    # create backdrop and backdrop class
    bckDp = create_backdrop([dt_node, wn, dt_out])
    class_btn = nuke.Text_Knob('class', 'class')
    bckDp.addKnob(class_btn)
    class_btn.setValue(wn_name + '_back')

    # set after render knob
    wn['afterRender'].setValue(python_set_read)


def get_selected_write_opt(writeBtns):
    for btn in writeBtns:
        if btn.isChecked():
            return btn.text()


def get_selected_channels_opt(maskButtons):
    for btn in maskButtons:
        if btn.isChecked():
            return btn.text()


def get_selected_bits_opt(bitsButtons):
    for btn in bitsButtons:
        if btn.isChecked():
            return btn.text()
        

def onSubmit(window, cacheNameTxt, writeBtns, maskButtons, bitsButtons):
    window.close()
    sn = nuke.selectedNode()
    sn_xpos = int(sn.xpos())
    sn_ypos = int(sn.ypos())
    sel_write = get_selected_write_opt(writeBtns)
        
    # create IN dot
    dt_node = nuke.createNode("Dot", inpanel=False)
    dt_node.setXYpos(sn_xpos + 34, sn_ypos  + 180)
    dt_node.setInput(0, sn)
    dt_node['label'].setValue('IN')

    # get the selected write node
    if sel_write == 'Write':
        set_write_node(dt_node, cacheNameTxt, maskButtons, bitsButtons, writeBtns)
    elif sel_write == 'DeepWrite':
        set_deepwrite_node(dt_node, cacheNameTxt, maskButtons, bitsButtons, writeBtns)
    elif sel_write == 'GeoWrite':
        set_geowrite_node(dt_node, cacheNameTxt, writeBtns)
    elif sel_write == 'ParticleCache':
        set_particlecache_node(dt_node, cacheNameTxt, writeBtns)


def onReject(window):
    window.close()


def select_write(window, sender, maskButtons, bitsButtons):
    #logica
    if window.previous_write_btn and window.previous_write_btn != sender:
        window.previous_write_btn.setChecked(False)

    sender.setChecked(True)

    window.previous_write_btn = sender

    if sender.objectName() == 'geoBtn' or sender.objectName() == 'particleBtn':
        for btn in maskButtons:
            btn.setEnabled(False)
            btn.setChecked(False)
        for btn in bitsButtons:
            btn.setEnabled(False)
            btn.setChecked(False)
    else:
        window.previous_mask_btn.setChecked(True)
        window.previous_bit_btn.setChecked(True)
        for btn in maskButtons:
            btn.setEnabled(True)
        for btn in bitsButtons:
            btn.setEnabled(True)


def select_mask(window, sender):
    #logica
    if window.previous_mask_btn and window.previous_mask_btn != sender:
        window.previous_mask_btn.setChecked(False)

    sender.setChecked(True)

    window.previous_mask_btn = sender


def select_bits(window, sender):
    #logica
    if window.previous_bit_btn and window.previous_bit_btn != sender:
        window.previous_bit_btn.setChecked(False)

    sender.setChecked(True)

    window.previous_bit_btn = sender


def CompCacheWindow():
    window = MainUI()
    window.show()