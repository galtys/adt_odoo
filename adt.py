import uuid
import hashlib
import varint
import collections
import pprint

GALTYS_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS,'galtys.com')
UUID_SIZE = 16
SHA256_SIZE = 32

TYPE_REGISTRY = collections.OrderedDict()
DCONS_REGISTRY = collections.OrderedDict()
DCONS_TYPE_MAP = collections.OrderedDict()

def hash(a):
    return hashlib.sha256(a).digest()

def concat(a):
    ret=b''
    for x in a:
        ret += x
    return ret
#to convert raw to and from hex, use    b'\xbe\xef'.hex() and bytes.fromhex('beef')

def parse_data_var(pos, msg):
    size = varint.decode_bytes( msg[pos:] )
    size_bytes_len = len(varint.encode( size ))
    pos = pos + size_bytes_len
    data = msg[ pos : pos +size]
    pos = pos + size 
    return pos, data

def parse_data_fixed(pos, msg, size):
    data = msg[pos : pos + size]
    pos = pos + size
    return pos, data

def encode_data_var(data):
    size = varint.encode( len(data) )
    return size+data
def encode_number(a):
    return varint.encode( a )

def parse_number(pos, msg):
    n = varint.decode_bytes( msg[pos:] )
    n_len = len( varint.encode(n) )
    pos = pos+n_len
    return pos, n

class Blob(object):
    _type = 'Blob'
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,_type)

    def __init__(self, data=None):
        self._data = data
    def get_sha256(self):
        pass    
    def _get_message(self):
        return self._uuid.bytes + encode_data_var(self._data) 
    def hash(self):
        msg = self._get_message()
        h = hashlib.sha256(msg)
        return h.digest()
    def refhash(self):
        return self.hash()    
    def encode(self):
        msg = self._get_message()
        h = self.hash()
        return msg+h
    def decode(self, msg, pos=0):
        _pos_start = pos
        
        pos, uuid = parse_data_fixed(pos, msg, UUID_SIZE)
        
        assert self._uuid.bytes == uuid
        
        pos, self._data = parse_data_var(pos, msg)

        pos, sha256 = parse_data_fixed(pos, msg, SHA256_SIZE)

        assert sha256 == hashlib.sha256(self._get_message() ).digest()
        return pos-_pos_start, self._data
    
    def get(self):
        return self._data
    def __repr__(self):
        return "<%s %s>"%(self._type, self.refhash().hex())
    

class TypeVariable(Blob):
    _type = 'TypeVariable'
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,_type)

    def __init__(self, type_name=None, var=None):
        if type_name and var:
            self.type_name = type_name
            self.var = var   #str
            self._var = bytes(var, 'utf-8') #bytes
            self._type_name = bytes(type_name, 'utf-8')
            self.init()
            
    def init(self):
            self._data = encode_data_var(self._type_name) + encode_data_var(self._var)
#    def to_bytes(self, a):
#        return None
#    def from_bytes(self, pos, b):
#        return None
    def refhash(self):
        h = hashlib.sha256(self._uuid.bytes + self._type_name + self._var)
        return h.digest()
    def decode(self, msg, pos=0):

        _pos, data = super(TypeVariable, self).decode(msg, pos=pos)
        pos=0
        pos, self._type_name = parse_data_var(pos, data)        
        pos, self._var = parse_data_var(pos, data)
        
        self.type_name = self._type_name.decode("utf-8")
        self.var = self._var.decode("utf-8")
        self.init()
        return _pos
    
    def get_var(self):
        return self.var
    def __repr__(self):
        return "<%s %s %s %s>"%(self._type, self.refhash().hex(), self.type_name, self.var)


