#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy as np

import pybdv
from pybdv import transformations as tf
import mrcfile as mrc
import os
from skimage import io
import sys
from shutil import copy

import xml.etree.ElementTree as ET

from tkinter import Tk,messagebox,filedialog


bdv_unit = 'um'

ov_mode = 'metadata'

# if individual BDV data files should be created for every Amira data object. I false, all will end up in one file.
split_files = True 

mrcl = ['mrc','st','rec','join','map']

ski_types = ['tif','png']

ov_data = ['data','all']


timept = 0

colors=dict()

colors['_R'] = '255 0 0 255'
colors['_G'] = '0 255 0 255'
colors['_B'] = '0 0 255 255'
colors['_W'] = '255 255 255 255'
colors['BF'] = '255 255 255 255'

outformat='.h5'

downscale_factors = list(([2,2,2],[2,2,2],[2,2,2],[2,2,2],[2,2,2],[2,2,2]))
blow_2d = 1


outname = os.path.basename(os.getcwd())

setup_id = -1


dirname = 'bdv_amira'


#%%
# filelist =  os.listdir()

# list_file = sys.argv[1]
root0=Tk()
root0.withdraw()
root0.wm_attributes("-topmost", 1)

mb1=messagebox.showinfo("Please select Amira output","Please select the Amira output file to start the conversion.\n",parent = root0)
list_file = filedialog.askopenfilename(initialdir = outname,title = "Select Amira output file",filetypes = {"Transform .list"}, parent = root0)
                   

#%%


if os.path.exists(list_file):
    with open(list_file) as f:
        filelist = f.read().splitlines()
else:
    print('ERROR: transformation list file not found!!')
    exit()

if not os.path.exists(dirname):
    os.makedirs(dirname)
    
for tf_file in filelist:
    # work on all tform files exported from Amira
    if not tf_file[-5:] == 'tform':
        continue
    else:
        setup_id = setup_id + 1
        
        print(' ----------------------------------------------\n      Converting image transform: '+tf_file)
        
        
        # set output
        if split_files:
                setup_id = 0
                basename = os.path.basename(tf_file)
                outname = basename[:basename.rindex(os.path.extsep)]   
                       
                
        #get and parse transform file 
        f = open(tf_file, 'r')
        tfile = f.read().splitlines() 
        f.close()               
        
        # import transform       
        tform = np.array(list(map(float,tfile[0].split(','))))    
        tform = np.reshape(tform,[4,4])
        
        #import BoundingBox
        bbox = np.array(list(map(float,tfile[1].split(','))))
        
        #import voxel size
        voxs = np.array(list(map(float,tfile[2].split(','))))    
        
        # import translation
        trans_0 = np.array(list(map(float,tfile[3].split(','))))  
        
        # import lattice info (double check properties)
        latt = np.array(list(map(float,tfile[4].split(',')[0].split(' x '))))
        
        #import file list        
        files = tfile[5].split(' , ')

        
