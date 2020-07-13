# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 16:30:40 2020

@author: schorb
"""

import sqlite3
import numpy as np
import os

from pybdv import transformations as tf

import bdv_tools as bdv

from skimage import io


# base intensity normailsation on average instead of absolute minmax values

int_av = True
#how many times StDev to consider
int_width = 2

downscale_factors = list(([1,2,2],[1,2,2],[1,2,2],[1,2,2],[1,4,4]))

dirname = 'bdv_LLP'
outformat = '.h5'

#%%



basename ='LLP'

cwd = os.getcwd()

if not os.path.exists(dirname):
    os.makedirs(dirname)

#load database

db = sqlite3.connect('llp.sqlite')
c=db.cursor()
c.execute('SELECT * FROM image_item')

keys = [description[0] for description in c.description]

imdb = list()
mags = list()

# import data
for row in c.execute('SELECT * FROM image_item ORDER BY image_id'):
    im_item = dict()
    for idx,key in enumerate(keys):
        im_item[key] = row[idx]
    
    mags.append(row[3])
    
    imdb.append(im_item)
    
mags=np.array(mags)


# histogram information for intensity scaling
c.execute('SELECT histgramRangeMax FROM histgram')
h_max = c.fetchall()[1][0]

c.execute('SELECT histgramRangeMin FROM histgram')
h_min = c.fetchall()[1][0]

c.execute('SELECT histgramAverage FROM histgram')
h_av = c.fetchall()[1][0]

c.execute('SELECT histgramStdev FROM histgram')
h_sd = c.fetchall()[1][0]

db.close()

#minmax iwill be based on average value, otherwise use given values

if int_av:
    h_max = int(min(65535,h_av + int_width * h_sd))
    h_min = int(max(0,h_av - int_width * h_sd))
    




# process each mag separately
    
#for thismag in np.unique(mags):

thismag=1000
if thismag==1000:
    
       
    itemname = basename + '_'+str(thismag)+'x'
     
    outfile = os.path.join(dirname,itemname)
    
    im_idx = np.where(mags==thismag)
    
    
    setup_id=0
    tile_id=0
    
    
    numslices = np.shape(im_idx)[1]
    digits = len(str(numslices))
    
    for tile_id,imx in enumerate(im_idx[0]):       
        
        thisview=dict()
        
        thisim = imdb[imx]
        
        im = io.imread(thisim['filename'])


        thisview['size'] = [1,thisim['image_width_px'],thisim['image_height_px']]
        pxs = 0.001/thisim['pixel_per_nm']
        thisview['resolution'] = [pxs,pxs,pxs]
        thisview['setup_name'] = itemname+'_t'+('{:0'+str(digits)+'}').format(tile_id)
        thisview['setup_id'] = setup_id
        
        thisview['OriginalFile'] = cwd                
        
        thisview['attributes'] = dict()
        thisview['attributes']['tile'] = dict({'id':tile_id})
        
        thisview['attributes']['displaysettings'] = dict({'id':setup_id,'color':bdv.colors['W'],'isset':'true'})
        thisview['attributes']['displaysettings']['Projection_Mode'] = 'Average'
        
        
        #TODO transformation
        
        # 1)  The scale and rotation information       

        
        th = np.radians(thisim['image_degree'])
        ct = np.cos(th)
        st = np.sin(th)
        
        rotmat = pxs * np.array([[ct,-st,0],[st,ct,0],[0,0,1]])
        mat_r = np.concatenate((rotmat,[[0],[0],[0]]),axis=1)                
        mat_r = np.concatenate((mat_r,[[0,0,0,1]]))
        
        tf_sc = tf.matrix_to_transformation(mat_r).tolist()
        
        # 2) The translation matrix to position the object in space (lower left corner)
        
        mat_t = np.concatenate((np.eye(2),[[0,thisim['location_x_nm']/1000],[0,thisim['location_y_nm']/1000]]),axis=1)
        mat_t = np.concatenate((mat_t,[[0,0,1,0],[0,0,0,1]]))
        
        tf_tr = tf.matrix_to_transformation(mat_t).tolist()

        


        
        
        
        thisview['trafo'] = dict()
        thisview['trafo']['Translation'] = tf_tr
        thisview['trafo']['RotateScale'] = tf_sc
        
        setup_id = setup_id+1
        
        data  = im
        thisview['attributes']['displaysettings']['min']=h_min
        thisview['attributes']['displaysettings']['max']=h_max
        bdv.write_bdv(outfile,data,thisview,1,downscale_factors)
    


