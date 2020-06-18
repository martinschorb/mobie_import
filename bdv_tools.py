# -*- coding: utf-8 -*-

# functions to help playing with BDV 

def attr_id2view_id(attribute_name,viewsetups):
    """
    

    Parameters
    ----------
    attribute_name : string
        Name of the attribute whose IDs are desired.
    viewsetups : ET.Element
        The ViewSetups Element of a BDV XML structure.

    Returns
    -------
    List of int-string pairs. Int in first column corresponds to target attribute IDs,
    strings in second column are the matching ViewSetup IDs.

    """
    
    result = list()
    
    atts = viewsetups.findall('Attributes')
    
    vs = viewsetups.findall('ViewSetup')  
    
    
        
    for attribute in atts:
    
        for viewsetup in vs:
                vs_id = viewsetup.find('id').text
                vs_attr = viewsetup.find('attributes')
                
                vs_tile = int(vs_attr.find(attribute_name).text)                
                result.append([vs_tile,vs_id])