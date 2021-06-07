# -*- coding: utf-8 -*-

import numpy as np

import h5py

import pybdv
import xml.etree.ElementTree as ET
from pybdv import transformations as tf
import os
import json


#from clusterms import submit_slurm


colors=dict()

colors['R'] = '255 0 0 255'
colors['G'] = '0 255 0 255'
colors['B'] = '0 0 255 255'
colors['W'] = '255 255 255 255'
colors['BF'] = '255 255 255 255'


# functions to help playing with BDV


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

    # Some more stuff that BigStitcher has. Maybe it's needed
    # MiV = ET.SubElement(seqdesc, 'MissingViews')
    # Vip = ET.SubElement(root, 'ViewInterestPoints')
    # BBx = ET.SubElement(root, 'BoundingBoxes')
    # PSF = ET.SubElement(root, 'PointSpreadFunctions')
    # StR = ET.SubElement(root, 'StitchingResults')
    # InA = ET.SubElement(root, 'IntensityAdjustments')

    pybdv.metadata._initialize_attributes(viewsets,views[0]['attributes'])

    for thisview in views:

        thisFMap = ET.SubElement(files,'FileMapping')
        thisFMap.set("view_setup",str(thisview['setup_id']))
        thisFMap.set("timepoint",'0')
        thisFMap.set("series",'0')

        pybdv.metadata._update_attributes(viewsets, thisview['attributes'],True)

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
        pybdv.metadata._require_view_setup(viewsets,thisview['setup_id'],thisview['setup_name'],thisview['resolution'],thisview['size'],thisview['attributes'],'nm',True,False,True)
        # write transformation(s)
        pybdv.metadata._write_transformation(vregs,thisview['setup_id'],'0',thisview['trafo'],thisview['resolution'],True)

        # write the xml
    pybdv.metadata.indent_xml(root)
    tree = ET.ElementTree(root)
    tree.write(outname,encoding="UTF-8",xml_declaration=True)



#%%
#================================================================================




def write_bdv(outfile, data, view,blow_2d=1,
                            outf='.h5',
                            downscale_factors = None,
                            timept=0,bdv_unit='um',
                            cluster=False,infile=None,chunks=None):
    outbase = os.path.splitext(outfile)[0]

    if cluster:

        #outdir = os.path.dirname(outfile)
        view_json = outbase+'_view.json'
        with open(view_json, 'w') as f:
            json.dump(view, f)
        
        # view_xml = outbase+'_view.xml'
        # dict2xml(view,view_xml)

        n_threads = 8
        time = 4
        mem = 4

        user = os.popen('whoami').read()

        #in case of domain:
        user = user[user.find('\\')+1:]

        user = user.rstrip('\n')+'@embl.de'

        submit = '/g/emcf/schorb/code/cluster/cluster_ms/submit_slurm.py'

        script = '/g/emcf/schorb/code/bdv_convert/write_bdv_cluster.py'
        env = '/g/emcf/software/python/miniconda/envs/bdv'

        callcmd = 'python ' + submit + ' ' + script

        ds_str = "\' "+str(downscale_factors)+"\' "
        ds_str = ds_str.replace(' ','')

        chunks_str = "\' "+str(chunks)+"\' "
        chunks_str = chunks_str.replace(' ','')

        infile = os.path.abspath(data)
        outfile = os.path.abspath(outfile)
        view_xml = os.path.abspath(view_xml)

        callcmd += ' '+' '.join([infile,outfile,view_xml,ds_str,chunks_str,
                                          'n_threads',str(n_threads),
                                          'mem_limit',str(mem)+'G',
                                          'time_limit',str(time),
                                          'env_name',env,
                                          'mail_address',user,
                                          'modules','[IMOD]'])

        #print(callcmd)
        os.system(callcmd)



            #submit_slurm(script, input_, n_threads=n_threads, mem_limit=str(mem)+'G',
            #             time_limit=time,
            #             env_name=env, mail_address=user)

    else:

        ndim = data.ndim
        if ndim > 2: assert ndim == 3, "Only support 3d"
            #assert len(resolution) == ndim
        if ndim < 3:
            assert ndim == 2, "Only support 2d"
            data=np.expand_dims(data,axis=0)

        data1=data

        # if data.dtype.kind=='i':
        #     if data.dtype.itemsize == 1:
        #         data1 = np.uint8(data-data.min())
        #         view['attributes']['displaysettings']['min']='0'
        #         view['attributes']['displaysettings']['max']=str(int(view['attributes']['displaysettings']['max'])-data.min())
        #     elif data.dtype.itemsize == 2:
        #         data1 = np.uint16(data-data.min())
        #         view['attributes']['displaysettings']['min']='0'
        #         view['attributes']['displaysettings']['max']=str(int(view['attributes']['displaysettings']['max'])-data.min())
        # elif not data.dtype.kind=='u':
        #     data1 = np.uint16((data-data.min())/data.max()*65535)
        #     view['attributes']['displaysettings']['min']='0'
        #     view['attributes']['displaysettings']['max']='65535'
        # elif data.dtype.itemsize > 2:
        #     data1 = np.uint16((data-data.min())/data.max()*65535)
        #     view['attributes']['displaysettings']['min']='0'
        #     view['attributes']['displaysettings']['max']='65535'


        sname = view['setup_name']

        print('Converting '+ sname + ' into BDV format.')


        pybdv.make_bdv(data1,outfile,downscale_factors,
                           resolution = view['resolution'],
                           unit = bdv_unit,
                           setup_id = view['setup_id'],
                           timepoint = timept,
                           setup_name = view['setup_name'],
                           attributes = view['attributes'],
                           affine = view['trafo'],
                           overwrite = 'metadata',
                           chunks = chunks)

        if 'OriginalFile' in view.keys():

            xml_path = os.path.splitext(outfile)[0] + '.xml'

            tree = ET.parse(xml_path)
            root = tree.getroot()

            if not root.find('OriginalFile') == None:
                origf = root.find('OriginalFile')
            else:
                origf = ET.SubElement(root, 'OriginalFile')

            origf.text = view['OriginalFile']

            # write the xml
            tf.indent_xml(root)
            tree = ET.ElementTree(root)
            tree.write(xml_path)

