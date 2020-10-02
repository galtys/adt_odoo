import uuid
import hashlib
import varint

GALTYS_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS,'galtys.com')
UUID_SIZE = 16
SHA256_SIZE = 32

class Blob(object):
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'Blob')

    def __init__(self, data=None):
        self._data = data
    def get_sha256(self):
        pass
    
    def _get_message(self):
        return self._uuid.bytes + varint.encode( len(self._data) ) + self._data
    
    def hash(self):
        msg = self._get_message()
        h = hashlib.sha256(msg)
        return h.digest()
    
    def encode(self):
        msg = self._get_message()
        h = self.hash()
        return msg+h

    def decode(self, msg):
        uuid=msg[0:UUID_SIZE]
        assert self._uuid.bytes == uuid
        size = varint.decode_bytes( msg[UUID_SIZE:] )
        size_bytes_len = len(varint.encode( size ))
        
        self._data = msg[ UUID_SIZE+size_bytes_len: UUID_SIZE+size_bytes_len +size]

        sha256 = msg[UUID_SIZE+size_bytes_len +size : UUID_SIZE+size_bytes_len +size + SHA256_SIZE]
        assert sha256 == hashlib.sha256(self._get_message() ).digest()
        return self._data

    def get(self):
        return self._data

class TypeVariable(Blob):
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'TypeVariable')

    def __init__(self, var=None):
        if var is not None:
            self.var = var   #str
            self._var = bytes(var, 'utf-8') #bytes
            size_var = varint.encode( len(self._var) )
            #self.var_uuid = uuid.uuid5(self._uuid, self.var) #uuid obj
            self._data = size_var + self._var # + self.var_uuid.bytes

    def decode(self, msg):

        data = super(TypeVariable, self).decode(msg)
        size = varint.decode_bytes( data )
        size_bytes_len = len(varint.encode( size ))
        self._var = data[size_bytes_len:size_bytes_len+size]
        #self._var_uuid = data[size_bytes_len+size : size_bytes_len+size+UUID_SIZE]
        self.var = self._var.decode("utf-8")
        
        #assert uuid.uuid5(self._uuid,str(self.var)).bytes == self._var_uuid
        #print ([size, self.var])

class DataConstructor(Blob):
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'DataConstructor')
    def __init__(self, name=None, parameters=None):
        if parameters is None:
            parameters = []
            self.parameters = parameters
        if name is not None:
            self.name = name   #str
            self._name = bytes(self.name, 'utf-8') #bytes
            size_name = varint.encode( len(self._name) )
            #self.var_uuid = uuid.uuid5(self._uuid, self.var) #uuid obj

            count_params = varint.encode( len(parameters) )
            params = b''
            for p in parameters:
                params += p
            self._data = size_name + self._name + count_params + params
            
    def decode(self, msg):

        data = super(TypeVariable, self).decode(msg)
        size = varint.decode_bytes( data )
        size_bytes_len = len(varint.encode( size ))
        pos = size_bytes_len+size
        self._name = data[size_bytes_len:pos]
        self.name = self._name.decode("utf-8")
        count_params = varint.decode_bytes( data[pos:] )
                       
        count_params_size = len( varint.encode( count_params ) )
        pos = pos+=count_params_size
        parameters = []
        for i in range(count_params):
            p = data[ i*SHA256_SIZE: (i+1)+SHA256_SIZE ]
            parameters.append(p)
        self.parameters = parameters
        #assert uuid.uuid5(self._uuid,str(self.var)).bytes == self._var_uuid
        #print ([size, self.var])

    
TEST_BLOB = b'4kdsfja;slkfdj'
x=Blob( TEST_BLOB )


msg =  x.encode() 

#print (msg, len(msg), len(TEST_BLOB)  )

Blob().decode( msg )

a=TypeVariable('a')
print (a.hash() )
msg = a.encode()

aa = TypeVariable()
aa.decode( msg )
print( aa.hash() )
