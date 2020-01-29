#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 16:26:45 2019

@author: schorb
"""

import numpy as np
import pyEM as em

import pybdv
from pybdv import transformations as tf
import mrcfile as mrc


import sys
import os

navfile = sys.argv[1]
# file name navigator

# change path to working directory
os.chdir(os.path.dirname(navfile))

tomos = True

downscale_factors = ([1,2,2],[1,2,2],[1,2,2],[1,4,4])


blow_2d = 1

# from the configuration in our Tecnai, will be used if no specific info can be found
ta_angle = -11.3 

#======================================
            
def write_h5(outname,data1,pxs,mat2,downscale_factors,blow_2d):
    
    outfile = os.path.join('bdv',outname)
    
        
    
    if not os.path.exists(outfile+'.h5'):
        ndim = data1.ndim
        if ndim > 2: assert ndim == 3, "Only support 3d"
            #assert len(resolution) == ndim
        if ndim < 3: 
            assert ndim == 2, "Only support 2d"
            data1=np.expand_dims(data1.copy(),axis=0)
#            data1=np.concatenate((d1,d1),axis=0)
    
        
        print('Converting map '+outname+' into HDF5.')
        data1[data1==0]=1
        pybdv.make_bdv(data1,outfile,downscale_factors=downscale_factors,setup_name=outname)
    
    if type(pxs)==float or type(pxs)==np.float64:
        scale = [pxs,pxs,blow_2d]
        mat2[2,2] = blow_2d
        mat2[2,3] = 0#-blow_2d/2
    elif len(pxs) == 1:
        scale = [pxs,pxs,blow_2d]
        mat2[2,2] = blow_2d
        mat2[2,3] = 0#-blow_2d/2
    elif len(pxs) == 3:
        scale = pxs
    else:
        print('Pixelsize was wrongly defined!!!')
        
        
        
    tf.write_resolution_and_matrix(outfile+'.xml',outfile+'.xml',scale,mat2)
    

#=======================================


def mapcorners(item):
    return np.squeeze([[np.array(item['PtsX']).astype(float)],[np.array(item['PtsY']).astype(float)]])

# =========================================
    

def smallestcorner(corners):
    sm_idx = np.argmin(np.sum([corners[0,:],corners[1,:]],axis=0))
    return np.array((corners[0,sm_idx],corners[1,sm_idx]))
    

# =========================================
    




navlines = em.loadtext(navfile)
allitems = em.fullnav(navlines)

if not os.path.exists('bdv'):
    os.makedirs('bdv')

mapinfo = list()

for idx,item in enumerate(allitems):
    if item['Type'][0] == '2': ## item is a map
        itemname=item['# Item']
        outname = itemname
        
        print('Processing map '+itemname+' to be added to BDV.')                      
                      
        mergemap = em.mergemap(item)
        
        data = mergemap['im'].copy()
        
        mat = np.linalg.inv(mergemap['matrix'])        
        
        corners = mapcorners(item)
        
        
        if 'Imported' in item.keys():
            transl = smallestcorner(corners)
        else:
            transl = [corners[0,0],corners[1,0]]
                        
        mat1=np.concatenate((mat,[[0,transl[0]],[0,transl[1]]]),axis=1)
                
        mat2 = np.concatenate((mat1,[[0,0,1,0],[0,0,0,1]]))
        
        pxs = mergemap['mapheader']['pixelsize'] 
        
        if data.dtype.kind=='i':
            if data.dtype.itemsize == 1:
                data0 = np.uint8(data)
            elif data.dtype.itemsize == 2:
                data0 = np.uint16(data)
            else:
                data0 = np.uint16((data-data.min())/data.max()*65535)
        else:
            data0 = data.copy()
        
        mapinfo.append([idx,pxs,itemname,mat])
        
        if (mergemap['mapheader']['stacksize'] == 1 and len(data.shape) > 2):
            for channel in range(data.shape[2]):            
                outname = itemname+'_ch'+str(channel)
                data1 = np.squeeze(data0[:,:,channel])
                
                if data1.max() > 0: write_h5(outname,data1,pxs,mat2,downscale_factors,blow_2d)            
            
        else:            
            write_h5(outname,data0,pxs,mat2,downscale_factors,blow_2d)
        
        
print('done writing maps')       
            
if tomos:
    print('starting to convert the tomograms')
    zstretch = blow_2d
    #factor to inflate tomograms in z
    
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
                # extract stage position from tiltfile
                mdocfile=''
                

            if os.path.exists(base+'.st'):
                tiltfile = base+'.st'
            elif os.path.exists(base+'b.st'):
                dual = True
                tiltfile = base+'b.st'
                
            elif os.path.exists(base+'a.st'):
                tiltfile = base+'a.st'
            else:
                print('No tilt stack or mdoc found for tomogram ' + base +'. Skipping it.')
                continue
                
            print('processing tomogram '+base+'.')    
                
            stageinfo = os.popen('extracttilts -s '+tiltfile).read()
            stagepos = stageinfo.splitlines()[-50]
            stage = stagepos.split('  ')
            while '' in stage:
                stage.remove('')    
            
            pos = np.array(stage).astype(float)
            
            
            # get pixel size
            mfile = mrc.mmap(file)
            tomopx = mfile.voxel_size.x / 10000 # in um
                        
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
                navlabel = slice1['NavigatorLabel'][0]
                
                navitem = em.nav_find(allitems,'# Item',navlabel)

                if navitem ==[]:
                    navitem = em.nav_find(allitems,'# Item','m_'+navlabel)
                                
                
                if not navitem ==[]:
                    navitem = navitem[0]
                    tomopx = float(slice1['PixelSpacing'][0]) / 10000 # in um            
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
                    pos = np.array([xval,yval])
                
            # compensate rotation
            
            phi = np.radians(ta_angle)
            c = np.cos(phi)
            s = np.sin(phi)
            rotmat = np.array([[c,s],[-s,c]])
            
            
            mat = np.dot(mat,rotmat)
            
            # determine location of tomogram corners
            
            posx = [-1,-1,1,1]*mfile.header.nx/2
            posy = [-1,1,-1,1]*mfile.header.ny/2
            
            pxcorners = np.array([posy,posx])
            
            corners = np.array(np.dot(mat,pxcorners))+[[pos[0]],[pos[1]]]
            
            transl = smallestcorner(corners)
            
            
            mat1=np.concatenate((mat,[[0,transl[0]],[0,transl[1]]]),axis=1)        
            mat2=np.concatenate((mat1,np.dot([[0,0,tomopx,-mfile.header.nz/2*tomopx],[0,0,0,1/zstretch]],zstretch)),axis=0)
            
            outname = base
            
            if not os.path.exists(outname+'.h5'):
                data = mfile.data
                
                if data.dtype.kind=='i':
                    if data.dtype.itemsize == 1:
                        data0 = np.uint8(data)
                    elif data.dtype.itemsize == 2:
                        data0 = np.uint16(data)
                    else:
                        data0 = np.uint16((data-data.min())/data.max()*65535)
                else:
                    data0 = data.copy()
                
                
        
                data0 = np.swapaxes(data,0,2)
                data1 = np.fliplr(data0)
                data2 = np.swapaxes(data1,0,2)
            else:
                data2 = []
          
            mfile.close()
            
            write_h5(outname,data2,[tomopx,tomopx,tomopx*zstretch],mat2,downscale_factors,blow_2d)
            
            
                
                
                

                
                
                
            
    
                
