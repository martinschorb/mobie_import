# -*- coding: utf-8 -*-
# import the py-EM module and make its functions available
import pyEM as em

import xml.etree.ElementTree as ET


# import sys
import os
import glob
import numpy as np
import tkinter as tk
from tkinter import filedialog

import pybdv


#======================================
            
def write_bdv(outname,data,view,blow_2d=1,outf='.h5'):
    
    outfile = os.path.join('bdv',outname)   
        
    

    ndim = data.ndim
    if ndim > 2: assert ndim == 3, "Only support 3d"
        #assert len(resolution) == ndim
    if ndim < 3: 
        assert ndim == 2, "Only support 2d"
        data=np.expand_dims(data.copy(),axis=0)
        
        
#            data1=np.concatenate((d1,d1),axis=0)
        
        if data.dtype.kind=='i':
            if data.dtype.itemsize == 1:
                data0 = np.uint8(data-data.min())
                view['attributes']['displaysettings']['min']='0'
                view['attributes']['displaysettings']['max']=str(int(view['attributes']['displaysettings']['max'])-data.min())
            elif data.dtype.itemsize == 2:
                data0 = np.uint16(data-data.min())
                view['attributes']['displaysettings']['min']='0'
                view['attributes']['displaysettings']['max']=str(int(view['attributes']['displaysettings']['max'])-data.min())
            else:
                data0 = np.uint16((data-data.min())/data.max()*65535)
                view['attributes']['displaysettings']['min']='0'
                view['attributes']['displaysettings']['max']='65535'
        else:
            data0 = data.copy()
        
        
    print('Converting map '+outname+' into BDV format ' +outf+'.')
    
    pybdv.make_bdv(data0,outfile,downscale_factors,
                       resolution = view['resolution'],
                       unit = bdv_unit, 
                       setup_id = view['setup_id'],
                       timepoint = timept,
                       setup_name = view['setup_name'],
                       attributes = view['attributes'],
                       affine = view['trafo'],
                       overwrite = 'metadata')
        
#%%

cwd = os.getcwd()

tk_root = tk.Tk()
tk_root.withdraw()
tk_root.wm_attributes("-topmost", 1)

tiles = False
numtiles = 1
itemname='-'
# skip integration into BDV->Icy->BDV as Icy cannot read bdv files (yet).

exist_bdv = tk.messagebox.askyesno(title = 'Select input files',message='Is the fixed image (EM) already registered in BDV?',parent = tk_root)

if exist_bdv:
    messg1 = tk.messagebox.showinfo(title = 'Select BDV XML', message = 'Select BDV description XML for fixed data (usually EM).',parent = tk_root)
    bdvxml_em = filedialog.askopenfilename(title = 'Select BDV XML of fixed image (EM).', filetypes = [('XML','*.xml')], initialdir = cwd,parent = tk_root)
    
    bdv_em_root = ET.parse(bdvxml_em)
    
    seqdes = bdv_em_root.find('SequenceDescription')
    vs0 = seqdes.find('ViewSetups')
    atts = vs0.findall('Attributes')
    
    vs = vs0.findall('ViewSetup')   
    
    itemname = os.path.splitext(os.path.basename(bdvxml_em))[0]
        
    for attribute in atts:
        if 'tile' in attribute.attrib.values():
            tiles = True
            numtiles = len(attribute)
            
            tile_setup = list()
            
            # find tile id for any VS id
            
            for viewsetup in vs:
                vs_id = viewsetup.find('id').text
                vs_attr = viewsetup.find('attributes')
                
                vs_tile = int(vs_attr.find('tile').text)
                
                tile_setup.append([vs_tile,vs_id])
                
 
tiletxt = '.'

if tiles: tiletxt = '. Use the original tiled (not stitched) montage file.'       

messg2 = tk.messagebox.showinfo(title = 'Select fixed (EM) image', message = 'Select fixed image (usually EM)'+tiletxt,parent = tk_root)
emf = filedialog.askopenfilename(title = 'Select fixed image (usually EM)',filetypes = [('images',('*.tif' , '*.tiff', '*.idoc','*.mrc','*.map','*.st'))], initialdir = cwd,parent = tk_root)

