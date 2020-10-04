import uuid
import hashlib
import varint

GALTYS_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS,'galtys.com')
UUID_SIZE = 16
SHA256_SIZE = 32

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
        #print ([self._uuid.bytes, uuid])
        
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
            
    def refhash(self):
        h = hashlib.sha256(self._uuid.bytes + self._type_name + self._var)
        return h.digest()
    def decode(self, msg, pos=0):

        _pos, data = super(TypeVariable, self).decode(msg, pos=pos)
        print ('decode type var, _pos: %s, len(msg): %s' % (_pos, len(msg)) )
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
    def __init__(self, type_name=None, cons_name=None, args=None):
        if args is None:
            args = []
        self.args = args
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
            
    def decode(self, msg, pos=0): 
        _pos, data = super(DataConstructor, self).decode(msg, pos=pos)
        #print (_pos, pos, data)
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
        return _pos
    
class DataType(Blob):
    _type = 'DataType'
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,_type)
    
    def __init__(self, type_name=None, type_vars=None, constructors = None, cons_name = None):
        if type_name and type_vars:
            self.type_name = type_name
            #self.cons_name = cons_name
            self._type_name = bytes(self.type_name, 'utf-8')
            if type_vars is None:
                type_vars = []
            self.type_vars = type_vars
            self.init()
            
    def init(self):            
            self._data = encode_data_var(self._type_name) #DataConstructor(type_name=type_name, cons_name=cons_name).encode()

            self._data += encode_number( len(self.type_vars) )
            
            for type_v in self.type_vars:
                #self._data += type_v.refhash()
                self._data += type_v.encode()
            
    def refhash(self): #due to the suport of recursive types, reference hash is (self._uuid + type_name)
        h = hashlib.sha256(self._uuid.bytes + self._type_name)
        return h.digest()

    def decode(self, msg, pos=0):
        _pos, data = super(DataType, self).decode(msg, pos=pos)
        #print ([_pos,data])
        pos =0
        pos, self._type_name = parse_data_var(pos, data)
        #print (pos, data)
        self.type_name = self._type_name.decode("utf-8")
                                         
        pos, self.no_type_vars = parse_number(pos, data)
        type_vars = []
        print ('number of type vars: ', self.no_type_vars)
        for i in range(self.no_type_vars):
            t_v = TypeVariable()
            print ('\n')
            print ('decoding type var inside of datatype')
            #print ('decode t_v, pos', pos)
            
            tv_size = t_v.decode(data, pos=pos)
            print ('data: ', data[pos:], 'tv_size', tv_size )            
            pos += tv_size
            #print ('decode t_v after, pos', pos)
            print (t_v)
            type_vars.append( t_v)
            
        self.type_vars = type_vars
            #pos, tv_data =
            #pos, ref_hash = parse_data_var(pos, data)
            
        self.init()
        return _pos
        #dc = DataConstructor()
        #dc.decode(data, pos=pos)
        #self._data = encode_data_var(self._type_name) #+ dc.encode()

a=TypeVariable(type_name='List', var='VARa')

b=TypeVariable(type_name='List', var='VARb')
msg = a.encode()
print ('X', a, len(msg) )

aa = TypeVariable()
sz = aa.decode( msg )
#print( aa.hash() )
#print ('type var a, sz: %s, len msg: %s' % (sz, len(msg)) )


if 0:
    dc = DataConstructor( type_name = 'Boolean', cons_name='True')
    msg = dc.encode()
    dc2 = DataConstructor()
    dc2.decode(msg)
    assert dc.hash()==dc2.hash()

#print (dc.hash() )


if 1:
    #print (dc2.type_name, dc2.cons_name)
    #print (dc2.hash() )
    list_cons = DataConstructor( type_name = 'List',
                                 cons_name='ListCons',
                                 args = [a])

    st = DataType( type_name = 'List', type_vars=[a,b] )
    msg = st.encode()
    st2 = DataType()
    st2.decode(msg)

    assert st.hash() == st2.hash()


