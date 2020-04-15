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
import xml.etree.ElementTree as ET
from skimage import io


tomos = True
blend = False
fast = False

bdv_unit = 'um'

timept = 0

colors=dict()

colors['_R'] = '255 0 0 255'
colors['_G'] = '0 255 0 255'
colors['_B'] = '0 0 255 255'
colors['_W'] = '255 255 255 255'
colors['BF'] = '255 255 255 255'

outformat='.h5'


downscale_factors = ([1,2,2],[1,2,2],[1,2,2],[1,4,4])
blow_2d = 1

# from the configuration in our Tecnai, will be used if no specific info can be found
ta_angle = -11.3 



#%%

navfile = sys.argv[1]
# file name navigator

# change path to working directory
os.chdir(os.path.dirname(navfile))
#%%

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
    
    # Some more stuff that BisStitcher has. Maybe it's needed
    MiV = ET.SubElement(seqdesc, 'MissingViews')
    Vip = ET.SubElement(root, 'ViewInterestPoints')
    BBx = ET.SubElement(root, 'BoundingBoxes')
    PSF = ET.SubElement(root, 'PointSpreadFunctions')
    StR = ET.SubElement(root, 'StitchingResults')
    InA = ET.SubElement(root, 'IntensityAdjustments')
    
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
    tree.write(outname)
        






#======================================
            
def write_bdv(outname,data,view,blow_2d=1,outf=outformat):
    
    outfile = os.path.join('bdv',outname)   
        
    

    ndim = data.ndim
    if ndim > 2: assert ndim == 3, "Only support 3d"
        #assert len(resolution) == ndim
    if ndim < 3: 
        assert ndim == 2, "Only support 2d"
        data=np.expand_dims(data.copy(),axis=0)
        
        
#            data1=np.concatenate((d1,d1),axis=0)
        
#        if data.dtype.kind=='i':
#            if data.dtype.itemsize == 1:
#                data0 = np.uint8(data-data.min())
#            elif data.dtype.itemsize == 2:
#                data0 = np.uint16(data-data.min())
#            else:
#                data0 = np.uint16((data-data.min())/data.max()*65535)
#        else:
#            data0 = data.copy()
        
        
    print('Converting map '+outname+' into BDV format ' +outf+'.')
    
    pybdv.make_bdv(data,outfile,downscale_factors,
                       resolution = view['resolution'],
                       unit = bdv_unit, 
                       setup_id = view['setup_id'],
                       timepoint = timept,
                       setup_name = view['setup_name'],
                       attributes = view['attributes'],
                       affine = view['trafo'],
                       overwrite = False)
        
