#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 16:26:45 2019

@author: schorb
"""

import numpy as np
import pyEM as em
import os

import pybdv
from pybdv import transformations as tf
import mrcfile as mrc

navfile = 'test.nav'

tomos = True

downscale_factors = ([2,2,1],[2,2,1],[4,4,1])


# from the configuration in our Tecnai, will be used if no specific info can be found
ta_angle = -11.3 

#======================================
            
def write_h5(outname,data1,pxs,mat2,downscale_factors):
    
    outfile = os.path.join('bdv',outname)
    ndim = data1.ndim
    
    
    if not os.path.exists(outfile+'.h5'):
        if ndim > 2: assert ndim == 3, "Only support 3d"
            #assert len(resolution) == ndim
        if ndim < 3: 
            assert ndim == 2, "Only support 2d"
            d1=np.expand_dims(data1.copy(),axis=0)
            data1=np.concatenate((d1,d1),axis=0)
    
        
        print('Converting map '+outname+' into HDF5.')
        pybdv.make_bdv(data1,outfile,downscale_factors=downscale_factors,setup_name=outname)
        
    tf.write_resolution_and_matrix(outfile+'.xml',outfile+'.xml',[pxs,pxs,10000],mat2)
    

#=======================================




navlines = em.loadtext(navfile)
allitems = em.fullnav(navlines)

if not os.path.exists('bdv'):
    os.makedirs('bdv')

mapinfo = list()

for idx,item in enumerate(allitems):
    if item['Type'][0] == '2': ## item is a map
        itemname=item['# Item']
        
        print('Processing map '+itemname+' to be added to BDV.')                      
                      
        mergemap = em.mergemap(item)
        
        data = mergemap['im'].copy()
        
        mat = np.linalg.inv(mergemap['matrix'])
        
        mat1=np.concatenate((mat,[[0,float(item['PtsX'][0])],[0,float(item['PtsY'][0])]]),axis=1)
        
        mat2=np.concatenate((mat1,[[0,0,10000,0],[0,0,0,1]]))
        
        pxs=mergemap['mapheader']['pixelsize'] 
        
        outname = itemname
        data0 = np.uint8((data-data.min())/data.max()*255)
        
        mapinfo.append([idx,pxs,itemname,mat])
        
        if (mergemap['mapheader']['stacksize'] == 1 and len(data.shape) > 2):
            for channel in range(data.shape[2]):            
                outname = itemname+'_ch'+str(channel)
                data1 = np.squeeze(data0[:,:,channel])
                
                if data1.max() > 0: write_h5(outname,data1,pxs,mat2,downscale_factors)            
            
        else:            
            write_h5(outname,data0,pxs,mat2,downscale_factors)
        
        
        
            
if tomos:
    pxszs = np.array([row[1] for row in mapinfo])
    
    for file in os.listdir():
        dual = False
        if '.rec' in file:
            base = file[:file.index('.rec')]
            
            if os.path.exists(base+'.st.mdoc'):
                mdocfile = base+'.st.mdoc'
            elif os.path.exists(base+'b.st.mdoc'):
                dual = True
                mdocfile = base+'b.st.mdoc'
            elif os.path.exists(base+'a.st.mdoc'):
                mdocfile = base+'a.st.mdoc'
            else:
                if os.path.exists(base+'.st'):
                    tiltfile = base+'.st'
                elif os.path.exists(base+'b.st'):
                    dual = True
                    tiltfile = base+'b.st'
                    
                elif os.path.exists(base+'a.st'):
                    tiltfile = base+'a.st'
                else:
                    print('No tilt stack or mdoc found for tomogram ' + base +'. Skipping it.'
                    continue
                
                # extract stage position from tiltfile
                mdocfile=''
                
                stageinfo = os.popen('extracttilts -s '+tiltfile).read()
                stagepos = stageinfo.splitlines()[-50]
                stage = stagepos.split('  ')
                while '' in stage:
                    stage.remove('')    
                
                pos = np.array(stage).astype(float)
                
                # get pixel size
                mfile = mrc.mmap(file)
                tomopx = mfile.voxel_size.x
                
                mfile.close()
                
                # find map with comparable pixel size and use its scale matrix
                matchidx = np.argmin(np.abs(1-pxszs/tomopx))
                map_px = pxszs[matchidx]
                mat = np.multiply(mapinfo[matchidx][3] , tomopx/map_px)
                
            if len(mdocfile)>0:
                
                mdlines=em.loadtext(mdocfile)
                ta_angle1 = mdlines[8]
                ta_angle2 = ta_angle1[ta_angle1.find('Tilt axis angle = ')+18:]
                ta_angle = float(ta_angle2[:ta_angle2.find(',')])
                
                slice1 = em.mdoc_item(mdlines,'ZValue = 0')
                navidx = int(slice1['NavigatorLabel'][0])
                navitem = allitems[navidx]
                
                tomopx = int(slice1['PixelSpacing'])                
                matchidx = np.argmin(np.abs(1-pxszs/tomopx))
                map_px = pxszs[matchidx]
                mat = np.multiply(mapinfo[matchidx][3] , tomopx/map_px)
                
                # if underlying map
                if navitem['Type'][0] == '2':
                    mapfile = em.map_file(navitem)
                    map_mrc = mrc.mmap(mapfile, permissive = 'True')
                    map_px = map_mrc.voxel_size.x
                    map_mrc.close()
                    
                    # check if tomo mag matches map mag
                    if np.abs(1-map_px/tomopx) < 0.05:
                        mat = np.linalg.inv(em.map_matrix(navitem))
                
                xval = float(navitem['StageXYZ'][0])
                yval = float(navitem['StageXYZ'][1])
                pos = numpy.array([xval,yval])
                
            # compensate rotation
            
            phi = np.radians(ta_angle)
            c = np.cos(phi)
            s = np.sin(phi)
            rotmat = np.array([[c,-s],[s,c]])
            
            mat = np.dot(mat,rotmat)
            
            mat1=np.concatenate((mat,[[0,pos[0]],[0,pos[1]]]),axis=1)        
            mat2=np.concatenate((mat1,[[0,0,10000,0],[0,0,0,1]]))
        
            
                
                
                

                
                
                
            
    
                
