# -*- coding: utf-8 -*-

import numpy as np
import pybdv
import xml.etree.ElementTree as ET
from pybdv import transformations as tf

colors=dict()

colors['R'] = '255 0 0 255'
colors['G'] = '0 255 0 255'
colors['B'] = '0 0 255 255'
colors['W'] = '255 255 255 255'
colors['BF'] = '255 255 255 255'


# functions to help playing with BDV 


def write_fast_xml(outname,views):   
    
    
    
     # write top-level data
    root = ET.Element('SpimData')
    root.set('version', '0.2')
    bp = ET.SubElement(root, 'BasePath')
    bp.set('type', 'relative')
    bp.text = '.'

    # make the sequence description element
    seqdesc = ET.SubElement(root, 'SequenceDescription')    
    
    
    # make the image loader
    imgload = ET.SubElement(seqdesc, 'ImageLoader')    
    imgload.set('format', 'spimreconstruction.filelist')
    il2c = ET.SubElement(imgload,'imglib2container')
    il2c.text = 'ArrayImgFactory'
    zg = ET.SubElement(imgload,'ZGrouped')
    zg.text = 'false'
    
    files = ET.SubElement(imgload,'files')
    
    # make the view descriptions
    viewsets = ET.SubElement(seqdesc, 'ViewSetups')
    
    # timepoint description
    tpoints = ET.SubElement(seqdesc, 'Timepoints')
    tpoints.set('type', 'range')
    ET.SubElement(tpoints, 'first').text = '0'
    ET.SubElement(tpoints, 'last').text = '0'
    
    # make the registration decriptions
    vregs = ET.SubElement(root, 'ViewRegistrations')
    
    # Some more stuff that BigStitcher has. Maybe it's needed
    # MiV = ET.SubElement(seqdesc, 'MissingViews')
    # Vip = ET.SubElement(root, 'ViewInterestPoints')
    # BBx = ET.SubElement(root, 'BoundingBoxes')
    # PSF = ET.SubElement(root, 'PointSpreadFunctions')
    # StR = ET.SubElement(root, 'StitchingResults')
    # InA = ET.SubElement(root, 'IntensityAdjustments')
    
    pybdv.metadata._initialize_attributes(viewsets, views[0]['attributes'])    
        
    for thisview in views:
        pybdv.metadata._update_attributes(viewsets, thisview['attributes'])
        
        thisFMap = ET.SubElement(files,'FileMapping')
        thisFMap.set("view_setup",str(thisview['setup_id']))
        thisFMap.set("timepoint",'0')
        thisFMap.set("series",'0')
        
        if 'channel' in thisview['attributes'].keys():
            thisFMap.set("channel",str(thisview['attributes']['channel']))
        else:
            thisFMap.set("channel",'0')          
        
        thisfile = ET.SubElement(thisFMap,'file')
        thisfile.set("type","relative")
        thisfile.text = thisview['file']
        
        if not 'setup_name' in thisview.keys():
            thisview['setup_name']=str(thisview['setup_id'])
        
        # write view setup
        pybdv.metadata._require_view_setup(viewsets,thisview['setup_id'],thisview['setup_name'],thisview['resolution'],thisview['size'],thisview['attributes'],'nm',False)
        # write transformation(s)
        pybdv.metadata._write_affine(vregs,thisview['setup_id'],'0',thisview['trafo'])

        # write the xml
    pybdv.metadata.indent_xml(root)
    tree = ET.ElementTree(root)
    tree.write(outname,encoding="UTF-8",xml_declaration=True)
        






#======================================
            
def write_bdv(outfile,data,view,blow_2d=1,outf='.h5',downscale_factors = None,timept=0,bdv_unit='um'):

    ndim = data.ndim
    if ndim > 2: assert ndim == 3, "Only support 3d"
        #assert len(resolution) == ndim
    if ndim < 3: 
        assert ndim == 2, "Only support 2d"
        data=np.expand_dims(data.copy(),axis=0)
        

#            data1=np.concatenate((d1,d1),axis=0)
    
    if data.dtype.kind=='i':
        if data.dtype.itemsize == 1:
            data1 = np.uint8(data-data.min())
            view['attributes']['displaysettings']['min']='0'
            view['attributes']['displaysettings']['max']=str(int(view['attributes']['displaysettings']['max'])-data.min())
        elif data.dtype.itemsize == 2:
            data1 = np.uint16(data-data.min())
            view['attributes']['displaysettings']['min']='0'
            view['attributes']['displaysettings']['max']=str(int(view['attributes']['displaysettings']['max'])-data.min())
    else:
        data1 = np.uint16((data-data.min())/data.max()*65535)
        view['attributes']['displaysettings']['min']='0'
        view['attributes']['displaysettings']['max']='65535'
    
        
   # print('Converting map '+outfile+' into BDV format ' +outf+'.')
    
    pybdv.make_bdv(data1,outfile,downscale_factors,
                       resolution = view['resolution'],
                       unit = bdv_unit, 
                       setup_id = view['setup_id'],
                       timepoint = timept,
                       setup_name = view['setup_name'],
                       attributes = view['attributes'],
                       affine = view['trafo'],
                       overwrite = 'metadata')
    
    if 'OriginalFile' in view.keys():
        
        xml_path = outfile + '.xml'
        
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        if not root.find('OriginalFile') == None:
            origf = root.find('OriginalFile')
        else:
            origf = ET.SubElement(root, 'OriginalFile')
            
        origf.text = view['OriginalFile']
        
        # write the xml
        tf.indent_xml(root)
        tree = ET.ElementTree(root)
        tree.write(xml_path)