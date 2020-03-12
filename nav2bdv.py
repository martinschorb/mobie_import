#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy as np
import pyEM as em

import pybdv
from pybdv import transformations as tf
import mrcfile as mrc
import glob
import re
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

#%%

#======================================
            
def write_h5(outname,data,pxs,mat2,downscale_factors,blow_2d):
    
    outfile = os.path.join('bdv',outname)
    
        
    
    if not os.path.exists(outfile+'.h5'):
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
            elif data.dtype.itemsize == 2:
                data0 = np.uint16(data-data.min())
            else:
                data0 = np.uint16((data-data.min())/data.max()*65535)
        else:
            data0 = data.copy()
        
        
        
        print('Converting map '+outname+' into HDF5.')
        data0[data0==0]=1
        
        pybdv.make_bdv(data0,outfile,downscale_factors=downscale_factors,setup_name=outname)
    
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
        
       # if not itemname == 'fm_r2':
       #     continue
        
        print('Processing map '+itemname+' to be added to BDV.')                      
        
        outfile = os.path.join('bdv',outname)   
        mergemap = em.mergemap(item)
        
        if not os.path.exists(outfile+'.h5'):  
        
            data = mergemap['im'].copy()
        
        
        
        mat = np.linalg.inv(mergemap['matrix'])        
        
        corners = mapcorners(item)
        
        
        if 'Imported' in item.keys():
            transl = [corners[0,2],corners[1,2]]
        else:
            transl = [corners[0,0],corners[1,0]]
                        
        mat1=np.concatenate((mat,[[0,transl[0]],[0,transl[1]]]),axis=1)
                
        mat2 = np.concatenate((mat1,[[0,0,1,0],[0,0,0,1]]))
        
        pxs = mergemap['mapheader']['pixelsize'] 
        
        
        
        mapinfo.append([idx,pxs,itemname,mat])
        
        if os.path.exists(outfile+'.h5'):
            data=np.array([])
        else:
            i=0
            while i<10:                
                if os.path.exists(outfile+'_ch'+str(i)+'.h5'):
                    data=np.array([])
                    outname = itemname+'_ch'+str(i)
                i=i+1
       
        if (mergemap['mapheader']['stacksize'] < 2 and len(data.shape) > 2):
            for channel in range(data.shape[2]):            
                outname = itemname+'_ch'+str(channel)
                data1 = np.squeeze(data[:,:,channel])
                
                if data1.max() > 0: write_h5(outname,data1,pxs,mat2,downscale_factors,blow_2d)            
            
        else:            
            write_h5(outname,data,pxs,mat2,downscale_factors,blow_2d)
        
        
print('done writing maps')       
            
if tomos:
    print('starting to convert the tomograms')
    zstretch = blow_2d
    #factor to inflate tomograms in z
    
    pxszs = np.array([row[1] for row in mapinfo])
    
    filelist = list()
    
    for file in glob.iglob('**/*.rec', recursive=True):   
        dual = False
        
        base = file[:file.index('.rec')]
        
        if base[-1]=='a' or  base[-1]=='b':
            if os.path.exists(base[:-1]+'.rec'):
                print('Dual axis reconstruction '+base[:-1]+' found, will skip individual axes.')
                continue
                
        outname = base
        outfile = os.path.join('bdv',outname) 
        
        base1 = os.path.basename(base)
        parts = re.split('\.|_|\-|;| |,',base1)
        
        for item in parts:
            if item.isnumeric():
                base_idx = item
        
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
        stagelines = stageinfo.splitlines()
        stagepos = stageinfo.splitlines()[-int((len(stagelines)-20)/2)]
        stage = stagepos.split('  ')
        while '' in stage:
            stage.remove('')    
        
        pos = np.array(stage).astype(float)
        
        
        # get pixel size
       
        mfile = mrc.mmap(file,permissive = 'True')
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
            
            
            
            if 'NavigatorLabel' in slice1.keys():            
                navlabel = slice1['NavigatorLabel'][0]
            else:
                navlabel = base_idx
            
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
        
        phi = np.radians(-ta_angle)
        c = np.cos(phi)
        s = np.sin(phi)
        rotmat = np.array([[c,s],[-s,c]])
        
        #??????
        mat = np.dot(mat,rotmat.T)
        
        # check if volume is from second axis -> additional 90deg rotation
        
        if base[-1]=='b':
            mat = np.dot(mat,np.array([[0,1],[-1,0]]))
            
        
        # determine location of tomogram corners
        xs=mfile.header.nx
        ys=mfile.header.ny
        zs=mfile.header.nz
        
        
        # check if volume is rotated 
        if xs/ys>5:
            zs=ys
            ys=mfile.header.nz
        
        
        
        posx = [-1,-1,1,1]*xs/2
        posy = [-1,1,-1,1]*ys/2
        
        pxcorners = np.array([posy,posx])
        
        corners = np.array(np.dot(mat,pxcorners))+[[pos[0]],[pos[1]]]
        
        
        transl = corners[:,0]#smallestcorner(corners)
        
        
        mat1=np.concatenate((mat,[[0,transl[0]],[0,transl[1]]]),axis=1)        
        mat2=np.concatenate((mat1,np.dot([[0,0,tomopx,-zs/2*tomopx],[0,0,0,1/zstretch]],zstretch)),axis=0)
        
        
        if not os.path.exists(outfile+'.h5'):
            data = mfile.data
            
            
            # check if volume is rotated 
            if data.shape[0]/data.shape[1]>5:
                data = np.swapaxes(data,0,1)
    
            data0 = np.swapaxes(data,0,2)
            data1 = np.fliplr(data0)
            data2 = np.swapaxes(data1,0,2)
        else:
            data2 = []
      
        mfile.close()
        
        write_h5(outname,data2.copy(),[tomopx,tomopx,tomopx*zstretch],mat2,downscale_factors,blow_2d)
            
            
                
                
                

                
                
                
            
    
                
