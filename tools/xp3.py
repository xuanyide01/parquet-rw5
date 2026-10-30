from pathlib import Path
import struct,zlib
MAGIC=b'XP3\r\n \n\x1a\x8bg\x01'

def chunks(data):
    pos=0
    while pos+12<=len(data):
        tag=data[pos:pos+4].decode('ascii',errors='replace')
        size=struct.unpack_from('<Q',data,pos+4)[0]
        if size>len(data)-pos-12: raise ValueError('invalid chunk size')
        yield tag,data[pos+12:pos+12+size]
        pos+=12+size

def index(path):
    entries=[]
    with path.open('rb') as f:
        header=f.read(19)
        if header[:11]!=MAGIC: raise ValueError('not standard XP3')
        offset=struct.unpack_from('<Q',header,11)[0]
        for _ in range(16):
            f.seek(offset);flag=f.read(1)[0]
            packed=struct.unpack('<Q',f.read(8))[0]
            raw=struct.unpack('<Q',f.read(8))[0] if flag&1 else packed
            if max(raw,packed)>64*1024*1024:raise ValueError('index too big')
            data=f.read(packed)
            if flag&1:data=zlib.decompress(data)
            assert len(data)==raw
            for tag,chunk in chunks(data):
                if tag!='File':continue
                item={}
                for sub,d in chunks(chunk):
                    if sub=='info':
                        flags,original,size,n=struct.unpack_from('<IQQH',d)
                        item.update(name=d[22:22+n*2].decode('utf-16-le'),flags=flags,original=original,packed=size)
                    elif sub=='segm':item['segments']=[struct.unpack_from('<IQQQ',d,i) for i in range(0,len(d),28)]
                    elif sub=='adlr':item['adler']=struct.unpack_from('<I',d)[0]
                entries.append(item)
            if not flag&128:break
            offset=struct.unpack('<Q',f.read(8))[0]
    return entries

def payload(path,item):
    if item['original']>64*1024*1024:raise ValueError('sample too big')
    blocks=[]
    with path.open('rb') as f:
        for flags,offset,original,packed in item['segments']:
            f.seek(offset);data=f.read(packed)
            if flags&1:data=zlib.decompress(data)
            assert len(data)==original
            blocks.append(data)
    data=b''.join(blocks);assert len(data)==item['original']
    return data

def decode_text(data):
    if data.startswith(b'\xff\xfe'):return data[2:].decode('utf-16-le'), 'utf-16-le'
    if data.startswith(b'\xef\xbb\xbf'):return data[3:].decode('utf-8'),'utf-8-sig'
    if data.startswith(b'\xfe\xfe'):return None,'kirikiri encoded text'
    for encoding in ['utf-8','cp932','gb18030']:
        try:
            text=data.decode(encoding)
            if '\x00' in text: continue
            return text,encoding
        except UnicodeError:pass
    return None,'unknown/binary'

