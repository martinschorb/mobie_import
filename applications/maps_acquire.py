# -*- coding: utf-8 -*-

# maps_acquire.py - (C) 2018 Martin Schorb EMBL
#
# takes a SerialEM navigator and generates virtual maps from a given low-mag map at the posisiton of selected points
# 
# input:
# - the file name of the navigator
#  - the navigator label of a map acquired in the target conditions (will be cloned for the virtual maps)
#
# output:
# - one tif file at the desired virtual magnification and image size for each item
# - a new navigator file containing all new maps with acquisition already enabled



# PARAMETERS


navname = 'nav.nav'
# file name navigator


target_map = 'refmap'
# one example map at the desired settings (NavLabel)


# ====================================================================================


# dependencies

import os
import os.path
import numpy

#import matplotlib.pyplot as plt

#import tifffile as tiff
import mrcfile as mrc
import pyEM as em


# start script


navlines = em.loadtext(navname)
(targetitem,junk) = em.nav_item(navlines,target_map)

targetfile = em.map_file(targetitem)
target_mrc = mrc.open(targetfile, permissive = 'True')
targetheader = em.map_header(target_mrc)

t_mat = em.map_matrix(targetitem)

newnavf = navname[:-4] + '_automaps.nav'
nnf = open(newnavf,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])


allitems = em.fullnav(navlines)


acq = filter(lambda item:item.get('Acquire'),allitems)
acq = list(filter(lambda item:item['Acquire']==['1'],acq))

non_acq = [x for x in allitems if x not in acq]

non_acq.remove(targetitem)
    
maps = {}

newmapid = em.newID(allitems,10000)

outnav=list()
ntotal = len(acq)

newnav = list()



for idx,acq_item in enumerate(acq):
  print('Processing navitem '+ str(idx+1) + '/' + str(ntotal) + ' (%2.0f%% done)' %(idx*100/ntotal))

  newmapid = em.newID(allitems,newmapid + 1)
  mapitem = em.realign_map(acq_item,allitems)
  
  itemid = mapitem['# Item']
    
  if not itemid in maps.keys():
    maps[itemid] = em.mergemap(mapitem)
    groupid = em.newID(allitems,999000000+int(mapitem['MapID'][0][-6:]))
    non_acq.remove(mapitem)
    
    # NoRealign
    mapitem['Color'] = '5'
        
    newnav.append(mapitem)
    

  # combine rotation matrices
  
  map_mat = maps[itemid]['matrix'] 
  
  maptf = numpy.linalg.inv(map_mat) * t_mat  
  
  xval = float(acq_item['StageXYZ'][0]) #(float(acq_item['PtsX'][0]))
  yval = float(acq_item['StageXYZ'][1]) #(float(acq_item['PtsY'][0]))
  
  pt = numpy.array([xval,yval])
  
  # calculate the pixel coordinates

  pt_px1 = em.get_pixel(acq_item,maps[itemid])

  px_scale = targetheader['pixelsize'] /( maps[itemid]['mapheader']['pixelsize'] )

  imsz1 = numpy.array([targetheader['ysize'],targetheader['xsize']])
  
  im = numpy.array(maps[itemid]['im'])

  im2, p2 = em.map_extract(im,pt_px1,pt_px1,px_scale,imsz1,maptf)
  

  if min(im2.shape)<200:
    print('Warning! Item ' + acq_item['# Item'] + ' is not within the map frame. Ignoring it')
  else:

    # pad item numbers to 4 digits    
    if acq_item['# Item'].isdigit(): acq_item['# Item'] = acq_item['# Item'].zfill(4)
                
    imfile = 'virt_map_' + acq_item['# Item'] + '.mrc'
    
    if os.path.exists(imfile): os.remove(imfile)
#    tiff.imsave(imfile,im2)
    
    im2 = numpy.rot90(im2,3)

    with mrc.new(imfile) as mrcf:
        mrcf.set_data(im2.T)
        mrcf.close()#        
        
    cx = im2.shape[0]
    cy = im2.shape[1]

    a = [[0,0],[cx,0],[cx,cy],[0,cy],[0,0]]
    a = numpy.matrix(a) - [cx/2 , cy/2]
    
    t_mat_i = numpy.linalg.inv(t_mat)

    c1 = a*t_mat_i.T + pt

    cnx = numpy.array(numpy.transpose(c1[:,1]))
    cnx = numpy.array2string(cnx,separator=' ')
    cnx = cnx[2:-2]

    cny = numpy.array(numpy.transpose(c1[:,0]))
    cny = " ".join(list(map(str,cny)))
    cny = cny[1:-2]


    # fill navigator

    acq_item['Acquire'] = '0'
    
    # NoRealign
    # acq_item['Color'] = '5'

    outnav.append(acq_item)


    newnavitem = dict(targetitem)
    


    newnavitem['MapFile'] = [imfile]
    newnavitem['StageXYZ'] = acq_item['StageXYZ']
    newnavitem['RawStageXY'] = acq_item['StageXYZ'][0:2]
    newnavitem['PtsY'] = cnx.split()
    newnavitem['PtsX'] = cny.split()
    newnavitem['NumPts'] = ['1']
    newnavitem['Note'] = newnavitem['MapFile']
    newnavitem['MapID'] = [str(newmapid)]
    newnavitem['Acquire'] = ['1']
    newnavitem['MapSection'] = ['0']
    newnavitem['SamePosId'] = acq_item['MapID']
    newnavitem['GroupID'] = [str(groupid)]
    # newnavitem['MapWidthHeight'] = [str(im2size[0]),str(im2size[1])]
    newnavitem['ImageType'] = ['2']
    newnavitem['MapMinMaxScale'] = [str(numpy.min(im2)),str(numpy.max(im2))]
    newnavitem['NumPts'] = ['5']
    newnavitem['# Item'] = 'map_' + acq_item['# Item']    

    outnav.append(newnavitem)

  
  
  outnav.sort()


#for nitem in non_acq: 
#    newnav.append(nitem)
  
for nitem in outnav:
    newnav.append(nitem)
   
for nitem in newnav: 
  out = em.itemtonav(nitem,nitem['# Item'])
  for item in out: nnf.write("%s\n" % item)

            
nnf.close()
