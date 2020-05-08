# Conversion of BigDataViewer to Amira, 3D registration and back

### Conversion from large data in BDV format to a downsampled volume in TIF format


- Drag the xml file of your BDV dataset onto Fiji
- BioFormats will recognize it and offer you to load it…

![BioFormats](https://git.embl.de/schorb/bdv_convert/-/blob/master/doc/im/image4.png "BioFormats")

- Select OK
- After a little while (it reads the file header), it shows you a selection of resolutions. These are stored in the data container and can be loaded one by one. Select one that has a reasonable size (possibly smaller than 500x500x500) and resolution you need to detect your registration target items. Remember the binning factor (divide the original voxel number in “Series 0” with the one you just selected. Make sure you unselect Series0.

![SeriesSelect](https://git.embl.de/schorb/bdv_convert/-/blob/master/doc/im/image1.png "SeriesSelect")

- You will get an Image stack in Fiji (it takes a bit to load, be patient)

![Stack](https://git.embl.de/schorb/bdv_convert/-/blob/master/doc/im/image5.png "Stack")

- Save it as Tif using the EXACT file name of the xml file and add 
**.bin*4*.tif**  with the *number* representing the binning factor.

