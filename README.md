# adt_odoo
adt_odoo experiment


TypeVariable: uuid, size, name, uuid -> sha256
VarIntType: uuid, size -> sha256
BytesType:      -> sha256
Int64 -> sha256

DataConstructor: uuid, name, count, [sha256 of type variables or types];

Type: uuid, size, name, uuid,
      count, [sha256 of type variables],
      count, [sha256 of DataConstructors ]
