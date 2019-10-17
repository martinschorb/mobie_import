# -*- coding: utf-8 -*-
# autoclem.py - (C) 2019 Martin Schorb EMBL
#
# takes a SerialEM navigator and imports light microscopy maps. It can use the gridbars for refining the registration
# input:
# - the file name of the navigator
#  - the navigator label of a map acquired in the target conditions (will be cloned for the virtual maps)
#
# output:
# - a new navigator file containing all new maps with acquisition already enabled



# PARAMETERS


navname = 'nav_start.nav'
# file name navigator


reference_map = 'a1_FM'
# one example map at the desired settings (NavLabel)


prefix_sep = '_'
bf = 'BF'
import_dir = 'import'
map_suffix = '-A'

em_bin = 4
fm_pxs = 110 #  in nm
gridbars = True
separate_regs = True
# ====================================================================================


# dependencies
from skimage.filters import threshold_otsu,sobel
from skimage import img_as_uint,feature,io
from skimage.transform import (hough_line,hough_line_peaks,rescale)
from skimage.morphology import remove_small_holes
import numpy
import pyEM as em
import mrcfile as mrc
import os
import os.path
import sys



# supporting function


# find lines
def findsquare(im):    
    thr = threshold_otsu(im)
    im1=img_as_uint(im>0.8*thr)
    szi = im.shape
    im2=remove_small_holes(im1,numpy.prod(szi)/100)
    edg1 = sobel(im2)
    
    h, theta, dist  = hough_line(edg1)
    
    # find line peaks
    maxint,a,d =hough_line_peaks(h, theta, dist)
    
    # clean lines based on pairwise parallel and orthogoonal relationships
    
    idx=-numpy.array([numpy.linspace(0,len(a)-1,num=len(a))]).T+numpy.linspace(0,len(a)-1,num=len(a))
    
    
    # parallel lines, expect a single true value...
    angle_thr = 0.0001
    sumcheck = False
    at = numpy.mod(a/numpy.pi,1)
    
    parcheck = abs(at[idx[1:,:].astype(int)]-at)==0
    isparallel = (numpy.sum(parcheck,axis=0)==1)

    if sum(isparallel)==4:
        paridx = numpy.where(isparallel)
        a = a[paridx]
        d = d[paridx]
    else:
        # check first two lines
        while not sumcheck and angle_thr<0.1:          
            parcheck = abs(at[idx[1:,:].astype(int)]-at)<angle_thr
            isparallel = (numpy.sum(parcheck,axis=0)==1)
            sumcheck = sum(isparallel)==2
            angle_thr = angle_thr * 1.5
        
        paridx = numpy.where(isparallel)
        
        a0=numpy.delete(a,paridx)
        d0=numpy.delete(d,paridx)    
        at0=numpy.delete(at,paridx)
        
        angle_thr = 0.0001
        sumcheck1 = False
        
        # check second two lines orthogonal
        while not sumcheck1 and angle_thr<0.1:          
            isparallel1 = abs(at0-0.5-at[paridx][0])<angle_thr        
            sumcheck1 = sum(isparallel1)==2
            angle_thr = angle_thr * 1.5
        
        par2idx = numpy.where(isparallel1)
        
        a = numpy.append(a[paridx],a0[par2idx])
        d = numpy.append(d[paridx],d0[par2idx])
    
    
    if len(a) < 4:
        print('ERROR: Could not find 2 pairs of parallel lines! Exiting' + '\n')
        sys.exit(1)
    
    # find corners
    # identify parallel lines with similar slope
    par = numpy.where(numpy.round(a*1000)==numpy.round(a[0]*1000))
    
    corners=list()
    
    for dist1 in d[par]:
        # lines that are not parallel will intersect
        ortho = numpy.delete(numpy.array((0,1,2,3)),par)
        
        # first line
        in1_a = numpy.array([[numpy.cos(a[0]),numpy.sin(a[0])],[numpy.cos(a[ortho[0]]),numpy.sin(a[ortho[0]])]])
        in1_b = numpy.array([dist1,d[ortho[0]]])
        
        x1 , y1 = numpy.linalg.solve(in1_a,in1_b.T)
        
        corners.append([x1,y1])
        
        #second line
        in2_a = numpy.array([[numpy.cos(a[0]),numpy.sin(a[0])],[numpy.cos(a[ortho[1]]),numpy.sin(a[ortho[1]])]])
        in2_b = numpy.array([dist1,d[ortho[1]]])
        
        x2 , y2 = numpy.linalg.solve(in2_a,in2_b.T)
        corners.append([x2,y2])
    
    # draw lines
    
    linepts=list()
    params = numpy.linspace(-2*max(szi[0],szi[1]),2*max(szi[0],szi[1]),4*max(szi[0],szi[1]))
    
    for i,val in enumerate(a):
        linepts.append(numpy.array([[numpy.cos(a[i])],[numpy.sin(a[i])]])*d[i] + params * numpy.array([[numpy.sin(a[i])],[-numpy.cos(a[i])]]))
        
    
    
    
    return numpy.array(corners),linepts







