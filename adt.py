import uuid
import hashlib
import varint

import logging

_logger = logging.getLogger(__name__)

GALTYS_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS,'galtys.com')
UUID_SIZE = 16
SHA256_SIZE = 32

def parse_data_var(msg):
    pos = 0
    size = varint.decode_bytes( msg[pos:] )
    size_bytes_len = len(varint.encode( size ))
    pos = pos + size_bytes_len
    data = msg[ pos : pos +size]
    pos = pos + size 
    return pos, data, msg[pos:]

def parse_data_fixed(msg, size):
    pos = 0
    data = msg[pos : pos + size]
    pos = pos + size
    return pos, data, msg[pos:]

def parse_number(msg):
    pos=0
    n = varint.decode_bytes( msg[pos:] )
    n_len = len( varint.encode(n) )
    pos = pos+n_len
    return pos, n, msg[pos:]

def encode_data_var(data):
    size = varint.encode( len(data) )
    return size+data
def encode_number(a):
    return varint.encode( a )


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
        ret = msg+h
        _logger.info("Encoded blob: %s, size: %s", self._uuid,
                     len(ret) )
        return ret
    def decode(self, msg):

        size, uuid, msg = parse_data_fixed(msg, UUID_SIZE)
        pos += size
        #print ([self._uuid.bytes, uuid])
        assert self._uuid.bytes == uuid
        
        size, self._data, msg = parse_data_var(msg)
        pos += size
        
        size, sha256, msg = parse_data_fixed(msg, SHA256_SIZE)
        pos += size
        
        assert sha256 == hashlib.sha256(self._get_message() ).digest()
        
        return pos, self._data, msg
    
    def get(self):
        return self._data
    def __repr__(self):
        return self.refhash().hex()

class TypeVariable(Blob):
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'TypeVariable')

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
            
    def decode(self, msg):

        _pos_size, data, msg = super(TypeVariable, self).decode(msg)
        #pos=0
        pos, self._type_name,data = parse_data_var(data)
        pos, self._var,data = parse_data_var(data)
        
        self.type_name = self._type_name.decode("utf-8")        
        self.var = self._var.decode("utf-8")
        self.init()
        return _pos_size
    
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
            self.init()
            
    def init(self):
        params_data = b''
        for p in self.args:
            #pb = bytes(p, 'utf-8')
            #params_data += encode_data_var(pb)
            params_data += p.refhash()

        self._data = encode_data_var(self._type_name)+ \
                     encode_data_var(self._cons_name)+ \
                     encode_number( len(self.args) ) + params_data

    def refhash(self):
        h = hashlib.sha256(self._uuid.bytes + self._type_name + self._cons_name)
        return h.digest()
            
    def decode(self, msg): 
        _pos, data,msg = super(DataConstructor, self).decode(msg)
        #print (_pos, pos, data)
        pos=0
        size, self._type_name,data = parse_data_var(data)
        self.type_name = self._type_name.decode("utf-8")
        pos += size
        
        size, self._cons_name,data= parse_data_var(data)
        self.cons_name = self._cons_name.decode("utf-8")
        pos += size
        
        size, self.no_args, data = parse_number(data)
        pos += size
        
        ref_args = []
        for i in range(self.no_args):            
            size, pb,data = parse_data_var(data)
            #p = pb.decode('utf-8')
            ref_args.append(pb)
        self.ref_args = ref_args
        return pos
    