#        ------------------------------------------------
        
        
        
        
        bbox_0 = bbox/np.repeat(voxs,2)
        
        bbox_n = bbox_0.copy()
        bbox_n[0]=0;bbox_n[2]=0;bbox_n[4]=0
        bbox_n[1]=bbox_n[1]-bbox_0[0];bbox_n[3]=bbox_n[3]-bbox_0[2];bbox_n[5]=bbox_n[5]-bbox_0[4]
        
               
         
        
        # compensate with initial translation (when opening Amira)
        
        trans = np.array([bbox[1],bbox[3],bbox[5]])/2 + trans_0
        
        
        # set up translation matrix
        
        mat_t = np.concatenate((np.eye(3),np.array([[trans[0]],[trans[1]],[trans[2]]])),axis=1)
        mat_t = np.concatenate((mat_t,[[0,0,0,1]]))
        
        tf_tr = tf.matrix_to_transformation(mat_t).tolist()
        
        
        #compensate data origin:
        
        trans_or = - np.array([bbox_0[1],bbox_0[3],bbox_0[5]])/2
        
        
        mat_or = np.concatenate((np.eye(3),trans_or.reshape((3,1))),axis=1)
        mat_or = np.concatenate((mat_or,[[0,0,0,1]]))
        tf_or = tf.matrix_to_transformation(mat_or).tolist()
        
        
        
        # make transformation matrix available
        tform1 =  tform.T * np.append(voxs,1)
        tf_tform = tf.matrix_to_transformation(tform1).tolist()
        
        # write BDV data         
            
        view=dict()
                            
        view['resolution'] = [voxs[0],voxs[2],voxs[1]]
        view['setup_id'] = setup_id
        view['setup_name'] = outname
        
        view['attributes'] = dict()                       
        
        view['trafo'] = dict()       
        
        view['trafo']['Amira_Translation'] = tf_tr
        view['trafo']['Amira_Transform'] = tf_tform     
        view['trafo']['Amira_Origin_Translation'] = tf_or
    
       
        
        
        outfile = os.path.join(dirname,outname+outformat) 
        
        
        data = []
            
        if len(files)<2:
            im_file = files[0]
            # single file for the volume or 2D data
            if '.xml.bin' in tf_file:
                # downsampled data from original BDV source
                binning = int(tf_file[tf_file.find('.xml.bin') + 8])
                tform[0:3,0:3] = 1 / binning * tform[0:3,0:3] 
                
                tform1 =  tform.T * np.append(voxs,1)
                tf_tform = tf.matrix_to_transformation(tform1).tolist()
                
                view['trafo']['Amira_Transform'] = tf_tform
                
                trans =  1 / binning * trans
                
                mat_t = np.concatenate((np.eye(3),np.array([[trans[0]],[trans[1]],[trans[2]]])),axis=1)
                mat_t = np.concatenate((mat_t,[[0,0,0,1]]))
        
                tf_tr = tf.matrix_to_transformation(mat_t).tolist()
                
                view['trafo']['Amira_Translation'] = tf_tr
                
                xml_orig = im_file[0:im_file.find('.xml.bin') + 4]
                
                
                
                if os.path.exists(xml_orig):
                    # check original bdv xml file for data location
                    ov_mode = 'metadata'
                    tree = ET.parse(xml_orig)
                    root = tree.getroot() 
                    # load the file location
                    base_path = root.find('BasePath').text
                    if base_path=='.': base_path=''                   
                    seqdesc = root.find('SequenceDescription')                   
                    imload = seqdesc.find('ImageLoader')                        
                    im_format = imload.attrib['format']                   
                    im_desc = imload[0]
                    
                    data_path = '/'.join([os.path.dirname(im_file),base_path, im_desc.text])
                    
                    is_h5=False
                    
                    if outformat=='.h5': is_h5=True
                    
                    
                    if os.access(xml_orig,os.W_OK):
                        # if data locatin is writable, create new file here
                        outname = im_file[0:im_file.find('.xml.bin')]+'_amira'                       
                        
                        
                    else:
                        # create new xml file in current directory linking to the original data
                        cwd = os.getcwd()
                        #
                        outname = os.path.join(cwd,dirname,os.path.basename(im_file[0:im_file.find('.xml.bin')]+'_amira'))
                        #
                        try:
                            com_path = os.path.commonpath([cwd,xml_orig])
                            rel_path = os.path.relpath(os.path.dirname(xml_orig),cwd)
                        except ValueError:
                            rel_path = "."
                            im_orig = os.path.splitext(xml_orig)[0]+outformat
                            newim =  os.path.join(cwd,dirname,os.path.basename(im_orig))
                            if not os.path.exists(newim): copy(im_orig,newim)
                            
                        xml_dir = '/'.join(rel_path.split(os.path.sep))
                        
                        if xml_dir[0]=='/': xml_dir=xml_dir[1:]
                        
                        data_path = '/'.join([xml_dir,dirname,base_path, im_desc.text])                        
                                                
                        
                    pybdv.metadata.write_xml_metadata(outname + '.xml', data_path,
                                                          resolution = view['resolution'],
                                                          unit = bdv_unit,setup_id = view['setup_id'],
                                                          timepoint = timept,setup_name = view['setup_name'],
                                                          attributes = view['attributes'],
                                                          affine = view['trafo'],
                                                          overwrite = True,
                                                          is_h5=is_h5,
                                                          overwrite_data=False,
                                                          enforce_consistency=True)
                else:
                    
                    cwd = os.getcwd()
                    
                    root=Tk()
                    root.withdraw()
                    
                    mb=messagebox.showinfo("Original data not found","Could not find the original data location.\n\n Please select the BDV xml file of the original dataset:\n   - "+xml_orig)
                    origxml = filedialog.askopenfilename(initialdir = cwd,title = "Select original data file -- "+xml_orig,filetypes = {"XML .xml"})
                    
                    root.destroy()                    
                    
                    
                    ov_mode = 'metadata'
                    tree = ET.parse(origxml)
                    root = tree.getroot() 
                    # load the file location
                    base_path = root.find('BasePath').text
                    if base_path=='.': base_path=''                   
                    seqdesc = root.find('SequenceDescription')                   
                    imload = seqdesc.find('ImageLoader')                        
                    im_format = imload.attrib['format']                   
                    im_desc = imload[0]
                    
                    
                        #
                    com_path = os.path.commonpath([cwd,origxml])
                    #
                    rel_path = os.path.relpath(os.path.dirname(origxml),cwd)
                    xml_dir = '/'.join(rel_path.split(os.path.sep))
                    
                    if xml_dir[0]=='/': xml_dir=xml_dir[1:]
                    
                    data_path = '/'.join([xml_dir,base_path, im_desc.text])
                    
                    is_h5=False
                    
                    if outformat=='.h5': is_h5=True
                    
                    pybdv.metadata.write_xml_metadata(outname + '.xml', data_path,
                                                          resolution = view['resolution'],
                                                          unit = bdv_unit,setup_id = view['setup_id'],
                                                          timepoint = timept,setup_name = view['setup_name'],
                                                          attributes = view['attributes'],
                                                          affine = view['trafo'],
                                                          overwrite = True,
                                                          is_h5=is_h5,
                                                          overwrite_data=False,
                                                          enforce_consistency=True)
                    
 
               # outname = tf_file[0:tf_file.find('.xml.bin')]
               # data = [];
                
            elif any(ext in os.path.basename(im_file) for ext in ski_types):
                data = io.imread(im_file)
            elif any(ext in os.path.basename(im_file) for ext in mrcl):
                data = mrc.mmap(im_file).data
                
                
                
        else:
            # list of slices as a stack
            if ((ov_mode in ov_data) | os.path.exists(outfile)==False):                
                # check if bdv data already exists
                for im_file in files:            
                    if any(ext in os.path.basename(im_file) for ext in ski_types):
                        print('Reading image data from: ' + im_file)
                        data0 = io.imread(im_file)
                        if len(data)==0:
                            data = np.expand_dims(data0.copy(),axis=0)
                        else:
                            data = np.concatenate((data,np.expand_dims(data0.copy(),axis=0)),axis=0)                
            else:
                data = np.zeros([1,1,1])

        if len(data)>0:
            ndim = data.ndim
            if ndim > 2: assert ndim == 3, "Only support 3d"
                #assert len(resolution) == ndim
            if ndim < 3: 
                assert ndim == 2, "Only support 2d"
                data=np.expand_dims(data.copy(),axis=0)
            
            print('Writing BDV output data for '+outfile)
            pybdv.make_bdv(data,outfile,downscale_factors,
                       resolution = view['resolution'],
                       unit = bdv_unit, 
                       setup_id = view['setup_id'],
                       timepoint = timept,
                       setup_name = view['setup_name'],
                       attributes = view['attributes'],
                       affine = view['trafo'],
                       overwrite = ov_mode)
            
        
        
                
                
            
    
                
