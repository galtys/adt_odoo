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

class Blob(object):
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'Blob')

    def __init__(self, data=None):
        self._data = data
    def get_sha256(self):
        pass    
    def _get_message(self):
        return self._uuid.bytes + encode_data_var(self._data) #varint.encode( len(self._data) ) + self._data
    def hash(self):
        msg = self._get_message()
        h = hashlib.sha256(msg)
        return h.digest()
    def encode(self):
        msg = self._get_message()
        h = self.hash()
        return msg+h
    def decode(self, msg, pos=0):

        pos, uuid = parse_data_fixed(pos, msg, UUID_SIZE)
        
        assert self._uuid.bytes == uuid
        
        pos, self._data = parse_data_var(pos, msg)

        pos, sha256 = parse_data_fixed(pos, msg, SHA256_SIZE)

        assert sha256 == hashlib.sha256(self._get_message() ).digest()
        return pos, self._data
    
    def get(self):
        return self._data
    
class TypeVariable(Blob):
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'TypeVariable')

    def __init__(self, var=None):
        if var is not None:
            self.var = var   #str
            self._var = bytes(var, 'utf-8') #bytes
            self._data = encode_data_var(self._var)

    def decode(self, msg, pos=0):

        _pos, data = super(TypeVariable, self).decode(msg)

        pos, self._var = parse_data_var(pos, data)
        self.var = self._var.decode("utf-8")
        return pos
    
    def get_var(self):
        return self.var

class DataConstructor(Blob):
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'DataConstructor')
    def __init__(self, type_name=None, cons_name=None, parameters=None):
        if parameters is None:
            parameters = []
            self.parameters = parameters
        if type_name and cons_name:
            self.type_name = type_name #str
            self._type_name = bytes(self.type_name, 'utf-8') #bytes
            self.cons_name = cons_name
            self._cons_name = bytes(self.cons_name, 'utf-8') #bytes
            #count_params = varint.encode( len(parameters) )
            #params = b''
            #for p in parameters:
            #    params += p
            self._data = encode_data_var(self._type_name)+encode_data_var(self._cons_name) #+ count_params + params
            
    def decode(self, msg, pos=0): 
        _pos, data = super(DataConstructor, self).decode(msg)

        pos, self._type_name = parse_data_var(pos, data)
        self.type_name = self._type_name.decode("utf-8")

        pos, self._cons_name = parse_data_var(pos, data)
        self.cons_name = self._cons_name.decode("utf-8")
                
        #count_params = varint.decode_bytes( data[pos:] )                       
        #count_params_size = len( varint.encode( count_params ) )
        #pos = pos+=count_params_size
        #parameters = []
        #for i in range(count_params):
        #    p = data[ i*SHA256_SIZE: (i+1)+SHA256_SIZE ]
        #    parameters.append(p)
        #self.parameters = parameters
    
class TypeRef(Blob):
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'Type')
    
class SimpleType(Blob):
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'Type')
    
    def __init__(self, type_name=None, cons_name = None):
        if type_name and cons_name:
            self.type_name = type_name
            #self.cons_name = cons_name
            self._type_name = bytes(self.type_name, 'utf-8')
            self._data = encode_data_var(self._type_name) + DataConstructor(type_name=type_name, cons_name=cons_name).encode()

    def decode(self, msg, pos=0):
        _pos, data = super(SimpleType, self).decode(msg)

        pos, self._type_name = parse_data_var(pos, data)
        self.type_name = self._type_name.decode("utf-8")
        
        dc = DataConstructor()
        dc.decode(data, pos=pos)
        self._data = encode_data_var(self._type_name) + dc.encode()

TEST_BLOB = b'4kdsfja;slkfdj'
x=Blob( TEST_BLOB )

msg =  x.encode() 

#print (msg, len(msg), len(TEST_BLOB)  )

Blob().decode( msg )

a=TypeVariable('a')
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

st = SimpleType( type_name = 'Boolean', cons_name='True')
msg = st.encode()
st2 = SimpleType()
st2.decode(msg)
