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

    def encode(self):
        msg = self._get_message()
        h = hashlib.sha256(msg)
        return msg+h.digest()

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
            self.var_uuid = uuid.uuid5(self._uuid, self.var) #uuid obj
            self._data = size_var + self._var + self.var_uuid.bytes

    def decode(self, msg):
        #print (44*'_')
        data = super(TypeVariable, self).decode(msg)
        size = varint.decode_bytes( data )
        size_bytes_len = len(varint.encode( size ))
        self._var = data[size_bytes_len:size_bytes_len+size]
        self._var_uuid = data[size_bytes_len+size : size_bytes_len+size+UUID_SIZE]
        self.var = self._var.decode("utf-8")
        
        assert uuid.uuid5(self._uuid,str(self.var)).bytes == self._var_uuid
        print ([size, self.var])

        
TEST_BLOB = b'4kdsfja;slkfdj'
x=Blob( TEST_BLOB )


msg =  x.encode() 

#print (msg, len(msg), len(TEST_BLOB)  )

Blob().decode( msg )

a=TypeVariable('a')
msg = a.encode()

TypeVariable().decode( msg )