# prepare nav-like entry for merging

mapitem = dict()
mapitem['MapScaleMat']=['1.0','0.0','0.0','1.0']
mapitem['MapFile']=[emf]
mapitem['MapSection']=['0']
mapitem['MapFramesXY']=['1',str(numtiles)]
mapitem['MontBinning']=['1']
mapitem['MapBinning']=['1']
mapitem['# Item']=itemname
mapitem['MapWidthHeight']=[0,0]
mapitem['StageXYZ']=[0,0,0]


# merge EM file 
merged = em.mergemap(mapitem,blendmont=False)
em_str = ''


if merged['mapheader']['stacksize'] > 1:
    tiles=True   
    
    tk_root2 = tk.Tk()
    tk_root2.withdraw()
    answer = tk.simpledialog.askstring("Which slice?", "Select montage slice (starting from 0),\n if you leave the field empty, the montage will be merged.")
    
    try:
        slice = int(answer)
        data_em = merged['im'][:,:,slice]
        em_str = '_s' + answer
        
    except ValueError:
        if answer == '':
            merged = em.mergemap(mapitem,blendmont=True)
        else:
            print("Could not convert input to an integer.")
        
    
else:
     data_em = merged['im']
    
tk_root2 = tk.Tk()
tk_root2.withdraw()
tk_root2.wm_attributes("-topmost", 1)

messg3 = tk.messagebox.showinfo(title = 'Select moving (FM) image', message = 'Select image that you want to register (usually FM).',parent = tk_root2)
fmf = filedialog.askopenfilename(title = 'Select fixed image (usually EM)',filetypes = [('images',('*.tif' , '*.tiff', '*.idoc','*.mrc','*.map','*.st'))], initialdir = cwd,parent = tk_root2)








# import icy XMLs

# x_emf = merged['mergefile'] + '_ROIsavedwhenshowonoriginaldata' + '.xml'
x_trafo = fmf + '_transfo' + '.xml'

if not os.path.exists(x_trafo):  raise ValueError('Could not find the results of Icy registration. Please re-run.')
    
root_trafo = ET.parse(x_trafo)

# extract transformation matrices

mat = []
if root_trafo.find('MatrixTransformation') == None:
    root_trafo = ET.parse(glob.glob(fmf + '_transfo' + '*back-up.xml')[-1])


for child in root_trafo.iter():
    if child.tag == 'MatrixTransformation':
        mat.append(child.attrib)

M = np.eye(4)
M_list = list()

for matrix in mat:
    thismat = np.eye(4)
    thismat[0,0] = matrix['m00']
    thismat[0,1] = matrix['m01']
    thismat[0,2] = matrix['m02']
    thismat[0,3] = matrix['m03']
    thismat[1,0] = matrix['m10']
    thismat[1,1] = matrix['m11']
    thismat[1,2] = matrix['m12']
    thismat[1,3] = matrix['m13']
    thismat[2,0] = matrix['m20']
    thismat[2,1] = matrix['m21']
    thismat[2,2] = matrix['m22']
    thismat[2,3] = matrix['m23']
    thismat[3,0] = matrix['m30']
    thismat[3,1] = matrix['m31']
    thismat[3,2] = matrix['m32']
    thismat[3,3] = matrix['m33']
    
    M_list.append(thismat)
    
    M = np.dot(M.T,thismat)
    




# write EM data


setup_id = 0

pxs = 1

view=dict()
                    
view['resolution'] = [pxs,pxs,pxs]
view['setup_id'] = setup_id
view['setup_name'] = 'EM_' +  os.path.basename(emf)

view['attributes'] = dict()                       

view['attributes']['displaysettings'] = dict({'id':setup_id,'color':colors['_W'],'isset':'true'})
view['attributes']['displaysettings']['Projection_Mode'] = 'Average'
view['attributes']['displaysettings']['min']=item['MapMinMaxScale'][0]
view['attributes']['displaysettings']['max']=item['MapMinMaxScale'][1]

view['trafo'] = dict()
view['trafo']['Translation'] = tf_tr
view['trafo']['MapScaleMat'] = tf_sc



write_bdv(outname,data,view)

