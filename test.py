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
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'Blob')

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

        pos, uuid = parse_data_fixed(pos, msg, UUID_SIZE)
        #print ([self._uuid.bytes, uuid])
        assert self._uuid.bytes == uuid
        
        pos, self._data = parse_data_var(pos, msg)

        pos, sha256 = parse_data_fixed(pos, msg, SHA256_SIZE)

        assert sha256 == hashlib.sha256(self._get_message() ).digest()
        return pos, self._data
    
    def get(self):
        return self._data
    

class TypeVariable(Blob):
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'TypeVariable')

    def __init__(self, type_name=None, var=None):
        if type_name and var:
            self.type_name = type_name
            self.var = var   #str
            self._var = bytes(var, 'utf-8') #bytes
            self._type_name = bytes(type_name, 'utf-8')            
            self._data = encode_data_var(self._var) + encode_data_var(self._var)
            
    def refhash(self):
        h = hashlib.sha256(self._uuid + self._type_name + self._var)
        return h.digest()
            
    def decode(self, msg, pos=0):

        _pos, data = super(TypeVariable, self).decode(msg, pos=pos)
        pos=0
        pos, self._type_name = parse_data_var(pos, data)        
        pos, self._var = parse_data_var(pos, data)
        
        self.type_name = self._type_name.decode("utf-8")        
        self.var = self._var.decode("utf-8")

        return pos
    
    def get_var(self):
        return self.var

class DataConstructor(Blob):
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'DataConstructor')
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
                pb = bytes(p, 'utf-8')
                params_data += encode_data_var(pb)
            
            self._data = encode_data_var(self._type_name)+ \
                         encode_data_var(self._cons_name)+ \
                         encode_number( len(self.args) ) + params_data

    def refhash(self):
        h = hashlib.sha256(self._uuid + self._type_name + self._cons_name)
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
            p = pb.decode('utf-8')
            args.append(p)
        self.args = args
        return pos
    
class DataType(Blob): 
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'Type')
    
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
        h = hashlib.sha256(self._uuid + self._type_name)
        return h.digest()

    def decode(self, msg, pos=0):
        _pos, data = super(DataType, self).decode(msg)
        #print ([_pos,data])
        
        pos, self._type_name = parse_data_var(pos, data)
        #print (pos, data)
        self.type_name = self._type_name.decode("utf-8")
                                         
        pos, self.no_type_vars = parse_number(pos, data)
        type_vars = []
        for i in range(self.no_type_vars):
            t_v = TypeVariable()
            pos = t_v.decode(data, pos=pos)
            type_vars.append( t_v)
        self.type_vars = type_vars
            #pos, tv_data =
            #pos, ref_hash = parse_data_var(pos, data)
            
        self.init()                                
        #dc = DataConstructor()
        #dc.decode(data, pos=pos)
        #self._data = encode_data_var(self._type_name) #+ dc.encode()

TEST_BLOB = b'4kdsfja;slkfdj'
x=Blob( TEST_BLOB )

msg =  x.encode() 

#print (msg, len(msg), len(TEST_BLOB)  )

Blob().decode( msg )

a=TypeVariable(type_name='List', var='a')
#print (a.hash() )
msg = a.encode()

aa = TypeVariable()
aa.decode( msg )
#print( aa.hash() )



dc = DataConstructor( type_name = 'Boolean', cons_name='True')
msg = dc.encode()
#print (dc.hash() )


dc2 = DataConstructor()
dc2.decode(msg)
assert dc.hash()==dc2.hash()
#print (dc2.type_name, dc2.cons_name)
#print (dc2.hash() )

st = DataType( type_name = 'List', type_vars=[a] )
msg = st.encode()
st2 = DataType()
st2.decode(msg)

assert st.hash() == st2.hash()


dc = DataConstructor( type_name = 'Partner',
                      cons_name='Partner',
                      args = ['name','street','street2'])
msg = dc.encode()
print (msg)
#print (dc.hash() )


dc2 = DataConstructor()
dc2.decode(msg)

assert dc.hash()==dc2.hash()


