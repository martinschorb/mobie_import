# -*- coding: utf-8 -*-

# maps_reg.py - (C) 2018 Martin Schorb EMBL
#
# takes a SerialEM navigator and 
# 
# input:
# - the file name of the navigator
#  
#
# output:
# 


# PARAMETERS


# navname = 'nav1.nav'
# file name navigator





# ====================================================================================


# dependencies


import pyEM as em
import numpy
import os
#import tifffile as tiff
from skimage import io
from skimage import transform as tf
import json

import argparse

parser = argparse.ArgumentParser(description='Export SerialEM Registration Information to external Software')
parser.add_argument('navfile', metavar='Filename', type=str,
                    help='the Navigator file to process')
parser.add_argument('-im', dest='im', help='use this flag if image output is desired', action='store_true', default=False)
parser.add_argument('-j', dest='json', help='use this flag if output should be JSON for ImageJ', action='store_true', default=False)
parser.add_argument('-icy', dest='icy', help='use this flag if output should be ICY csv ROIs', action='store_true', default=False)

args = parser.parse_args()


# start actions

navname = args.navfile
f_im = args.im
f_json = args.json
f_icy = args.icy

# start script

#%%


navlines = em.loadtext(navname)
allitems = em.fullnav(navlines)


# Find all Registration Points
regpts = list(filter(lambda item:item.get('RegPt'),allitems))


# Find all Maps to process
acq = filter(lambda item:item.get('Acquire'),allitems)
acq = list(filter(lambda item:item['Acquire']==['1'],acq))



regidx = []
regreg = []
regmap = []

for regpoint in regpts:
    regidx.append(int(regpoint['RegPt'][0]))
    regreg.append(int(regpoint['Regis'][0]))
    regmap.append(regpoint['DrawnID'][0])
    
regidx = numpy.array(regidx)
regreg = numpy.array(regreg)
regmap = numpy.array(regmap)


# Process each map
for mapitem in acq:
    
    start_map = em.mergemap(mapitem)
    
    # find the Registration Points on this Map
    mapregpt_idx = numpy.where(regmap==mapitem['MapID'])[0]
    mapregpt_ptidx = regidx[mapregpt_idx]
    
    mapreg = mapitem['Regis']
    
    # find maps in the same Registratoin that will be transformed as well
    sameregmaps = filter(lambda item:item.get('MapMontage'),allitems)
    sameregmaps = filter(lambda item:item['Regis']==mapreg,sameregmaps)
    sameregmaps = list(filter(lambda item:item['MapWidthHeight']==mapitem['MapWidthHeight'],sameregmaps))
    
#    sameregmaps.remove(mapitem)
    
    mapreg = int(mapreg[0])
    
    em_pt = []   
    lm_pt = []
    
    
    # find the corresponding registration point pairs and target map
    pair0 = numpy.where(regidx==regidx[mapregpt_idx[0]])[0]
    
    # determine correct order for this pair
    if regreg[pair0[0]]==mapreg:
        pair0 =  numpy.array([pair0[1],pair0[0]])
        
    
    reg_start = regreg[pair0[1]]
    reg_target = regreg[pair0[0]]
    
    targetitem = regpts[pair0[0]]
    target_mitem = list(filter(lambda item:item['MapID']==targetitem['DrawnID'],allitems))[0]
    target_map = em.mergemap(target_mitem)
    
     
    # determine pixel coordinates for each registration point for this map's transform   
    for index in mapregpt_idx:
        pair = numpy.where(regidx==regidx[index])[0]
        
        # determine correct order for this pair
        if regreg[pair[0]]==mapreg:
            pair =  numpy.array([pair[1],pair[0]])
            
        targetitem = regpts[pair[0]]
        startitem = regpts[pair[1]]
        
        em_pt.append(em.get_pixel(targetitem,target_map))
        lm_pt.append(em.get_pixel(startitem,start_map))
        
    lm_pt1 = numpy.squeeze(lm_pt)
    em_pt1 = numpy.squeeze(em_pt)
    
    
    # generate Transformation
    tform = tf.SimilarityTransform()
    tform.estimate(em_pt1,lm_pt1)
    
    # Transform and export all maps in this Registration
    for tfmmap in sameregmaps:
        srcmap = em.mergemap(tfmmap)

#        
        # file names and export
        startname = os.path.splitext(os.path.basename(srcmap['mapfile']))[0]
        targetname = os.path.splitext(os.path.basename(target_map['mergefile']))[0]
        outfile = startname+'->'+targetname+'.tif'

        
        newfile = startname + '.meta.txt'
        
        mat= tform.params*srcmap['mergeheader']['pixelsize']*1000
        

    #########  Registered images     
    
        if f_im:
        
            
            warped = tf.warp(numpy.array(srcmap['im']), tform, output_shape = target_map['im'].shape)
            
            if warped.dtype == 'float': 
                if srcmap['im'].dtype == 'uint8':
                    warped = (warped*255)
                elif srcmap['im'].dtype == 'uint16':
                    warped = (warped*65535)
                        
                warped = warped.astype(srcmap['im'].dtype)
            io.imsave(outfile,warped)
            
            print('Output file '+outfile+' written as transformed image.')

        ######### JSON
        
        if f_json:
            
            out=dict()
            
            out['TargetMap'] = os.path.basename(target_map['mergefile'])
            out['unit'] = 'nanometer'
            out['AffineTransformation2D'] = mat[0:2,:].tolist()
            out['TransformationType'] = 'Similarity'
            out['PointPairs'] = numpy.concatenate((lm_pt1,em_pt1),axis=1).tolist()
            
            
            newfile = startname + '.meta_src.json'
            json.dumps(out)
            nnf = open(newfile,'w')
            nnf.write(json.dumps(out))
            nnf.close()
            
            print('Output file '+newfile+' written as JSON metadata.')

        
        
        
        
        ######## ICY 
        
        if f_icy:
        
            lm_file = start_map['mapfile']+'.csv'
            outtext = list()
            
            for pt in lm_pt:
                outtext.append(numpy.array2string(pt[0])+','+numpy.array2string(pt[1])+',0')
            
            nnf = open(lm_file,'w')
              
            for item in outtext: nnf.write("%s\n" % item)
            
            nnf.close()
            
            
            em_file = target_map['mapfile']+'.csv'
            outtext = list()
            
            for pt in em_pt:
                outtext.append(numpy.array2string(pt[0])+','+numpy.array2string(pt[1])+',0')
            
            nnf = open(em_file,'w')
              
            for item in outtext: nnf.write("%s\n" % item)
            
            nnf.close() 
            
            print('Output files written as csv lists for Icy.')

        
    

    
    
    
    
    

   
            
            
            
            
        
    
    
        
    
    