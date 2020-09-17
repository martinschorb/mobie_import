#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy as np
import pyEM as em

#import pybdv
from pybdv import transformations as tf
import mrcfile as mrc
import glob
import re
import sys
import os

from skimage import io

import bdv_tools as bdv

tomos = True
blend = True
skipmaps = True
fast = False
cluster = True


bdv_unit = 'um'

timept = 0

outformat='.h5'

chunks = list((16,192,192))
downscale_factors = list(([1,2,2],[1,2,2],[1,2,2],[1,2,2],[1,4,4]))
blow_2d = 1

# from the configuration in our Tecnai, will be used if no specific info can be found
ta_angle = -11.3

dirname0 = 'bdv'+outformat

tomodir = 'tomo'
recdir = 'tomo_rec'





#%%

navfile = sys.argv[1]
# file name navigator

# change path to working directory
os.chdir(os.path.dirname(navfile))
#%%

if skipmaps:
    blend = False

#=======================================


def mapcorners(item):
    return np.squeeze([[np.array(item['PtsX']).astype(float)],[np.array(item['PtsY']).astype(float)]])

# =========================================


def smallestcorner(corners):
    sm_idx = np.argmin(np.sum([corners[0,:],corners[1,:]],axis=0))
    return np.array((corners[0,sm_idx],corners[1,sm_idx]))


# =========================================


navlines = em.loadtext(navfile)
allitems = em.fullnav(navlines)

dirname = dirname0

if tomos:
    dirname=os.path.join(dirname0,'maps')

if not os.path.exists(dirname):
    os.makedirs(dirname)



mapinfo = list()

