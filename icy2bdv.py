# -*- coding: utf-8 -*-
# import the py-EM module and make its functions available
import pyEM as em

import xml.etree.ElementTree as ET



# parse command line parameters


import sys
import os
import glob
import numpy as np
import tkinter as tk
from tkinter import filedialog

import pybdv
from pybdv import transformations as tf





#%%

cwd = os.getcwd()

tkroot = tk.Tk()
tkroot.withdraw()



# skip integration into BDV->Icy->BDV as Icy cannot read bdv files (yet).

exist_bdv = tk.messagebox.askyesno(title = 'Select input files',message='Is the fixed image (EM) already registered in BDV?')

if exist_bdv:
    messg1 = tk.messagebox.showinfo(title = 'Select BDV XML', message = 'Select BDV description XML for fixed data (usually EM).')
    bdvxml_em = filedialog.askopenfilename(title = 'Select BDV XML of fixed image (EM).', filetypes = [('XML','*.xml')], initialdir = cwd)
    
    em_root = ET.parse(bdvxml_em)
    
    

emf = filedialog.askopenfilename(title = 'Select fixed image (usually EM)')





# import icy XMLs

x_emf = mm_em['mergefile']+ os.path.splitext( mm_em['mapfile'])[1] + '_ROIsavedwhenshowonoriginaldata' + '.xml'
x_trafo = mm_fm['mapfile'] + '_transfo' + '.xml'

if not all([os.path.exists(x_emf),os.path.exists(x_trafo)]):  raise ValueError('Could not find the results of Icy registration. Please re-run.')
    
root_em = ET.parse(x_emf)
root_trafo = ET.parse(x_trafo)


# extract transformation matrices

mat = []
if root_trafo.find('MatrixTransformation') == None:
    root_trafo = ET.parse(glob.glob(mm_fm['mapfile'] + '_transfo' + '*back-up.xml')[-1])


for child in root_trafo.iter():
    if child.tag == 'MatrixTransformation':
        mat.append(child.attrib)

M = np.eye(4)
M_list = list()
        
for matrix in mat:
    thismat = np.eye(4)
    thismat[0,0] = matrix['m00']
    thismat[0,1] = matrix['m01']
    thismat[0,2] = matrix['m02']
    thismat[0,3] = matrix['m03']
    thismat[1,0] = matrix['m10']
    thismat[1,1] = matrix['m11']
    thismat[1,2] = matrix['m12']
    thismat[1,3] = matrix['m13']
    thismat[2,0] = matrix['m20']
    thismat[2,1] = matrix['m21']
    thismat[2,2] = matrix['m22']
    thismat[2,3] = matrix['m23']
    thismat[3,0] = matrix['m30']
    thismat[3,1] = matrix['m31']
    thismat[3,2] = matrix['m32']
    thismat[3,3] = matrix['m33']
    
    M_list.append(thismat)
    
    M = np.dot(M.T,thismat)
    


# extract registration point positions


p_idx = list()
pts = list()

for child in root_em.iter():
    pt = np.zeros(2)
    if child.tag == 'position':
        
        for coords in child.getiterator():            
            if coords.tag == 'pos_x':
                pt[0] = float(coords.text)
            elif coords.tag == 'pos_y':
                pt[1] = float(coords.text)
            #elif coords.tag == 'pos_z':
            #    pt[2] = float(coords.text)
            
        pts.append(pt)
            
    elif child.tag == 'name':
        p_idx.append(int(child.text[child.text.rfind(' '):]))
                
    


