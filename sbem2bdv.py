# -*- coding: utf-8 -*-




import os
import glob
import bdv_tools as bdv
from pyEM import parse_adoc
import numpy as np
from pybdv import transformations as tf

#%%


if not os.path.exists('meta'): print('Change to proper directory!');exit()




mfile0 = os.path.join('meta','logs','imagelist_')

mfiles = glob.glob(mfile0+'*')

tiles = list()
views = list()

idx = 0

for mfile in mfiles:
    
    with open(mfile) as mf: ml = mf.read().splitlines()
    
    mdfile = os.path.join('meta','logs','metadata'+mfile[mfile.rfind('_'):])
    
    with open(mdfile) as mdf: mdl = mdf.read().splitlines()
    
    conffile = os.path.join('meta','logs','config'+mfile[mfile.rfind('_'):])
    
    with open(conffile) as cf: cl = cf.read().splitlines()
    
    config = parse_adoc(cl)
    
    
    pxs = float(config['pixel_size'][0])*2#/1000  # in um
    z_thick = float(config['slice_thickness'][0])#/1000  # in um
    
    
     # generate the individual transformation matrices
     # 1)  The scale and rotation information form the map item
    mat = np.diag((pxs,pxs,z_thick))
    
    mat_s = np.concatenate((mat,[[0],[0],[0]]),axis=1)
    mat_s = np.concatenate((mat_s,[[0,0,0,1]]))
    
    tf_sc = tf.matrix_to_transformation(mat_s).tolist()
    
    
    outfile = os.path.splitext(mfile[mfile.rfind('_')+1:])[0]
    
    
    
    for line in mdl:
        if line.startswith('TILE: '):
            
            tile = bdv.str2dict(line[line.find('{'):])
            tiles.append(tile)
            
       # 2) The translation matrix to position the object in space (lower left corner)
            mat_t = np.concatenate((np.eye(3),[[tile['glob_x']],[tile['glob_y']],[tile['glob_z']]]),axis=1)
            mat_t = np.concatenate((mat_t,[[0,0,0,1]]))
    
            tf_tr = tf.matrix_to_transformation(mat_t).tolist()
            
            
            thisview=dict()
            
            thisview['file'] = tile['filename']
            thisview['setup_name'] = tile['tileid']
            thisview['setup_id'] = idx
            
            thisview['attributes'] = dict()
            thisview['attributes']['tile'] = dict({'id':idx})
            
            
            thisview['attributes']['displaysettings'] = dict({'id':idx,'color':bdv.colors['W'],'isset':'true'})
            thisview['attributes']['displaysettings']['Projection_Mode'] = 'Average'
            
            thisview['attributes']['displaysettings']['min']=0
            thisview['attributes']['displaysettings']['max']=255
    
            thisview['size'] = [1,tile['tile_height'],tile['tile_width']]
            thisview['resolution'] = [z_thick,pxs,pxs]
            
    
            thisview['trafo'] = dict()
            thisview['trafo']['Translation'] = tf_tr
            thisview['trafo']['MapScaleMat'] = tf_sc
            
            idx += 1
            
            views.append(thisview)
            

bdv.write_fast_xml(outfile+'.xml',views)


    