for idx,item in enumerate(allitems):
    if item['Type'][0] == '2': ## item is a map

        if 'Draw' in item.keys():

            if item['Draw'] == ['0']: continue

        itemname=item['# Item']
        outname = itemname

        mfbase = os.path.basename(item['MapFile'][0])
        mfbase = mfbase[:mfbase.rfind(os.path.extsep)]

        print('Processing map '+itemname+' to be added to BDV.')

        outfile = os.path.join(dirname,outname)+outformat

        mergemap = em.mergemap(item,blendmont=blend)

        mat = np.linalg.inv(mergemap['matrix'])
        pxs = mergemap['mapheader']['pixelsize']

        corners = mapcorners(item)

        if 'Imported' in item.keys():
            transl = [corners[0,2],corners[1,2]]
        else:
            transl = [corners[0,0],corners[1,0]]



        # generate the individual transformation matrices
        # 1)  The scale and rotation information form the map item
        mat_s = np.concatenate((mat,[[0,0],[0,0]]),axis=1)
        mat_s = np.concatenate((mat_s,[[0,0,1,0],[0,0,0,1]]))

        tf_sc = tf.matrix_to_transformation(mat_s).tolist()

        # 2) The translation matrix to position the object in space (lower left corner)
        mat_t = np.concatenate((np.eye(2),[[0,transl[0]],[0,transl[1]]]),axis=1)
        mat_t = np.concatenate((mat_t,[[0,0,1,0],[0,0,0,1]]))

        tf_tr = tf.matrix_to_transformation(mat_t).tolist()





        # continue based on properties of the map
        if not skipmaps:
            if type(mergemap['im'])==list:
                # map is composed of single tifs. Can feed them directly into BDV/BigStitcher
                setup_id=0
                tile_id=0
                views=list()
                numim = len(mergemap['im'])

                digits = len(str(numim))


                for imfile in mergemap['im']:

                    # directly into BigStitcher/BDV

                    imbase = os.path.basename(imfile)
                    thisview=dict()

                    thisview['file'] = '../'+imbase
                    thisview['OriginalFile'] = imfile

                    thisview['size'] = [1,mergemap['mapheader']['ysize'], mergemap['mapheader']['xsize']]
                    thisview['resolution'] = [pxs,pxs,pxs]
                    thisview['setup_name'] = itemname+'_tile'+('{:0'+str(digits)+'}').format(tile_id)
                    thisview['setup_id'] = setup_id

                    thisview['attributes'] = dict()
                    thisview['attributes']['tile'] = dict({'id':tile_id})

                    thisview['attributes']['displaysettings'] = dict({'id':setup_id,'color':bdv.colors['W'],'isset':'true','min':0,'max':65535})
                    thisview['attributes']['displaysettings']['Projection_Mode'] = 'Average'

                    thisview['trafo'] = dict()
                    thisview['trafo']['Translation'] = tf_tr
                    thisview['trafo']['MapScaleMat'] = tf_sc

                    mat_tpos = np.concatenate(([[1,0],[0,-1]],[[0,mergemap['tilepx'][tile_id][0]],[0,mergemap['mapheader']['ysize']+mergemap['tilepx'][tile_id][1]]]),axis=1)
                    mat_tpos = np.concatenate((mat_tpos,[[0,0,1,0],[0,0,0,1]]))

                    thisview['trafo']['TilePosition'] = tf.matrix_to_transformation(mat_tpos).tolist()


                    tile_id = tile_id+1
                    setup_id = setup_id+1

                    if not fast:
                        data  = io.imread(imfile)
                        thisview['attributes']['displaysettings']['min']=data.min()
                        thisview['attributes']['displaysettings']['max']=data.max()
                        bdv.write_bdv(outfile,data,thisview,blow_2d,downscale_factors)
                    else:
                        views.append(thisview)

                if fast:
                    bdv.write_fast_xml(outfile+'.xml',views)

            elif len(mergemap['im'].shape)==3 and blend==False and not('Imported' in item.keys()):
                # montage tiles in mrc stack


                setup_id=0
                tile_id=0

                numslices = mergemap['im'].shape[2]
                digits = len(str(numslices))

                for tile_id in range(numslices):

                    thisview=dict()

                    thisview['size'] = [1,mergemap['mapheader']['xsize'], mergemap['mapheader']['ysize']]
                    thisview['resolution'] = [pxs,pxs,pxs]
                    thisview['setup_name'] = itemname+'_tile'+('{:0'+str(digits)+'}').format(tile_id)
                    thisview['setup_id'] = setup_id

                    thisview['OriginalFile'] = mergemap['mapfile']

                    thisview['attributes'] = dict()
                    thisview['attributes']['tile'] = dict({'id':tile_id})

                    thisview['attributes']['displaysettings'] = dict({'id':setup_id,'color':bdv.colors['W'],'isset':'true'})
                    thisview['attributes']['displaysettings']['Projection_Mode'] = 'Average'

                    thisview['trafo'] = dict()
                    thisview['trafo']['Translation'] = tf_tr
                    thisview['trafo']['MapScaleMat'] = tf_sc

                    mat_tpos = np.concatenate(([[1,0],[0,1]],[[0,mergemap['tilepx'][tile_id][0]],[0,mergemap['mergeheader']['ysize']-mergemap['mapheader']['ysize']-mergemap['tilepx'][tile_id][1]]]),axis=1)
                    mat_tpos = np.concatenate((mat_tpos,[[0,0,1,0],[0,0,0,1]]))

                    thisview['trafo']['TilePosition'] = tf.matrix_to_transformation(mat_tpos).tolist()

                    setup_id = setup_id+1

                    data  = mergemap['im'][:,:,tile_id]
                    thisview['attributes']['displaysettings']['min']=item['MapMinMaxScale'][0]
                    thisview['attributes']['displaysettings']['max']=item['MapMinMaxScale'][1]
                    bdv.write_bdv(outfile,data,thisview,blow_2d,downscale_factors)


            else:
                # merged image exists
                data = mergemap['im']#.copy()

                setup_id = 0

                view=dict()

                view['resolution'] = [pxs,pxs,pxs]
                view['setup_id'] = setup_id
                view['setup_name'] = itemname

                view['OriginalFile'] = mergemap['mergefile']

                view['attributes'] = dict()

                view['trafo'] = dict()
                view['trafo']['Translation'] = tf_tr
                view['trafo']['MapScaleMat'] = tf_sc

                # Light microscopy image (CLEM)
                if 'Imported' in item.keys():
                    # assign channels
                    view['attributes']['displaysettings']=dict({'id':setup_id,'Projection_Mode':'Sum','isset':'true'})

                    if item['MapMinMaxScale'] == ['0', '0']:
                        #RGB
                        for chidx,ch in enumerate(['R','G','B']):
                            data0 = data[:,:,chidx]
                            view['attributes']['channel'] = dict({'id':int(chidx)})
                            view['attributes']['displaysettings']['min']=data0.min()
                            view['attributes']['displaysettings']['max']=data0.max()

                            view['setup_id'] = setup_id
                            view['setup_name'] = itemname + ch


                            view['attributes']['displaysettings']['id'] = setup_id
                            view['attributes']['displaysettings']['color'] = bdv.colors[ch]

                            if data0.max()>0: # ignore empty images
                                bdv.write_bdv(outfile,data0,view,downscale_factors)
                                setup_id = setup_id + 1

                    else:
                        # single channel, check if color description in item label
                        if itemname[-3:][itemname[-3:].rfind('_')+1:] in bdv.colors.keys():
                            view['attributes']['displaysettings']['color'] = bdv.colors[itemname[-3:][itemname[-3:].rfind('_')+1:]]
                        elif mfbase[-3:][mfbase[-3:].rfind('_')+1:] in bdv.colors.keys():
                            view['attributes']['displaysettings']['color'] = bdv.colors[mfbase[-3:][mfbase[-3:].rfind('_')+1:]]

                        view['attributes']['displaysettings']['min']=item['MapMinMaxScale'][0]
                        view['attributes']['displaysettings']['max']=item['MapMinMaxScale'][1]
                        bdv.write_bdv(outfile,data,view,downscale_factors)


                else:

                    view['attributes']['displaysettings'] = dict({'id':setup_id,'color':bdv.colors['W'],'isset':'true'})
                    view['attributes']['displaysettings']['Projection_Mode'] = 'Average'

                    if os.path.exists(outfile+'.xml'):
                        view['attributes']['displaysettings'] = bdv.get_displaysettings(outfile)
                    else:
                        view['attributes']['displaysettings']['min']=data.min()#item['MapMinMaxScale'][0]
                        view['attributes']['displaysettings']['max']=data.max()#item['MapMinMaxScale'][1]

                    bdv.write_bdv(outfile,data,view,downscale_factors)




        mapinfo.append([idx,pxs,itemname,mat])