class DataConstructor(Blob):
    _type = 'DataConstructor'
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,_type)
    def __init__(self, type_name=None, cons_name=None,
                 args=None, to_bytes=None, from_bytes=None,
                 encode_hash=True):
        if args is None:
             args = []
        self.args = args
        self.encode_hash = encode_hash #for types with just one data constructor, hash can be disabled
        self.to_bytes =to_bytes
        self.from_bytes = from_bytes
        if type_name and cons_name:
            self.type_name = type_name #str
            self._type_name = bytes(self.type_name, 'utf-8') #bytes
            self.cons_name = cons_name
            self._cons_name = bytes(self.cons_name, 'utf-8') #bytes

            params_data = b''
            for p in self.args:
                pb = p.refhash()
                #pb = bytes(p, 'utf-8')
                params_data += encode_data_var(pb)
            
            self._data = encode_data_var(self._type_name)+ \
                         encode_data_var(self._cons_name)+ \
                         encode_number( len(self.args) ) + params_data
            
    def refhash(self):
        h = hashlib.sha256(self._uuid.bytes + self._type_name + self._cons_name)
        return h.digest()
    def __repr__(self):
        return "<%s %s %s %s>"%(self._type, self.refhash().hex(), self.type_name, self.cons_name)
    def data_set(self, a):
        self.data = a
    def data_get(self):
        return self.data
    def data_encode(self):
        #print (44*'-', self.to_bytes)
        #print (self.data)
        #print (self)
        if self.data is None:
           x=b''
        else:
           x=self.to_bytes(self, self.data)
        if self.encode_hash: #datacons has before, value, data hash after
            h = self.hash()
            _hx = h+x
            h2 = hashlib.sha256( _hx ).digest()
            ret = _hx + h2
        else:
            ret =  x
        return ret
    def link_hash(self):
        msg = self.data_encode()
        assert self.encode_hash
        return msg[(-1)*SHA256_SIZE:]
    
    def data_decode(self, msg, pos=0):

        if self.encode_hash:
            h = self.hash()
            assert h == msg[pos:pos+SHA256_SIZE]
            pos += SHA256_SIZE

            if self.from_bytes is not None:
                pos, ret = self.from_bytes(self, pos, msg )
            else:
                ret = None
            
            h2d = msg[pos:pos+SHA256_SIZE]
            pos += SHA256_SIZE
        else:
            pos, ret = self.from_bytes(self, pos, msg )
        self.data = ret
        if self.encode_hash:
            #print (['CHECK: ', self.data])
            if self.from_bytes is not None:
                x=self.to_bytes(self, self.data)
                h = self.hash()
                h2 = hashlib.sha256( h+x ).digest()
                assert h2 == h2d            
        return pos
    
    def decode(self, msg, pos=0): 
        _pos, data = super(DataConstructor, self).decode(msg, pos=pos)
        pos=0
        pos, self._type_name = parse_data_var(pos, data)
        self.type_name = self._type_name.decode("utf-8")

        pos, self._cons_name = parse_data_var(pos, data)
        self.cons_name = self._cons_name.decode("utf-8")

        pos, self.no_args = parse_number(pos, data)

        args = []
        for i in range(self.no_args):

            pos, pb = parse_data_var(pos, data)
            #p = pb.decode('utf-8')
            args.append(pb)
        self.ref_args = args
        #pos, self.data_args = self.from_bytes(self, pos, data)
        return _pos
    