#       
#    if type(pxs)==float or type(pxs)==np.float64:
#        scale = [pxs,pxs,blow_2d]
#        mat2[2,2] = blow_2d
#        mat2[2,3] = 0#-blow_2d/2
#    elif len(pxs) == 1:
#        scale = [pxs,pxs,blow_2d]
#        mat2[2,2] = blow_2d
#        mat2[2,3] = 0#-blow_2d/2
#    elif len(pxs) == 3:
#        scale = pxs
#    else:
#        print('Pixelsize was wrongly defined!!!')
        
        
#    tf.write_resolution_and_matrix(outfile+'.xml',outfile+'.xml',scale,mat2)
    

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
        
        outfile = os.path.join('bdv',outname)
                
        mergemap = em.mergemap(item,blendmont=blend)              
        
        mat = np.linalg.inv(mergemap['matrix'])        
        pxs = mergemap['mapheader']['pixelsize'] 
        
        corners = mapcorners(item)       
        
        if 'Imported' in item.keys():
            transl = [corners[0,2],corners[1,2]]
        else:
            transl = [corners[0,0],corners[1,0]]
        


        # generate the individual transformation matrices
        # 1)  The scale and rotation information form the map item        
        mat_s = np.concatenate((mat,[[0,0],[0,0]]),axis=1)                
        mat_s = np.concatenate((mat_s,[[0,0,1,0],[0,0,0,1]]))
        
        tf_sc = tf.matrix_to_transformation(mat_s).tolist()

        # 2) The translation matrix to position the object in space (lower left corner)
        mat_t = np.concatenate((np.eye(2),[[0,transl[0]],[0,transl[1]]]),axis=1)
        mat_t = np.concatenate((mat_t,[[0,0,1,0],[0,0,0,1]]))
        
        tf_tr = tf.matrix_to_transformation(mat_t).tolist()

        



        # continue based on properties of the map
        
        if type(mergemap['im'])==list:
            # map is composed of single tifs. Can feed them directly into BDV/BigStitcher
            setup_id=0
            tile_id=0
            views=list()
            
            numim = len(mergemap['im'])
            
            digits = len(str(numim))
            
            
            for imfile in mergemap['im']:                   

                # directly into BigStitcher/BDV
                
                imbase = os.path.basename(imfile)
                thisview=dict()
                
                thisview['file'] = '../'+imbase
                
                thisview['size'] = [1,mergemap['mapheader']['xsize'], mergemap['mapheader']['ysize']]
                thisview['resolution'] = [pxs,pxs,pxs]
                thisview['setup_name'] = itemname+'_tile'+('{:0'+str(digits)+'}').format(tile_id)
                thisview['setup_id'] = setup_id
                
                thisview['attributes'] = dict()
                thisview['attributes']['tile'] = tile_id#dict({'id':tile_id})
                
                
                
                thisview['trafo'] = dict()
                thisview['trafo']['Translation'] = tf_tr
                thisview['trafo']['MapScaleMat'] = tf_sc
                
                mat_tpos = np.concatenate(([[1,0],[0,-1]],[[0,mergemap['tilepx'][tile_id][0]],[0,mergemap['mapheader']['ysize']+mergemap['tilepx'][tile_id][1]]]),axis=1)
                mat_tpos = np.concatenate((mat_tpos,[[0,0,1,0],[0,0,0,1]]))
    
                thisview['trafo']['TilePosition'] = tf.matrix_to_transformation(mat_tpos).tolist()
                 
                                  
                tile_id = tile_id+1
                setup_id = setup_id+1
                
                if not fast:
                    data  = io.imread(imfile)
                    write_bdv(outname,data,thisview,blow_2d)
                else:
                    views.append(thisview)
                
            if fast:
                write_fast_xml(outfile+'.xml',views)
                
        else:
            # merged image exists
            data = mergemap['im'].copy()
            
            setup_id = 0
            
            view=dict()
                                
            view['resolution'] = [pxs,pxs,pxs]
            view['setup_id'] = setup_id
            view['setup_name'] = itemname
            
            view['attributes'] = dict()                       
            
            view['trafo'] = dict()
            view['trafo']['Translation'] = tf_tr
            view['trafo']['MapScaleMat'] = tf_sc
            
            # Light microscopy image (CLEM)
            if 'Imported' in item.keys():
                # assign channels
                view['attributes']['displaysettings']=dict()
                
                if item['MapMinMaxScale'] == ['0', '0']:
                    #RGB                    
                    for chidx,ch in enumerate(['_R','_G','_B']):
                        data0 = data[:,:,chidx]
                        view['attributes']['channel'] = dict({'id':int(chidx)})
                        
                        
                        view['setup_id'] = setup_id
                        view['setup_name'] = itemname + ch
                        
                        
                        view['attributes']['displaysettings']['id'] = setup_id                        
                        view['attributes']['displaysettings']['color'] = colors[ch]
                        
                        if data0.max()>0: # ignore empty images
                            write_bdv(outname,data0,view)
                        
                        setup_id = setup_id + 1
                else:
                    # single channel, check if color description in item label
                    if itemname[-2:] in colors.keys():
                        view['attributes']['displaysettings']['color'] = colors[itemname[-2:]]                   
                    
                    write_bdv(outname,data,view)                
        
                
            else:           
                write_bdv(outname,data,view)
            
        
        
        
        mapinfo.append([idx,pxs,itemname,mat])
        
        
       
       
        
        
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
        
        
        
        posx =  np.array([-1,1,1,-1])*xs/2
        posy =  np.array([-1,-1,1,1])*ys/2
        
        pxcorners = np.array([posy,posx])
        
        corners = np.array(np.dot(mat,pxcorners))+[[pos[0]],[pos[1]]]
        
        
        transl = corners[:,0]#smallestcorner(corners)
        
        
        # generate the individual transformation matrices
        # 1)  The scale and rotation information form the map item        
        mat_s = np.concatenate((mat,[[0,0],[0,0]]),axis=1)                
        mat_s = np.concatenate((mat_s,np.dot([[0,0,tomopx,-zs/2*tomopx],[0,0,0,1/zstretch]],zstretch)),axis=0)
        
        tf_sc = tf.matrix_to_transformation(mat_s).tolist()

        # 2) The translation matrix to position the object in space (lower left corner)
        mat_t = np.concatenate((np.eye(2),[[0,transl[0]],[0,transl[1]]]),axis=1)
        mat_t = np.concatenate((mat_t,[[0,0,1,0],[0,0,0,1]]))
        
        tf_tr = tf.matrix_to_transformation(mat_t).tolist()        
               
        
        setup_id = 0
            
        view=dict()
                            
        view['resolution'] = [pxs,pxs,pxs*zstretch]
        view['setup_id'] = setup_id
        view['setup_name'] = 'tomo_'+ base
                             
        
        view['trafo'] = dict()
        view['trafo']['Translation'] = tf_tr
        view['trafo']['RotScale'] = tf_sc
        
        view['attributes'] = dict()
        data = mfile.data
        
        
        # check if volume is rotated 
        if data.shape[0]/data.shape[1]>5:
            data = np.swapaxes(data,0,1)

        data0 = np.swapaxes(data,0,2)
        data1 = np.fliplr(data0)
        data2 = np.swapaxes(data1,0,2)
        
        
        write_bdv(outname,data2,view,blow_2d=blow_2d)
      
        mfile.close()
        
           
            
                
                
                

                
                
                
            
    
                