print('done writing maps')

if tomos:

    dirname=os.path.join(dirname0,'tomos')

    if not os.path.exists(dirname):
        os.makedirs(dirname)



    print('starting to convert the tomograms')
    zstretch = blow_2d
    #factor to inflate tomograms in z

    pxszs = np.array([row[1] for row in mapinfo])

    filelist = list()

    for file in glob.iglob(recdir+'/*.rec', recursive=True):
        dual = False

        base = os.path.splitext(file)[0]

        if base[-1]=='a' or  base[-1]=='b':
            if os.path.exists(base[:-1]+'.rec'):
                print('Dual axis reconstruction '+base[:-1]+' found, will skip individual axes.')
                continue

        outname = os.path.basename(base)
        outfile = os.path.join(dirname,outname)+outformat


        base1 = os.path.basename(base)
        parts = re.split('\.|_|\-|;| |,',base1)


        for item in parts:
            if item.isnumeric():
                base_idx = item

        tomobase = os.path.join(tomodir,base1)

        if os.path.exists(tomobase+'.st.mdoc'):
            mdocfile = tomobase+'.st.mdoc'
        elif os.path.exists(tomobase+'b.st.mdoc'):
            dual = True
            mdocfile = tomobase+'b.st.mdoc'
        elif os.path.exists(tomobase+'a.st.mdoc'):
            mdocfile = tomobase+'a.st.mdoc'
        else:
            # extract stage position from tiltfile
            mdocfile=''


        if os.path.exists(tomobase+'.st'):
            tiltfile = tomobase+'.st'
        elif os.path.exists(tomobase+'b.st'):
            dual = True
            tiltfile = tomobase+'b.st'

        elif os.path.exists(tomobase+'a.st'):
            tiltfile = tomobase+'a.st'
        else:
            print('No tilt stack or mdoc found for tomogram ' + base +'. Skipping it.')
            continue

        print('processing tomogram '+base+'.')

        stageinfo = os.popen('extracttilts -s '+tiltfile).read()
        stagelines = stageinfo.splitlines()
        stagepos = stageinfo.splitlines()[-int((len(stagelines)-20)/2)]
        stage = stagepos.split('  ')
        while '' in stage:
            stage.remove('')

        pos = np.array(stage).astype(float)


        # get pixel size

        mfile = mrc.mmap(file,permissive = 'True')
        tomopx = mfile.voxel_size.x / 10000 # in um


        # find map with comparable pixel size and use its scale matrix
        matchidx = np.argmin(np.abs(1-pxszs/tomopx))
        map_px = pxszs[matchidx]
        mat = np.multiply(mapinfo[matchidx][3] , tomopx/map_px)

        if len(mdocfile)>0:

            mdlines=em.loadtext(mdocfile)
            ta_angle1 = mdlines[8]
            ta_angle2 = ta_angle1[ta_angle1.find('Tilt axis angle = ')+18:]
            ta_angle = float(ta_angle2[:ta_angle2.find(',')])

            slice1 = em.mdoc_item(mdlines,'ZValue = 0')



            if 'NavigatorLabel' in slice1.keys():
                navlabel = slice1['NavigatorLabel'][0]
            else:
                navlabel = base_idx

            navitem = em.nav_find(allitems,'# Item',navlabel)



            if navitem ==[]:
                navitem = em.nav_find(allitems,'# Item','m_'+navlabel)

            else:

                navitem = navitem[0]
                tomopx = float(slice1['PixelSpacing'][0]) / 10000 # in um

                checkpx = True
                # if underlying map
                if navitem['Type'][0] == '2':
                    mapfile = em.map_file(navitem)
                    map_mrc = mrc.mmap(mapfile, permissive = 'True')
                    map_px = map_mrc.voxel_size.x / 10000
                    map_mrc.close()

                    # check if tomo mag matches map mag
                    if np.abs(1-map_px/tomopx) < 0.05:
                        mat = np.linalg.inv(em.map_matrix(navitem))
                        checkpx = False

                if checkpx:
                    matchidx = np.argmin(np.abs(1-pxszs/tomopx))
                    map_px = pxszs[matchidx]
                    mat = np.multiply(mapinfo[matchidx][3] , tomopx/map_px)


                xval = float(navitem['StageXYZ'][0])
                yval = float(navitem['StageXYZ'][1])
                pos = np.array([xval,yval])

        # compensate rotation

        phi = np.radians(-ta_angle)
        c = np.cos(phi)
        s = np.sin(phi)
        rotmat = np.array([[c,s],[-s,c]])


        #??????
        mat = np.dot(mat,rotmat.T)

        # check if volume is from second axis -> additional 90deg rotation

        if base[-1]=='b':
            mat = np.dot(mat,np.array([[0,1],[-1,0]]))


        # determine location of tomogram corners
        xs=mfile.header.nx
        ys=mfile.header.ny
        zs=mfile.header.nz


        # check if volume is rotated
        if xs/ys>5:
            zs=ys
            ys=mfile.header.nz



        posx =  np.array([-1,1,1,-1])*xs/2
        posy =  np.array([-1,-1,1,1])*ys/2

        pxcorners = np.array([posy,posx])

        corners = np.array(np.dot(mat,pxcorners))+[[pos[0]],[pos[1]]]


        transl = corners[:,0]#smallestcorner(corners)


        # generate the individual transformation matrices
        # 1)  The scale and rotation information form the map item
        mat_s = np.concatenate((mat,[[0,0],[0,0]]),axis=1)
        mat_s = np.concatenate((mat_s,np.dot([[0,0,tomopx,-zs/2*tomopx],[0,0,0,1/zstretch]],zstretch)),axis=0)

        tf_sc = tf.matrix_to_transformation(mat_s).tolist()

        # 2) The translation matrix to position the object in space (lower left corner)
        mat_t = np.concatenate((np.eye(2),[[0,transl[0]],[0,transl[1]]]),axis=1)
        mat_t = np.concatenate((mat_t,[[0,0,1,0],[0,0,0,1]]))

        tf_tr = tf.matrix_to_transformation(mat_t).tolist()


        setup_id = 0

        view=dict()

        view['resolution'] = [tomopx,tomopx,tomopx*zstretch]
        view['setup_id'] = setup_id
        view['setup_name'] = 'tomo_'+ os.path.basename(base)

        view['OriginalFile'] = file

        view['trafo'] = dict()
        view['trafo']['Translation'] = tf_tr
        view['trafo']['RotScale'] = tf_sc

        view['attributes'] = dict()

        view['attributes']['displaysettings'] = dict({'id':setup_id,'color':bdv.colors['W'],'isset':'true'})
        view['attributes']['displaysettings']['Projection_Mode'] = 'Average'

        view['attributes']['displaysettings']['min']=-127
        view['attributes']['displaysettings']['max']=127

        data = mfile.data


        # check if volume is rotated
        if data.shape[0]/data.shape[1]>5:
            data = np.swapaxes(data,0,1)

        data0 = np.swapaxes(data,0,2)
        data1 = np.fliplr(data0)
        data2 = np.swapaxes(data1,0,2)

        print(outfile)

        bdv.write_bdv(outfile,data2,view,blow_2d=blow_2d,downscale_factors=downscale_factors,cluster=cluster,infile=file,chunks=chunks)

        mfile.close()