#%%
#================================================================================

def get_displaysettings(infile):
    root = ET.parse(infile+'.xml')
    seqdes = root.find('SequenceDescription')
    vs0 = seqdes.find('ViewSetups')
    atts = vs0.findall('Attributes')

    for attribute in atts:
        if 'displaysettings' in attribute.attrib.values():
            ds = attribute.find('Displaysettings')
    dsv = dict()

    for dset in ds:
        dsv[dset.tag] = dset.text

    return dsv

#%%
#================================================================================


def dict2xml(indict,outfile,root=None):

    if root==None: root = ET.Element('py_dict')

    for key,val in indict.items():
        cp = ET.SubElement(root,key)

        if type(val)==dict:
            cp=dict2xml(val,outfile,root=cp)
        else:
            cp.text = str(val)

    tf.indent_xml(root)
    tree = ET.ElementTree(root)
    tree.write(outfile,encoding="UTF-8")


#%%
#================================================================================



def xml2dict(infile,root=None):
   if root==None:
        tree = ET.parse(infile)
        root = tree.getroot()

   d=dict()

   for elem in root:
        if len(elem)==0:
             item = elem.text
             try:
                 item = int(item)
             except ValueError:
                 try:
                     item = float(item)
                 except ValueError:
                    if item == 'True':
                        item = True
                    elif item == 'False':
                        item = False
                    elif item[0]=='[':
                        item = str2list(item)

             d[elem.tag] = item
        else:
            d[elem.tag]=xml2dict(infile,root=elem)

   return d

#%%
#================================================================================


def str2list(instr):
    # find dim

    dim=0

    instr=str(instr)

    for dim in range(0,len(instr)):
        if instr[dim]=='[':
            continue
        else:
            break

    sepstr = ', ' + '[' * (dim-1)

    df1 = instr[dim:-1].split(sepstr)

    outlist = list()

    if dim > 1:
        for item in df1:
            outlist.append(str2list('[' * (dim-1) + item))
    else:
        for item in df1:
            try:
                outlist.append(int(item))
            except ValueError:
                try:
                    outlist.append(float(item))
                except ValueError:
                    if item == 'True': outlist.append(True)
                    elif item == 'False': outlist.append(False)
                    elif item == 'None': outlist.append(None)
                    else: outlist.append(item)



    return outlist

#%%

#=================================================================================

def str2dict(fun_in):

    if type(fun_in)==list:
        inlist = fun_in
    else:
        instr = str(fun_in.strip('{}'))
        inlist = instr.split(', ')


    output = dict()

    for elem in inlist:
        keyval = elem.split(': ')

        key = str(keyval[0]).strip('\'\"')
        item = str(keyval[1]).strip('\'\"')

        if item.startswith('{'):
            output[key] = str2dict(item)
        else:
             try:
                 int(item)
                 item = int(item)
             except ValueError:
                 try:
                     float(item)
                     item = float(item)
                 except ValueError:
                     if item[0]=='[':
                         item = str2list(item)

             output[key] = item

    return output