class DataType(Blob):
    _type = 'DataType'
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,_type)
    
    def __init__(self, type_name=None, type_vars=None, constructors = None, cons_name = None):
        if type_vars is None:
            type_vars = []
        self.type_vars = type_vars
        if constructors is None:
            constructors = []
        self.constructors = constructors
        if type_name:
            self.type_name = type_name
            #self.cons_name = cons_name
            self._type_name = bytes(self.type_name, 'utf-8')
            self.init()
            
    def init(self):            
            self._data = encode_data_var(self._type_name)
            #DataConstructor(type_name=type_name, cons_name=cons_name).encode()
            self._data += encode_number( len(self.type_vars) )
            
            for type_v in self.type_vars:
                #self._data += type_v.refhash()
                self._data += type_v.encode()
                
            self._data += encode_number( len(self.constructors) )
            
            for cons in self.constructors:
                #self._data += type_v.refhash()
                self._data += cons.encode()
    def __repr__(self):
        return "<%s %s %s>"%(self._type, self.refhash().hex(), self.type_name)
    def refhash(self):
        #due to the suport of recursive types, reference hash is (self._uuid + type_name)
        h = hashlib.sha256(self._uuid.bytes + self._type_name)
        return h.digest()

    def decode(self, msg, pos=0):
        _pos, data = super(DataType, self).decode(msg, pos=pos)
        pos =0
        pos, self._type_name = parse_data_var(pos, data)
        self.type_name = self._type_name.decode("utf-8")

        pos, self.no_type_vars = parse_number(pos, data)
        type_vars = []        
        for i in range(self.no_type_vars):
            t_v = TypeVariable()
            tv_size = t_v.decode(data, pos=pos)
            pos += tv_size
            type_vars.append( t_v)            
        self.type_vars = type_vars

        pos, self.no_cons = parse_number(pos, data)
        constructors = []        
        for i in range(self.no_cons):
            cons = DataConstructor()
            cons_size = cons.decode(data, pos=pos)
            pos += cons_size
            constructors.append( cons )            
        self.constructors = constructors
            
        self.init()
        return _pos
        #dc = DataConstructor()
        #dc.decode(data, pos=pos)
        #self._data = encode_data_var(self._type_name) #+ dc.encode()

def int64b_to_bytes(d, a, type_as_parent=False):
    ret=a.to_bytes(8, byteorder='big' )
    return ret

def int64b_from_bytes(d, pos, b, type_as_parent=False):
    ret=int.from_bytes(b[pos:pos+8], byteorder='big' )
    pos+=8
    return pos, ret

def int32b_to_bytes(d, a, type_as_parent=False):
    ret=a.to_bytes(4, byteorder='big' )
    return ret

def int32b_from_bytes(d, pos, b, type_as_parent=False):
    ret=int.from_bytes(b[pos:pos+4], byteorder='big' )
    pos+=4
    return pos, ret

def int8b_to_bytes(d, a, type_as_parent=False):
    ret=a.to_bytes(1, byteorder='big' )
    return ret

def int8b_from_bytes(d, pos, b, type_as_parent=False):
    ret=int.from_bytes(b[pos:pos+1], byteorder='big' )
    pos+=1
    return pos, ret

def string_to_bytes(d, a, type_as_parent=False):
    ab = bytes(a, 'utf-8') #bytes
    ret = encode_data_var(ab)
    return ret

def string_from_bytes(d, pos, b, type_as_parent=False):
    pos, _ret = parse_data_var(pos, b)
    return pos, _ret.decode('utf-8')


def binary_to_bytes(d, a, type_as_parent=False):
    #ab = bytes(a, 'utf-8') #bytes
    ret = encode_data_var(a)
    return ret

def binary_from_bytes(d, pos, b, type_as_parent=False):
    pos, _ret = parse_data_var(pos, b)
    return pos, _ret

def product_type_to_bytes(d, a, type_as_parent=False):
    ret = b''
    type_parent_obj = DCONS_TYPE_MAP[d.hash()]
    #print (type_parent_obj)
    #print (a)
    #if isinstance(a, list):
    if 1:
        for dc_t, dc_a in zip(d.args, a):
            
            #print (dc_a)
            c_rh, pyval = dc_a
            type_obj = DCONS_TYPE_MAP[c_rh]

            cons = DCONS_REGISTRY[c_rh]
            #print ([dc_t.type_name, cons.type_name])
            #print ('not ok')
            if dc_t.type_name == cons.type_name:
                #print (type_parent_obj, type_obj)
                cons.data_set( pyval)
                ret += cons.data_encode()
            else:
                cons.data_set( pyval)
                ret += cons.data_encode()
        
    return ret
