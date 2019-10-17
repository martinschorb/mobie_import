# -*- coding: utf-8 -*-

# ice.py - (C) 2018 Martin Schorb EMBL
#
# takes a SerialEM navigator and checks image intensity in the map at each point selected for acquisition.
# 
# input:
# - the file name of the navigator
# - the navigator label of a point marking a hole with thick ice
# - the navigator label of a point marking a hole with empty ice
# - the window size (in nm) of the image area to check around the points
# - the intensity range (in percent) between empty and dark hole to consider as good (around the center of the intensity distribution) 
#
# output:
# - a new navigator file containing all good points with acquisition already enabled



# PARAMETERS


navname = 'ice2.nav'
# file name navigator


thicklabel = 'thick'
# NavLabel of thick ice example

emptylabel = 'empty'
# NavLabel of empty hole example

checkwindow = 100  # nm
# box size to check intensities around POI

goodrange = 50    #  percent
# intensity range (around center between thick and empty) to consider good


# ====================================================================================


# dependencies

import pyEM as em
import numpy

# start script


navlines = em.loadtext(navname)




newnavf = navname[:-4] + '_niceice.nav'
nnf = open(newnavf,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])


allitems = em.fullnav(navlines)

acq = filter(lambda item:item.get('Acquire'),allitems)
acq = list(filter(lambda item:item['Acquire']==['1'],acq))
non_acq = [x for x in allitems if x not in acq]


(thick,rest)=em.nav_item(navlines,thicklabel)

thickmapitem = em.realign_map(thick,allitems)

thickmap = em.mergemap(thickmapitem)


(empty,rest)=em.nav_item(navlines,emptylabel)

emptymapitem = em.realign_map(empty,allitems)


if emptymapitem==thickmapitem:
    emptymap = thickmap
else:
    emptymap = em.mergemap(emptymapitem)
    
emptypos = em.get_pixel(empty,emptymap)

thickpos = em.get_pixel(thick,thickmap)



window = checkwindow / thickmap['mapheader']['pixelsize']/1000


im_t = em.imcrop(numpy.array(thickmap['im']),thickpos,[window,window])
im_e = em.imcrop(numpy.array(emptymap['im']),emptypos,[window,window])

i_thick = im_t.mean()
i_empty = im_e.mean()

i_range = i_empty - i_thick

uplim = i_range *(0.5 + float(goodrange)/200) + i_thick
lolim = i_range *(0.5 - float(goodrange)/200) + i_thick



maps = {}

outnav=list()
ntotal = len(acq)

for idx,nav_item in enumerate(acq):
  acq_item=dict(nav_item)  
  print('Processing navitem '+ str(idx+1) + '/' + str(ntotal) + ' (%2.0f%% done)' %(idx*100/ntotal))


  mapitem = em.realign_map(acq_item,allitems)
  
  itemid = mapitem['# Item']
    
  if not itemid in maps.keys():
    if mapitem['# Item'] == thickmapitem['# Item']:
        maps[itemid] = thickmap
    elif mapitem['# Item'] == emptymapitem['# Item']:
        maps[itemid] = emptymap
    else:
        maps[itemid] = em.mergemap(mapitem)     
    
    non_acq.remove(mapitem)
    
    # NoRealign
    #mapitem['Color'] = '5'
        
    outnav.append(mapitem)    
  
  ptpx=em.get_mergepixel(acq_item,maps[itemid])
  
  im_curr = em.imcrop(numpy.array(maps[itemid]['im']),ptpx,[window,window])
  
  intensity = im_curr.mean()
    
  #px = round(pt_px1[0])
  #py = round(pt_px1[1])
  
  if min(im_curr.shape)<window/2:
    print('Warning! Item ' + acq_item['# Item'] + ' is not within the map frame. Ignoring it')
  else:

      
      
      
      
    if (intensity > lolim) & (intensity < uplim):
      #acq_item['Color'] = '1'
      acq_item['Note'] = ['ice OK']
      outnav.append(acq_item)
      
    else:
      #acq_item['Acquire'] = '0'
      acq_item=[]  
      #outnav.append(acq_item)  
        
    # fill navigator

    
    
    # NoRealign
    # acq_item['Color'] = '5'

    #outnav.append(acq_item)


    
    
    # pad item numbers to 4 digits    
  #  if acq_item['# Item'].isdigit(): acq_item['# Item'] = acq_item['# Item'].zfill(4)



  #outnav.sort()

newnav = list()
#for nitem in non_acq: 
#    newnav.append(nitem)
for nitem in outnav:
    newnav.append(nitem)
   
for nitem in newnav: 
  out = em.itemtonav(nitem,nitem['# Item'])
  for item in out: nnf.write("%s\n" % item)

            
nnf.close()
