# Proyecto 3 - Simulación de HBase con Python

El proyecto consiste en imitar el funcionamiento básico de la base de datos columnar HBase, implementando los siguientes comandos:

### help - Devuelve información sobre cada comando disponible.
```
help <command>?
```

## DDL:
### create_namespace
Crea un nuevo namespace en el directorio.
```
create_namespace <namespace>
```
### list_namespaces
Lista todos los namespaces disponibles.
```
list_namespaces
```
### create
 Crea una nueva tabla con los column families descritos en el namespace indicado. Si no se especifica ningún namespace, se utiliza el 'default'.
```
create <namespace>?:<table_name> [column_families]
```
### list
Lista todas las tablas que coincidan con los parámetros dados. Si se especifica una regex, listará todas las tablas que coincidan. Si no se especifica el nombre del namespace, se buscará en el namespace 'default'.
```
list [ <namespace>?:regex ]?
```
### disable
Deshabilita la tabla indicada. Si no se especifica el namespace, se tomará el namespace 'default'.
```
disable <namespace>?:<table_name>
```
### enable
Habilita la tabla indicada. Si no se especifica el namespace, se tomará el namespace 'default'.
```
enable <namespace>?:<table_name>
```
### is_enabled
Verifica el estado de la tabla descrita. Si no se especifica el namespace, se tomará el namespace 'default'.
```
is_enabled <namespace>?:<table_name>
```
### alter
Modifica la tabla descrita. El método 'add' añade el column family a la tabla, mientras que el método 'delete' la elimina de la tabla, así como todos los registros asignados a ella. Si no se especifica el namespace, se tomará el namespace 'default'.
```
alter <namespace>?:<table_name> {NAME => <column_name>, [ METHOD => 'add' | 'delete' ]?}
```
### drop
Elimina la tabla descrita y todo su contenido. Si no se especifica el namespace, se tomará el namespace 'default'.
```
drop <namespace>?:<table_name>
```
### drop_all
Elimina todas las tablas que coincidan con los parámetros dados. Si se especifica una regex, eliminará las tablas que coincidan. Si no se especifica el namespace, se tomará el namespace 'default'.
```
drop_all [ <namespace>?:regex ]?
```
### describe
Proporciona una breve descripción de la tabla indicada. Si no se especifica el namespace, se tomará el namespace 'default'.
```
describe <namespace>?:<table_name>
```

## DML:
### put
Crea un nuevo registro dentro de la tabla y columna indicadas, con el row_Id dado y el nuevo valor. Si ya hay un registro con esta combinación de
> <namespace\>:<table_name\> <row_Id\> y <column_family\>:<column\>

se agregará un segundo valor como el más actualizado, manteniendo una copia de seguridad del antiguo. Si no se especifica el namespace, se tomará el namespace 'default'.
```
put <namespace>?:<table_name> <row_Id> <column_family>:<column> <value>
```
### get
Devuelve la fila que coincida con el row_id dado. Se pueden especificar las columnas que se deben devolver, con su column family respectivo. Si no se especifica el namespace, se tomará el namespace 'default'.
```
get <namespace>?:<table_name> <row_Id> [ <column_family>:<column> ]?
```
### scan
Devuelve todas las filas de la tabla indicada. Si no se especifica el namespace, se tomará el namespace 'default'.
```
scan <namespace>?:<table_name>
```
### delete
Elimina la fila que coincida con todos los parámetros. Si no se especifica el namespace, se tomará el namespace 'default'.
```
delete <namespace>?:<table_name> <row_Id> <column_family>:<column> <timestamp>
```
### deleteall
Elimina todas las filas con el row_Id indicado. Si no se especifica el namespace, se tomará el namespace 'default'.
```
deleteall <namespace>?:<table_name> <row_Id>
```
### count
Cuenta la cantidad de filas en la tabla indicada. Si no se especifica el namespace, se tomará el namespace 'default'.
```
count <namespace>?:<table_name>
```
### truncate
Elimina todo el contenido de la tabla, manteniendo la estructura básica. Si no se especifica el namespace, se tomará el namespace 'default'.
```
truncate <namespace>?:<table_name>
```

# Estructura de archivos
Al ejecutar el proyecto se creará el namespace 'default', de manera que no es necesario crear otro namespace para comenzar a utilizar los comandos descritos.

Los datos se almacenarán en el directorio
> namespaces/<namespace\>/<table\>/

La estructura de los archivos se describe en formato json, con una sección de metadata en la que se especifica la tabla, column families, región, fecha de creación y si la tabla está activa. Luego, está la sección 'data', en donde se almacenará cada registro en la estructura:
> row_id >> column_family >> column >> timestamp:value