def product_type_from_bytes(d, pos, b, type_as_parent=False):
    #cons_refhash = b[pos:pos+SHA256_SIZE]
    #pos += SHA256_SIZE
    ret = []
    cons = d #DCONS_REGISTRY[cons_refhash]
    type_parent_obj = DCONS_TYPE_MAP[d.hash()]
    if 1:
        for a in cons.args:
            c_rh = b[pos:pos+SHA256_SIZE]
            c = DCONS_REGISTRY[c_rh]

            obj_t = DCONS_TYPE_MAP[c_rh]
            #if type_parent_obj.hash() != obj_t.hash():
            pos = c.data_decode( b, pos=pos)
            ret.append( (c_rh, c.data_get()) )
        
    return pos, ret



if 1:
    _Int64 = DataType( type_name = 'Int64' )
    _Int32 = DataType( type_name = 'Int32' )
    _Int8 = DataType( type_name = 'Int8' )
    _String = DataType( type_name = 'String' )
    _Binary = DataType( type_name = 'Binary' )
        
    ConsInt64 = DataConstructor( type_name = 'Int64',
                             cons_name='ConsInt64',
                             args = [_Int64], #shoud be python buildin type int .. ?
                             to_bytes=int64b_to_bytes,  
                             from_bytes = int64b_from_bytes)
    ConsInt32 = DataConstructor( type_name = 'Int32',
                             cons_name='ConsInt32',
                             args = [_Int32],                                 
                             to_bytes=int32b_to_bytes,
                             from_bytes = int32b_from_bytes)
    ConsInt8 = DataConstructor( type_name = 'Int8',
                             cons_name='ConsInt8',
                             args = [_Int8],                                
                             to_bytes=int8b_to_bytes,
                             from_bytes = int8b_from_bytes)
    
    ConsString = DataConstructor( type_name = 'String',
                                  cons_name='ConsString',
                                  args = [_String],
                                  to_bytes=string_to_bytes,
                                  from_bytes = string_from_bytes)
    
    ConsBinary = DataConstructor( type_name = 'Binary',
                                  cons_name='ConsBinary',
                                  args = [_Binary],
                                  to_bytes=binary_to_bytes,
                                  from_bytes = binary_from_bytes)
    
    ConsBooleanTrue  =  DataConstructor( type_name = 'Boolean',
                                         cons_name='True')
    ConsBooleanFalse  = DataConstructor( type_name = 'Boolean',
                                         cons_name='False')
    
    Int64 = DataType( type_name = 'Int64', constructors=[ConsInt64] )
    Int32= DataType( type_name = 'Int32', constructors=[ConsInt32] )
    Int8 = DataType( type_name = 'Int8', constructors=[ConsInt8] )    
    String = DataType( type_name = 'String', constructors=[ConsString] )
    Binary = DataType( type_name = 'Binary', constructors=[ConsBinary] )
    Boolean = DataType( type_name = 'Boolean', constructors=[ConsBooleanTrue, ConsBooleanFalse] )

    TYPE_REGISTRY[ Int64.refhash() ] = Int64
    TYPE_REGISTRY[ Int32.refhash() ] = Int32
    TYPE_REGISTRY[ Int8.refhash() ] = Int8
    TYPE_REGISTRY[ String.refhash() ] = String
    TYPE_REGISTRY[ Binary.refhash() ] = Binary
    TYPE_REGISTRY[ Boolean.refhash() ] = Boolean


    #

    ConsContact = DataConstructor( type_name = 'Contact',
                                   cons_name='ConsContact',
                                   to_bytes=product_type_to_bytes,
                                   from_bytes = product_type_from_bytes,
                                   args = [String,String,Int64] ) #name,street,zip
    
    Contact = DataType( type_name = 'Contact', constructors=[ConsContact] )


    #


    a=TypeVariable(type_name='List', var='VARa')
    msg = a.encode()
    
    _List = DataType( type_name = 'List' )          #List is a recursive type
    ConsList = DataConstructor( type_name = 'List',
                                 cons_name='ConsList',
                                to_bytes=product_type_to_bytes,
                                from_bytes = product_type_from_bytes,
                                 args = [_List, a]) 

    ConsNil = DataConstructor( type_name = 'List',
                                to_bytes=product_type_to_bytes,
                               #from_bytes = product_type_list_from_bytes,
                               cons_name='ConsNil')
    
    List = DataType( type_name = 'List', type_vars=[a], constructors=[ConsList, ConsNil]  )
    TYPE_REGISTRY[ List.refhash() ] = List
    
    msg = List.encode()
    
    assert _List.refhash() == List.refhash()
    #

    TYPE_REGISTRY[ Contact.refhash() ] = Contact
    for k,v in TYPE_REGISTRY.items():
        for cons in v.constructors:
            DCONS_REGISTRY[ cons.hash() ] = cons
            DCONS_TYPE_MAP[ cons.hash() ] = v
    #print ('ConsList.hash(): ', ConsList.hash() )
    if 1:

        fp = open('test.bin', 'wb')

        #Nil
        ConsNil.data_set( None)
        
        msg = ConsNil.data_encode()
        linkhash  = ConsNil.link_hash()
        #fp.write(msg)
        
        #1
        input_data = [ (ConsBinary.hash()   , linkhash ),
                       (ConsString.hash(), 'Galtys Ltd') ]
        ConsList.data_set( input_data )
        msg = ConsList.data_encode()
        linkhash = ConsList.link_hash()

        sz=ConsList.data_decode(msg)
        #print ( ConsList.data_get() )
        print (sz,len(msg), linkhash)

        fp.write(msg)

        #2
        input_data = [ (ConsBinary.hash()   ,linkhash ),
                       (ConsString.hash(), 'Muf') ]    
        ConsList.data_set( input_data )
        msg = ConsList.data_encode()
        
        linkhash = ConsList.link_hash()
        sz=ConsList.data_decode(msg)
        #print ( ConsList.data_get() )        
        print (sz, len(msg),linkhash)
        fp.write(msg)

        #3
        input_data = [ (ConsBinary.hash()   , linkhash ),
                       (ConsString.hash(), 'No43') ]    
        ConsList.data_set( input_data )
        msg = ConsList.data_encode()
        linkhash = ConsList.link_hash()
        sz=ConsList.data_decode(msg)
        #print ( ConsList.data_get() )        
        print (sz, len(msg), linkhash)
        fp.write(msg)

        fp.close()

    if 1:

        test_map = {}
        fp = open('test.bin', 'br')
        msg = fp.read()
        fp.close()
        #print (msg)

        pos = 0
        N = len(msg)
        cont = True
        while cont:
            HEAD = msg[pos:pos+SHA256_SIZE]
            cons = DCONS_REGISTRY[HEAD]
            #print (cons)
            pos = cons.data_decode(msg, pos=pos)
            ret = cons.data_get()
            #conshash, val = ret
            
            #if len(ret)>0:
            #    
            #print (val)
            #else:
            print (ret)
            if pos>=N:
                cont=False
        #linkhash = ConsList.link_hash()
    if 0:
        input_data = [ (ConsString.hash(), 'Galtys Ltd'),
                       (ConsString.hash(), '88 LowerMarsh'),
                       (ConsInt64.hash(), 33415) ]


        #
        ConsContact.data_set( input_data )
        msg = ConsContact.data_encode()

        #print (msg)

        pos = ConsContact.data_decode(msg)
    
if 0:
        
    msg = dc.encode()
    dc2 = DataConstructor()
    dc2.decode(msg)
    assert dc.hash()==dc2.hash()

#print (dc.hash() )

def list_cons_to_bytes(d, a):
    ab = bytes(a, 'utf-8') #bytes
    ret = encode_data_var(ab)
    return ret

def string_from_bytes(d, pos, b):
    pos, _ret = parse_data_var(pos, b)
    return pos, _ret.decode('utf-8')