class DataType(Blob): 
    _uuid = uuid.uuid5(GALTYS_NAMESPACE,'Type')
    
    def __init__(self, type_name=None, type_vars=None, constructors = None, cons_name = None):
        if constructors is None:
            constructors = []
        self.constructors = constructors
        if type_vars is None:
            type_vars = []
        self.type_vars = type_vars
            
        if type_name:
            self.type_name = type_name
            #self.cons_name = cons_name
            self._type_name = bytes(self.type_name, 'utf-8')
            self.init()
            
    def init(self):
            self._data = b''
            #self._data += b'TYPE_NAME'
            self._data = encode_data_var(self._type_name) #DataConstructor(type_name=type_name, cons_name=cons_name).encode()
            
            #self._data += b'LEN VARS'
            self._data += encode_number( len(self.type_vars) )
            
            #self._data += b'VARS'
            for type_v in self.type_vars:
                #self._data += type_v.refhash()
                var_msg = type_v.encode()
                print ('var msg len: ', len(var_msg) )
                self._data += var_msg
                
            #self._data += b'LEN CONS'
            number_of_cons = encode_number( len(self.constructors) )
            print ('number_of_cons', number_of_cons)
            self._data += number_of_cons

            #self._data += b'CONS'
            for c in self.constructors:
                c_msg = c.encode()
                print ('c msg len: ', len(c_msg) )
                self._data += c_msg

                
            
    def refhash(self): #due to the suport of recursive types, reference hash is (self._uuid + type_name)
        h = hashlib.sha256(self._uuid.bytes + self._type_name)
        return h.digest()

    def decode(self, msg, pos=0):
        _pos, data = super(DataType, self).decode(msg, pos=pos)
        #print ([_pos,data])
        #os= len(b'TYPE_NAME')
        pos, self._type_name = parse_data_var(pos, data)
        #print (pos, data)
        self.type_name = self._type_name.decode("utf-8")

        #pos += len(b'LEN VARS')
        pos, self.no_type_vars = parse_number(pos, data)
        print ('no type vars: ', self.no_type_vars)
        type_vars = []
        for i in range(self.no_type_vars):
            t_v = TypeVariable()
            size = t_v.decode(data, pos=pos)
            print ('tv: %s, size: %s' % (t_v, size) )
            pos += size
            type_vars.append( t_v)
        self.type_vars = type_vars

        
        print ('data', data)
        #pos = pos +4
        pos, self.no_constructors = parse_number(pos, data)
        constructors = []
        print ('no cons: ', self.no_constructors)
        for i in range(self.no_constructors):
            c = DataConstructor()
            size = c.decode(data, pos=pos)
            print ('cons size: ', size)
            pos = pos + size
            constructors.append( c )
            #pos, tv_data =
            #pos, ref_hash = parse_data_var(pos, data)
        self.constructors = constructors
        self.init()                                
        #dc = DataConstructor()
        #dc.decode(data, pos=pos)
        #self._data = encode_data_var(self._type_name) #+ dc.encode()

#TEST_BLOB = b'4kdsfja;slkfdj'
#x=Blob( TEST_BLOB )

#msg =  x.encode() 

#print (msg, len(msg), len(TEST_BLOB)  )
#xx=Blob()
#xx.decode( msg )
#assert x.hash()==xx.hash()
#assert x.refhash()==xx.refhash()



a=TypeVariable(type_name='List', var='a')
#print (a.hash() )
msg = a.encode()

list_a = TypeVariable()
list_a.decode( msg )

#print (a._uuid, a._type_name, a._var)
#print (aa._uuid, aa._type_name, aa._var)
print ('type var a: ', list_a)
#print( aa.hash() )



bool_true = DataConstructor( type_name = 'Boolean', cons_name='True')
bool_false = DataConstructor( type_name = 'Boolean', cons_name='False')

msg = bool_true.encode()
#print (dc.hash() )
#print (dc)

dc2 = DataConstructor()
dc2.decode(msg)
assert bool_true.hash()==dc2.hash()
#print (dc2.type_name, dc2.cons_name)
#print (dc2.hash() )





list_cons = DataConstructor( type_name = 'List',
                      cons_name='ListConstructor',
                      args = [list_a])
list_nil = DataConstructor( type_name = 'List',
                            cons_name ='Nil')
msg = list_cons.encode()

dc2 = DataConstructor()
dc2.decode(msg)

assert list_cons.hash()==dc2.hash()







st = DataType( type_name = 'List',
               type_vars=[list_a],
               constructors=[list_cons,list_nil] )
msg = st.encode()
st2 = DataType()
#st2.decode(msg)
#print (st, st2)
#assert st.hash() == st2.hash()

#print (st2.type_vars)




