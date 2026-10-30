"""CLANNAD six-bit RGB and exact PNG; SG0 complete-canvas shared expression layers."""
import io
import numpy as np
from PIL import Image

def six_bit_rgb(im):
    a=np.asarray(im.convert('RGBA')).copy();a[:,:,:3]=(a[:,:,:3]//4)*4+2;a[a[:,:,3]==0]=0
    return Image.fromarray(a,'RGBA')

def encode_exact(im):
    im=im.convert('RGBA');a=np.asarray(im);colors,inv=np.unique(a.reshape(-1,4),axis=0,return_inverse=True)
    if len(colors)<=256:
        result=Image.fromarray(inv.reshape(im.height,im.width).astype('uint8'),'P');result.putpalette(colors[:,:3].flatten().tolist());result.info['transparency']=colors[:,3].tobytes()
    else:result=im
    b=io.BytesIO();result.save(b,format='PNG',optimize=True,compress_level=9);data=b.getvalue()
    assert Image.open(io.BytesIO(data)).convert('RGBA').tobytes()==im.tobytes()
    return data

def composite_mse(source,candidate):
    a=np.asarray(source,dtype='float32');b=np.asarray(candidate,dtype='float32')
    a=a[:,:,:3]*a[:,:,3:]/255+48*(1-a[:,:,3:]/255)
    b=b[:,:,:3]*b[:,:,3:]/255+48*(1-b[:,:,3:]/255)
    return float(np.mean((a-b)**2))

def apply_palette(im,palette):
    from scipy.spatial import cKDTree
    used=sorted(index for count,index in palette.getcolors(256));colors=np.asarray(palette.getpalette(),dtype='uint8').reshape(-1,3)[used];a=np.asarray(im);flat=a[:,:,:3].reshape(-1,3);unique,inv=np.unique(flat,axis=0,return_inverse=True)
    _,nearest=cKDTree(colors.astype('float32')).query(unique.astype('float32'));out=np.empty_like(a);out[:,:,:3]=colors[nearest][inv].reshape(a.shape[0],a.shape[1],3);out[:,:,3]=a[:,:,3];out[out[:,:,3]==0]=0
    return Image.fromarray(out,'RGBA')

def compact_faced_base(im,rect):
    from scipy.spatial import cKDTree
    x,y,w,h=rect;face=im.crop((x,y,x+w,y+h));training=Image.new('RGBA',(max(im.width,face.width*4),im.height+face.height*3))
    training.paste(im,(0,0))
    for i in range(12):training.paste(face,((i%4)*face.width,im.height+(i//4)*face.height))
    trained=training.quantize(colors=255,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE);used=sorted(index for count,index in trained.getcolors(256));colors=np.asarray(trained.getpalette('RGBA'),dtype='uint8').reshape(-1,4)[used]
    colors=np.concatenate([np.array([[0,0,0,0]],dtype='uint8'),colors[colors[:,3]>0]])
    a=np.asarray(im);unique,inv=np.unique(a.reshape(-1,4),axis=0,return_inverse=True);weights=np.array([1,1,1,2],dtype='float32');_,nearest=cKDTree(colors.astype('float32')*weights).query(unique.astype('float32')*weights);out=colors[nearest][inv].reshape(a.shape);out[a[:,:,3]==0]=0
    return Image.fromarray(out,'RGBA')
