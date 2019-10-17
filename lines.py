#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 15:52:03 2019

@author: schorb
"""

#line detection

# im2: binned image 

# fill montage with zeros: blendmont option -fill 0

# get edges
from skimage.filters import threshold_otsu
from skimage import img_as_uint,feature
from skimage.transform import (hough_line,hough_line_peaks,rescale)
from skimage.morphology import remove_small_holes
import numpy
import pyEM as em


em_pxs = 12.6
fm_pxs = 110

binning = 4


#bin by 4
im1=img_as_uint(rescale(im,1/binning))

corners_fm,lines_em = findsquare(im1)

corners_em = corners_em*binning
lines_em = lines_em*binning

# transform fm image for initial rotation
#fm1 = ....

corners_fm,lines_fm = findsquare(fm)




# find lines
def findsquare(im):    
    thr = threshold_otsu(im)
    im1=img_as_uint(im>0.8*thr)
    szi = im.shape
    im2=remove_small_holes(im1,numpy.prod(szi)/1000)
    edg1 = feature.canny(im2,sigma=10)
    
    h, theta, dist  = hough_line(edg1)
    
    # find line peaks
    maxint,a,d =hough_line_peaks(h, theta, dist)
    
    # clean lines based on pairwise parallel and orthogoonal relationships
    
    idx=-numpy.array([numpy.linspace(0,len(a)-1,num=len(a))]).T+numpy.linspace(0,len(a)-1,num=len(a))
    
    # parallel lines, expect a single true value...
    parcheck = numpy.abs(a[idx[1:,:].astype(int)]-a)<0.01
    isparallel = (numpy.sum(parcheck,axis=0)==1)
    
    wrongidx = numpy.where(isparallel==False)
    a=numpy.delete(a,wrongidx)
    d=numpy.delete(d,wrongidx)
    
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
        
    
    
    
    return corners,linepts


