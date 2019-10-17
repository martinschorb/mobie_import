# -*- coding: utf-8 -*-

# holefinder.py - (C) 2018 Martin Schorb EMBL
#
# takes a SerialEM navigator and finds objects on maps (selected for acquisition) that match a provided template
# 
# input:
# - the file name of the navigator
# - the navigator label of a point marking a hole (an object)
# - the size (in µm) of the hole (object)
#
# output:
# - a new navigator file containing all good points with acquisition already enabled



# PARAMETERS


navname = 'holes.nav'
# file name navigator


holelabel = 'hole'
# NavLabel of template hole

holesize = 2  # µm
# 


# ====================================================================================


# dependencies

import pyEM as em
import numpy
from skimage.feature import match_template
from skimage.filters import gaussian
from skimage.morphology import label
from skimage.measure import regionprops

# start script


navlines = em.loadtext(navname)




newnavf = navname[:-4] + '_holes.nav'
nnf = open(newnavf,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])


allitems = em.fullnav(navlines)

acq = filter(lambda item:item.get('Acquire'),allitems)
acq = list(filter(lambda item:item['Acquire']==['1'],acq))
non_acq = [x for x in allitems if x not in acq]


(hole,rest)=em.nav_item(navlines,holelabel)
holemapitem = em.realign_map(hole,allitems)

holemap = em.mergemap(holemapitem)
maps = {}
maps[holemapitem['# Item']]=holemap

holepos = em.get_pixel(hole,holemap)

window = float(holesize)/holemap['mapheader']['pixelsize'] * 1.6


im_h = em.imcrop(numpy.array(holemap['im']),holepos,[window,window])




outnav=list()
ntotal = len(acq)
  
groupid = em.newID(allitems,99999000)
mapid = em.newID(allitems,199999000)

for idx,map_item in enumerate(acq):
  print('Processing map '+ str(idx+1) + '/' + str(ntotal) + ' (%2.0f%% done)' %(idx*100/ntotal))
  itemid = map_item['# Item']
    
  if not itemid in maps.keys():
      maps[itemid] = em.mergemap(map_item)     
    
       
    
  map_item['Acquire'] = '0'
        
  outnav.append(map_item)    

# Image processing


  im_curr = maps[itemid]['im']
  
  result = match_template(im_curr,im_h,True)
  
  imfd = gaussian(result,window/50) - gaussian(result,window/10)
  
  holelabels = label((imfd>0.5* imfd.max()))
  holeregions = regionprops(holelabels)
  
  groupid=em.newID(outnav,groupid+1)
  imsz = im_curr.shape

#Navigator output
  
  for h_idx,currlabel in enumerate(holeregions):
      mapid=em.newID(outnav,mapid+1)
      ptnav = dict()
      ptnav['Type'] = ['0']
      ptnav['Color'] = ['0']
      ptnav['NumPts'] = ['1']
      ptnav['Acquire'] = ['1']
      ptnav['Draw'] = ['1']
      ptnav['Regis'] = map_item['Regis']
      ptnav['DrawnID'] = map_item['MapID']
      ptnav['MapID'] = [str(mapid)]
      ptnav['BklshXY'] = ['5 -5']
      ptnav['GroupID'] = [str(groupid)]
           
      c_o = numpy.array(currlabel.centroid)
      c_out = numpy.copy(c_o)
      
      c_out[0] = c_o[1]
      c_out[1] = imsz[0] - c_o[0]
      
      if map_item['MapFramesXY'] == ['0', '0']:
        ptnav['CoordsInMap'] = [str(c_out[0]),str(c_out[1]),map_item['StageXYZ'][2]]
      elif maps[itemid]['Sloppy']:
        ptnav['CoordsInAliMontVS'] = [str(c_out[0]),str(c_out[1]),map_item['StageXYZ'][2]]
      else:
        ptnav['CoordsInAliMont'] = [str(c_out[0]),str(c_out[1]),map_item['StageXYZ'][2]]
        
      
      ptnav['# Item'] = map_item['# Item'] + '_' + str(h_idx).zfill(3)
           
      ptnav['PtsX'] = [str(c_out[0])]
      ptnav['PtsY'] = [str(c_out[1])]
      
      outnav.append(ptnav)
    
    
  #px = round(pt_px1[0])
  #py = round(pt_px1[1])
  


newnav = list()
#for nitem in non_acq: 
#    newnav.append(nitem)
for nitem in outnav:
    newnav.append(nitem)
   
for nitem in newnav: 
  out = em.itemtonav(nitem,nitem['# Item'])
  for item in out: nnf.write("%s\n" % item)

            
nnf.close()