# start script


navlines = em.loadtext(navname)
(refitem,junk) = em.nav_item(navlines,reference_map)

reffile = em.map_file(refitem)

t_mat = em.map_matrix(refitem)

newnavf = navname[:-4] + '_autoclem.nav'
nnf = open(newnavf,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])

allitems = em.fullnav(navlines)

acq = filter(lambda item:item.get('Acquire'),allitems)
acq = list(filter(lambda item:item['Acquire']==['1'],acq))

non_acq = [x for x in allitems if x not in acq]

outnav=list()
ntotal = len(acq)

outnav.extend(non_acq)

newnav = list()

for idx,acq_item in enumerate(acq[0:2]):
    mapfilesearch = acq_item['# Item']+prefix_sep+'*tif'
    fm_files = em.findfile(mapfilesearch,import_dir)
    
    newmapid = em.newID(outnav,10000+idx)
    newmap = refitem.copy()
    
    
    
        
    
    if gridbars:
        
        if not len(fm_files)==2:
            print('ERROR: No matching FM images matching :' + mapfilesearch + ' found! Exiting' + '\n')
            sys.exit(1)
            
        bffilesearch = acq_item['# Item']+prefix_sep+bf+prefix_sep+'*tif'
        bf_files = em.findfile(bffilesearch,import_dir)
        
        if not len(bf_files)==1:
            print('ERROR: No matching BrightField FM image matching :' + bffilesearch + ' found! Exiting' + '\n')
            sys.exit(1)               
    
        bf_file = bf_files[0]
        fm_file = fm_files[fm_files.index(bf_file)-1]
        
        fm = io.imread(bf_file)
            
        (emmapitem,junk) = em.nav_item(navlines,acq_item['# Item']+map_suffix)
        
        emmap = em.mergemap(emmapitem,black=True)
        
        #bin
        im1=img_as_uint(rescale(emmap['im'],1/em_bin))
                 
        
        corners_em,lines_em = findsquare(im1)    
        corners_em = corners_em * em_bin
       
        # transform fm image for initial rotation
        #fm1 = ....
        
        corners_fm,lines_fm = findsquare(fm)
        
        c_fm = numpy.mean(corners_fm,axis=0)
        c_em = numpy.mean(corners_em,axis=0)
        
        
        #transform fm image coordinates
        
        imc_fm = numpy.array(fm.shape)/2
        imc_em = numpy.array(im1.shape)/2*em_bin
        
        mat1 = t_mat/numpy.sqrt(numpy.abs(numpy.linalg.det(t_mat)))
        mat1[:,0]=-mat1[:,0]
        offset=numpy.squeeze(numpy.array(imc_fm-numpy.dot(mat1,imc_fm)))
        
        fm2=em.affine_transform(fm,mat1,offset=offset)
        c1=numpy.array((corners_fm-imc_fm)*mat1.T + imc_fm)
        
        empair=[]
        
        em_c1=(corners_em-c_em) * emmap['mapheader']['pixelsize']
        fm_c1=(c1-c_fm)*fm_pxs/1000
        
        for i in [0,1,2,3]:
            empair.append(numpy.argmin(numpy.sum((fm_c1-em_c1[i,:])**2, axis =1)))
        
        
        
    
    
    else:
        fm_file = fm_files[0]
                
        if len(fm_files)>1:
            print('WARNING: multiple FM images matching :' + mapfilesearch + ' found! Will pick the first one: ' + fm_file + '\n')
            
        
        newmap['PtsX'] =(numpy.array(newmap['PtsX']).astype(float) - numpy.array(newmap['StageXYZ'])[0].astype(float) + numpy.array(acq_item['PtsX']).astype(float)).astype(str)
        newmap['PtsY'] =(numpy.array(newmap['PtsY']).astype(float) - numpy.array(newmap['StageXYZ'])[1].astype(float) + numpy.array(acq_item['PtsY']).astype(float)).astype(str)
        newmap['StageXYZ'] = acq_item['StageXYZ']
    
    

    
    newmap['# Item'] = acq_item['# Item']+prefix_sep+'FM'
    newmap['MapID'] = [str(newmapid)]
    if separate_regs:
        newmap['Regis'] = [str(em.newreg(outnav))]
    newmap['MapFile'] = ['.\\' + import_dir + '\\' + os.path.basename(fm_file)]
    newmap['Note'] = [import_dir + '\\' + os.path.basename(fm_file)]
    
    
    outnav.append(newmap)

for nitem in outnav:
    newnav.append(nitem)
   
for nitem in newnav: 
  out = em.itemtonav(nitem,nitem['# Item'])
  for item in out: nnf.write("%s\n" % item)
            
nnf.close()
