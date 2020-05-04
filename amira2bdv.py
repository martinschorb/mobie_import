#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy as np
import pyEM as em

import pybdv
from pybdv import transformations as tf
import mrcfile as mrc
import os
from skimage import io

bdv_unit = 'um'


# if individual BDV data files should be created for every Amira data object. I false, all will end up in one file.
split_files = True 

mrcl = ['mrc','st','rec','join','map']


timept = 0

colors=dict()

colors['_R'] = '255 0 0 255'
colors['_G'] = '0 255 0 255'
colors['_B'] = '0 0 255 255'
colors['_W'] = '255 255 255 255'
colors['BF'] = '255 255 255 255'

outformat='.h5'

downscale_factors = list(([1,2,2],[1,2,2],[1,2,2],[1,4,4]))
blow_2d = 1


#%%
#=======================================

outname = os.path.basename(os.getcwd())

setup_id = -1


for tf_file in os.listdir():
    # work on all tform files exported from Amira
    if not tf_file[-5:] == 'tform':
        continue
    else:
        setup_id = setup_id + 1
        
        # set output
        if split_files:
                setup_id = 0
                basename = os.path.basename(tf_file)
                outname = basename[:basename.rindex(os.path.extsep)]   
                       
                
        #get and parse transform file              
        tfile = em.loadtext(tf_file)  
        
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
        files = tfile[5].split(' ')
        
        
        
#        ------------------------------------------------
        
        
        
        
        bbox_0 = bbox/np.repeat(voxs,2)
        
        bbox_n = bbox_0.copy()
        bbox_n[0]=0;bbox_n[2]=0;bbox_n[4]=0
        bbox_n[1]=bbox_n[1]-bbox_0[0];bbox_n[3]=bbox_n[3]-bbox_0[2];bbox_n[5]=bbox_n[5]-bbox_0[4]
        
               
        
        if len(files)<2:
            im_file = files[0]
            # single file for the volume or 2D data
            if 'tif' in im_file[im_file.rindex(os.path.extsep):]:
                data = io.imread(im_file)
            elif any(ext in im_file for ext in mrcl):
                data = mrc.mmap(im_file).data
                
                
                
        else:
            # list of slices as a stack
            data = [];
            
            for im_file in files:            
                if 'tif' in im_file[im_file.rindex(os.path.extsep):]:
                    data0 = io.imread(im_file)
                    if len(data)==0:
                        data = np.expand_dims(data0.copy(),axis=0)
                    else:
                        data = np.concatenate((data,np.expand_dims(data0.copy(),axis=0)),axis=0)
            

            
            
        
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
     
             

       
        
        outfile = os.path.join('bdv',outname+outformat) 
        
            
    
        ndim = data.ndim
        if ndim > 2: assert ndim == 3, "Only support 3d"
            #assert len(resolution) == ndim
        if ndim < 3: 
            assert ndim == 2, "Only support 2d"
            data=np.expand_dims(data.copy(),axis=0)
        
        
        pybdv.make_bdv(data1,outfile,downscale_factors,
                   resolution = view['resolution'],
                   unit = bdv_unit, 
                   setup_id = view['setup_id'],
                   timepoint = timept,
                   setup_name = view['setup_name'],
                   attributes = view['attributes'],
                   affine = view['trafo'],
                   overwrite = 'all')
        
        
        
                
                
            
    
                
