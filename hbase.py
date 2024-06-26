import os
import json
from time import time
import glob
import shutil
import re
from datetime import datetime
import shutil
from tabulate import tabulate
import textwrap

class HBase:
    def __init__(self):
        self.metadata_file = 'metadata.json'
        self.metadata = {}
        self.readMetadata()

        if 'default' not in self.metadata:
            self.createNamespace('default')
            self.writeMetadata()

    def verifyTable(self,name):
        if ':' in name:
            current_namespace, name = name.split(':')
        else: current_namespace = 'default'

        if current_namespace == '':
            return '\033[91mERROR: Debe especificar el namespace.\033[0m'
        
        if name == '':
            return '\033[91mERROR: Debe especificar el nombre de la tabla.\033[0m'

        if current_namespace not in self.metadata:
            return '\033[91mNamespaceNotFoundException: El namespace especificado no existe.\033[0m'
        
        tables = [(namespace,t,atributes['families'],atributes['enabled'],atributes['region']) for namespace,tables in self.metadata.items() for t,atributes in tables.items() if namespace == current_namespace and t == name]
        return tables[0] if len(tables) > 0 else (current_namespace,name)

    def readMetadata(self):
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)

    def writeMetadata(self):
        for namespace in self.metadata:
            self.metadata[namespace] = {k: self.metadata[namespace][k] for k in sorted(self.metadata[namespace])}
            
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=4)

    def createNamespace(self, name):
        inicio = time()
        if name in self.metadata:
            return f"\033[91mNamespaceExistsException: El namespace '{name}' ya existe\033[0m"
                
        self.metadata[name] = {}

        self.writeMetadata()

        namespace_path = os.path.join('namespaces', name)
        os.makedirs(namespace_path, exist_ok=True)
        return f'\033[95m0 \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'            

    def createTable(self, name, columnFamilies, embedded = False):
        inicio = time()
        result = ''
        
        if ':' in name:
            current_namespace, name = name.split(':')
        else: current_namespace = 'default'

        if current_namespace == '':
            return '\033[91mERROR: Debe especificar el namespace.\033[0m' if not embedded else False
        
        if name == '':
            return '\033[91mERROR: Debe especificar el nombre de la tabla.\033[0m' if not embedded else False

        if current_namespace not in self.metadata:
            return '\033[91mNamespaceNotFoundException: El namespace especificado no existe.\033[0m' if not embedded else False
        
        if not len(columnFamilies):
            return '\033[91mERROR: Debe especificar al menos una column family.\033[0m' if not embedded else False
        
        tables = self.metadata[current_namespace]

        if name in tables:
            return f"\033[91mTableExistsException: La tabla '{name}' ya existe dentro del namespace {current_namespace}\033[0m" if not embedded else False
        
        tables[name] = {'families': columnFamilies, 'enabled':True, 'region': len(self.metadata[current_namespace])}
        self.writeMetadata()

        table_path = os.path.join(f'namespaces/{current_namespace}', name)
        os.makedirs(table_path, exist_ok=True)
        
        result += f'\033[95m0 \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds\n'
        result += f'=> \033[91mHbase::Table\033[0m - {name}'
        return result if not embedded else True

    def listTables(self, param=None):
        inicio = time()
        regex = None
        current_namespace = 'default'
        if not param:
            regex = '.*'
        elif ':' not in param: regex = param
        else: current_namespace, regex = param.split(':')

        if current_namespace == '':
            return '\033[91mERROR: Debe especificar el namespace.\033[0m'
        
        if not regex:
            return '\033[91mERROR: La expresión regular no es válida.\033[0m'
        
        if current_namespace not in self.metadata:
            return '\033[91mNamespaceNotFoundException: El namespace especificado no existe.\033[0m'

        if regex:
            if regex[0] != '^':
                regex = f'^{regex}'
            if regex[-1] != '$':
                regex = f'{regex}$'

        result = 'TABLE\n'
        rows = 0
        for table in self.metadata[current_namespace]:
            if not re.match(regex,table): continue
            result += f'{table}\n'
            rows += 1
        result += f'\033[95m{rows} \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'
        return result

    def listNamespaces(self):
        inicio = time()
        result = ''
        result += 'NAMESPACE\n'
        rows = 0
        for namespace in self.metadata.keys():
            result += f'{namespace}\n'
            rows += 1
        result += f'\033[95m{rows} \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'
        return result

    def disableTable(self, name, embedded=False):
        inicio = time()
        table = self.verifyTable(name)

        if not isinstance(table,tuple):
            return table

        if len(table) == 2:
            return f"\033[91mTableNotFoundException: La tabla '{table[1]}' no existe en el namespace '{table[0]}'\033[0m" if not embedded else False

        self.metadata[table[0]][table[1]]["enabled"] = False
        self.writeMetadata()

        path = os.path.join(f'namespaces/{table[0]}/', table[1])
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

        for file in files:
            full_path = os.path.join(path, file)
            file_content = {}
            with open(full_path, 'r') as f:
                file_content = json.load(f)

            if file_content['metadata']['enabled']:
                file_content['metadata']['enabled'] = False
            with open(full_path, 'w') as f:
                json.dump(file_content, f, indent=4)
        return f'\033[95m0 \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds' if not embedded else True
    
    def enableTable(self, name):
        inicio = time()
        table = self.verifyTable(name)

        if not isinstance(table,tuple):
            return table

        if len(table) == 2:
            return f"\033[91mTableNotFoundException: La tabla '{table[1]}' no existe en el namespace '{table[0]}'\033[0m"

        self.metadata[table[0]][table[1]]["enabled"] = True
        self.writeMetadata()

        path = os.path.join(f'namespaces/{table[0]}/', table[1])
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

        for file in files:
            full_path = os.path.join(path, file)
            file_content = {}
            with open(full_path, 'r') as f:
                file_content = json.load(f)

            if not file_content['metadata']['enabled']:
                file_content['metadata']['enabled'] = True
            with open(full_path, 'w') as f:
                json.dump(file_content, f, indent=4)
        return f'\033[95m0 \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'
    
    def checkEnabledTable(self, name):
        result = ''
        inicio = time()
        table = self.verifyTable(name)

        if not isinstance(table,tuple):
            return table

        if len(table) == 2:
            return f"\033[91mTableNotFoundException: La tabla '{table[1]}' no existe en el namespace '{table[0]}'\033[0m"

        state = self.metadata[table[0]][table[1]]["enabled"]

        if not state:
            result += f"\033[91mDisabled\033[0m\n"
        else:
            result += f"\033[32mEnabled\033[0m\n"
        result += f'\033[95m0 \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'
        return result

    def alterTable(self, name, options):
        result = ''
        table = self.verifyTable(name)

        if not isinstance(table,tuple):
            return table

        if len(table) == 2:
            return f"\033[91mTableNotFoundException: La tabla '{table[1]}' no existe en el namespace '{table[0]}'\033[0m"
        
        if table[3]:
            return f"\033[91mTableNotDisabledException: La tabla '{table[1]}' no está deshabilitada.\033[0m"

        inicio = time()

        options = options[1:-1]
        
        option_commands = [el.strip() for el in options.split(',')]
        actions = {}
        for oc in option_commands:
            instructions = [i.strip() for i in oc.split('=>')]
            actions[instructions[0]] = instructions[1]

        cf = actions.get('NAME')
        action = actions.get('METHOD') if 'METHOD' in actions.keys() else 'add'

        if action == 'add':
            if cf not in table[2]:
                table[2].append(cf)
        if action == 'delete':
            if cf in table[2]:
                table[2].remove(cf)        
        if action == 'modify':
            newCF = actions.get('NEW') if 'NEW' in actions.keys() else cf
            if cf in table[2]:
                table[2].remove(cf)
                table[2].append(newCF)


        self.writeMetadata()
        result += 'Updating all files with the new schema...\n'

        path = os.path.join(f'namespaces/{table[0]}/', table[1])
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

        for file in files:
            full_path = os.path.join(path, file)
            file_content = {}
            with open(full_path, 'r') as f:
                file_content = json.load(f)

            if action == 'add' and cf not in file_content['metadata']['column_families']:
                file_content['metadata']['column_families'].append(cf)
            if action == 'delete' and cf in file_content['metadata']['column_families']:
                file_content['metadata']['column_families'].remove(cf)
                data = file_content['data']

                for _,v in data.items():
                    if cf in v:
                        v.pop(cf)
            if action == 'modify' and cf in file_content['metadata']['column_families']:
                newCF = actions.get('NEW') if 'NEW' in actions.keys() else cf
                file_content['metadata']['column_families'].append(newCF)
                file_content['metadata']['column_families'].remove(cf)
                data = file_content['data']

                for _,v in data.items():
                    if cf in v:
                        v[newCF] = v[cf]
                        v.pop(cf)
            with open(full_path, 'w') as f:
                json.dump(file_content, f, indent=4)


        result += f'\033[95m{len(files)} \033[96mfiles\033[0m(s) updated in \033[95m{round(time() - inicio,6)} \033[0mseconds\nDone'
        return result

    def dropTable(self,name,embedded = False):
        inicio = time()
        table = self.verifyTable(name)

        if not isinstance(table,tuple):
            return table

        if len(table) == 2:
            return f"\033[91mTableNotFoundException: La tabla '{table[1]}' no existe en el namespace '{table[0]}'\033[0m" if not embedded else False
        
        if table[3]:
            return f"\033[91mTableNotDisabledException: La tabla '{table[1]}' no está deshabilitada.\033[0m" if not embedded else False
        
        self.metadata[table[0]].pop(table[1])
        self.writeMetadata()

        table_path = os.path.join(f'namespaces/{table[0]}', table[1])
        files = len(glob.glob(os.path.join(table_path, "*")))
        shutil.rmtree(table_path)
        return f'\033[95m{files} \033[96mfile\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds' if not embedded else True

    def dropAllTables(self, param=None):
        inicio = time()
        regex = None
        result = ''
        current_namespace = 'default'
        if not param:
            regex = '.*'
        elif ':' not in param: regex = param
        else: current_namespace, regex = param.split(':')

        if current_namespace == '':
            return '\033[91mERROR: Debe especificar el namespace.\033[0m'
        
        if not regex:
            return '\033[91mERROR: La expresión regular no es válida.\033[0m'
        
        if current_namespace not in self.metadata:
            return '\033[91mNamespaceNotFoundException: El namespace especificado no existe.\033[0m'

        if regex:
            if regex[0] != '^':
                regex = f'^{regex}'
            if regex[-1] != '$':
                regex = f'{regex}$'
        
        tables = [t for t in self.metadata[current_namespace].keys() if re.match(regex, t)]
        
        counter = 0
        for t in tables:
            result += f"Disabling table {current_namespace}:{t}\n"
            counter += 1
            if not self.disableTable(f'{current_namespace}:{t}',embedded=True):
                result += f"\033[91mCouldn't disable {current_namespace}:{t}\033[0m\n"
                counter -= 1
        
        for t in tables:
            counter += 1
            result += f"Dropping table {current_namespace}:{t}\n"
            if not self.dropTable(f'{current_namespace}:{t}',embedded=True):
                result += f"\033[91mCouldn't drop {current_namespace}:{t}\033[0m\n"
                counter -= 1

        result += f'\033[95m{counter} \033[96mtable\033[0m(s) dropped in \033[95m{round(time() - inicio,6)} \033[0mseconds'
        return result

    def describeTable(self,name):
        inicio = time()
        result = ''
        table = self.verifyTable(name)

        if not isinstance(table,tuple):
            return table

        if len(table) == 2:
            return f"\033[91mTableNotFoundException: La tabla '{table[1]}' no existe en el namespace '{table[0]}'\033[0m"
        
        result += f'\033[91mTABLE \033[0m{table[1]} is \033[95m{"ENABLED" if table[3] else "DISABLED"}\033[0m\n'
        result += f'{table[1]}\n'
        result += '\033[95mCOLUMN FAMILIES DESCRIPTION\033[0m\n'

        for cf in table[2]:
            result += f"{'{'}NAME => \033[92m'{cf}'\033[0m{'}'}\n"

        result += f'\033[95m{len(table[2])} \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'
        return result

    def putRow(self,table,rowId,col,value):
        inicio = time()
        table = self.verifyTable(table)

        if not isinstance(table,tuple):
            return table

        if len(table) == 2:
            return f"\033[91mTableNotFoundException: La tabla '{table[1]}' no existe en el namespace '{table[0]}'\033[0m"
        
        if not table[3]:
            return f"\033[91mTableDisabledException: La tabla '{table[1]}' está deshabilitada.\033[0m"
        
        if ':' not in col:
            return f"\033[91mERROR: Debe especificar el column family al que pertenece la columna\033[0m"
        
        cf, column = col.split(':')

        if cf not in table[2]:
            return f"\033[91mFamilyNotFoundException: La familia '{cf}' no existe en la tabla '{table[1]}'\033[0m"
        
        table_path = os.path.join(f'namespaces/{table[0]}', table[1])
        files = len(glob.glob(os.path.join(table_path, "*")))
        files = files - 1 if files > 0 else files

        fileName = f'HFile_{files}.json'
        hfile = {}
        
        file_path = os.path.join(table_path, fileName)

        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                hfile = json.load(f)
                
        # if 'data' in hfile.keys() and len(hfile['data']) > 50:
        #     fileName = f'HFile_{files+1}.json'
        #     file_path = os.path.join(table_path, fileName)
        #     hfile['data'] = {}
        #     hfile['metadata']['creation_time'] = datetime.now().isoformat()

        if 'metadata' not in hfile.keys():
            hfile['metadata'] = {
                'table_name': table[1],
                'enabled': True,
                'column_families': table[2],
                'creation_time': datetime.now().isoformat(),
                'region': table[4]
                }
            
        timestamp = datetime.now().timestamp()
        
        if 'data' not in hfile.keys():
            hfile['data'] = {rowId: {cf: {column: {timestamp: value}}}}
        else:
            if rowId in hfile['data'].keys():
                if cf in hfile['data'][rowId]:
                    if column in hfile['data'][rowId][cf]:
                        values = list(hfile['data'][rowId][cf][column].values())
                        if len(values) and value != values[0]:
                            hfile['data'][rowId][cf][column] = {timestamp: value, **hfile['data'][rowId][cf][column]}
                    else:
                        hfile['data'][rowId][cf][column] = {timestamp: value}
                else:
                    hfile['data'][rowId][cf] = {column: {timestamp: value}}
            else:
                hfile['data'][rowId] = {cf: {column: {timestamp: value}}}
            
        if len(hfile['data'][rowId][cf][column]) == 4:
            hfile['data'][rowId][cf][column].popitem()
            
        hfile['data'] = {k: hfile['data'][k] for k in sorted(hfile['data'], key=int)}

        with open(file_path, 'w') as f:
            json.dump(hfile, f, indent=2)
            
        return f'\033[95m{1} \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'
    
    
    def getData(self, table, rowId, cols=None, timestamp=None):
        resultMessage=''
        inicio = time()
        table = self.verifyTable(table)
        result = {}
        cf = None
        column = None

        if not isinstance(table,tuple):
            return table

        if len(table) == 2:
            return f"\033[91mTableNotFoundException: La tabla '{table[1]}' no existe en el namespace '{table[0]}'\033[0m"
        
        if not table[3]:
            return f"\033[91mTableDisabledException: La tabla '{table[1]}' está deshabilitada.\033[0m"
        
        if cols:
            for col in cols:
                if ':' not in col: cf = col
                else: cf, column = col.split(':')

                if cf not in table[2]:
                    return f"\033[91mFamilyNotFoundException: La familia '{cf}' no existe en la tabla '{table[1]}'\033[0m"
                if ':' in col:
                    result[(cf,column)] = []
            
        rows = []
        
        table_path = os.path.join(f'namespaces/{table[0]}', table[1])
        files = glob.glob(os.path.join(table_path, "*"))
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    hfile = json.load(f)
                    if 'data' in hfile.keys():
                        rows.append(hfile['data'])
                        
        rowCounter = 0
        
        for r in rows:
            if rowId in r.keys():
                if not cols:
                    result = {
                        (family, column): {}
                        for _, families in r.items()
                        for family, columns in families.items()
                        for column in columns.keys()
                    }
                if cf and not column:
                    result = {
                        (family, column): {}
                        for _, families in r.items()
                        for family, columns in families.items()
                        for column in columns.keys()
                        if family == cf
                    }
                for c in result.keys():
                    if c[1] in r[rowId][c[0]].keys():
                        result[c] = r[rowId][c[0]][c[1]]
                        if timestamp:
                            result[c] = {k: v for k, v in result[c].items() if k == timestamp}
                    else:
                        result[c] = {}
                continue
    
        headers = ['\033[94mCOLUMN','\033[95mCELL\033[0m']
        
        data = []
        for r in result.items():
            for v in r[1].items():
                data.append([f'{r[0][0]}:{r[0][1]}',f'value={v[1]} timestamp={v[0]}'])
                rowCounter += 1
                
        resultMessage += tabulate(data, headers=headers, tablefmt="plain")
        resultMessage += '\n'
        resultMessage += f'\n\033[95m{rowCounter} \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'
        return resultMessage
    
    def scanData(self, table, limit, offset):
        offset = 0 if offset is None else max(offset - 1, 0)
        limit = 10 if limit is not None and limit <= 0 else limit
        resultMessage=''
        inicio = time()
        table = self.verifyTable(table)
        result = {}

        if not isinstance(table,tuple):
            return table

        if len(table) == 2:
            return f"\033[91mTableNotFoundException: La tabla '{table[1]}' no existe en el namespace '{table[0]}'\033[0m"
        
        if not table[3]:
            return f"\033[91mTableDisabledException: La tabla '{table[1]}' está deshabilitada.\033[0m"
            
        rows = []
        
        table_path = os.path.join(f'namespaces/{table[0]}', table[1])
        files = glob.glob(os.path.join(table_path, "*"))
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    hfile = json.load(f)
                    if 'data' in hfile.keys():
                        rows.append(hfile['data'])
                        
        rowCounter = 0
        headers = ['\033[95mROW','\033[94mCOLUMN\033[0m+CELL']
        data = []
        
        for r in rows:
            for rowId, families in r.items():
                for family, columns in families.items():
                    for column, info in columns.items():
                        result[(rowId,f'{family}:{column}')] = info
                        rowCounter += len(info)
    
        
        for r in result.items():
            for v in r[1].items():
                data.append([r[0][0],f'\033[94mcolumn\033[0m={r[0][1]} \033[95mtimestamp\033[0m=\033[95m{v[0]} \033[94mvalue\033[0m={v[1]}'])                
                
        if limit is None and len(data) and len(data) > 10:
            data = data[offset:10+offset]
            data.append(['.', '.'])
            data.append(['.', '.'])
            data.append(['.', '.'])
        elif len(data) and limit:
            data = data[offset:limit+offset]
            
        resultMessage += tabulate(data, headers=headers, tablefmt="plain")
        resultMessage += '\n'
        if limit is None and len(data) and len(data) > 10:
            limit = 10
            resultMessage += f'\n\033[93mWARNING:\033[0m {rowCounter - limit - offset} row(s) more'
        elif not len(data): limit = 0
        else: limit = 10
            
        resultMessage += f'\n\033[95m{min(limit, len(data))} \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'
        return resultMessage
        
        
    def deleteRow(self, name, rowId, column, timestamp):
        inicio = time()
        table = self.verifyTable(name)

        if not isinstance(table,tuple):
            return table

        if len(table) == 2:
            return f"\033[91mTableNotFoundException: La tabla '{table[1]}' no existe en el namespace '{table[0]}'\033[0m"
        
        if not table[3]:
            return f"\033[91mTableDisabledException: La tabla '{table[1]}' está deshabilitada.\033[0m"
        
        if ':' not in column:
            return f"\033[91mERROR: Debe especificar el column family al que pertenece la columna\033[0m"
        
        cf, column = column.split(':')

        if cf not in table[2]:
            return f"\033[91mFamilyNotFoundException: La familia '{cf}' no existe en la tabla '{table[1]}'\033[0m"
        
        hfiles = {}
        
        table_path = os.path.join(f'namespaces/{table[0]}', table[1])
        files = glob.glob(os.path.join(table_path, "*"))
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    hfile = json.load(f)
                    if 'data' in hfile.keys():
                        hfiles[file_path] = hfile
                        
        for file_path, hfile in hfiles.items():
            r = hfile['data']
            if rowId in r.keys():
                try:
                    del r[rowId][cf][column][timestamp]
                    with open(file_path, 'w') as f:
                        json.dump(hfile, f, indent=2)
                except:
                    return f'\033[95m{0} \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'            
            continue
        return f'\033[95m{1} \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'
    
    def deleteAll(self, name, rowId):
        inicio = time()
        table = self.verifyTable(name)

        if not isinstance(table,tuple):
            return table

        if len(table) == 2:
            return f"\033[91mTableNotFoundException: La tabla '{table[1]}' no existe en el namespace '{table[0]}'\033[0m"
        
        if not table[3]:
            return f"\033[91mTableDisabledException: La tabla '{table[1]}' está deshabilitada.\033[0m"
        
        hfiles = {}
        
        table_path = os.path.join(f'namespaces/{table[0]}', table[1])
        files = glob.glob(os.path.join(table_path, "*"))
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    hfile = json.load(f)
                    if 'data' in hfile.keys():
                        hfiles[file_path] = hfile

        rows = 0                        
        for file_path, hfile in hfiles.items():
            r = hfile['data']
            if rowId in r.keys():
                rows = 0
                for _, columns in r[rowId].items():
                    for col in columns.items():
                        rows += len(col[1])
                    # rows += len(columns)
                r.pop(rowId)
                with open(file_path, 'w') as f:
                        json.dump(hfile, f, indent=2)
            continue
        
        return f'\033[95m{rows} \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'
    
    def countRows(self, name, embedded=False):
        inicio = time()
        table = self.verifyTable(name)

        if not isinstance(table,tuple):
            return table

        if len(table) == 2:
            return f"\033[91mTableNotFoundException: La tabla '{table[1]}' no existe en el namespace '{table[0]}'\033[0m" if not embedded else None
        
        hfiles = {}
        
        table_path = os.path.join(f'namespaces/{table[0]}', table[1])
        files = glob.glob(os.path.join(table_path, "*"))
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    hfile = json.load(f)
                    if 'data' in hfile.keys():
                        hfiles[file_path] = hfile

        rows = 0                        
        for file_path, hfile in hfiles.items():
            r = hfile['data']
            for rowId in r.keys():
                for _, columns in r[rowId].items():
                    for col in columns.items():
                        rows += len(col[1])
        
        return f'\033[95m{rows} \033[96mrow\033[0m(s)\033[0m' if not embedded else rows
    
    def truncateTable(self,name):
        inicio = time()
        table = self.verifyTable(name)
        result = f"Truncating '{table[1]}' table (it may take a while):\n"

        if not isinstance(table,tuple):
            return table

        if len(table) == 2:
            return f"\033[91mTableNotFoundException: La tabla '{table[1]}' no existe en el namespace '{table[0]}'\033[0m"
        
        rows = self.countRows(f'{table[0]}:{table[1]}', embedded=True)
        if rows == None:
            return f"\033[91mCouldn't count {table[0]}:{table[1]} rows\033[0m\n"
        
        result += "   - Disabling table...\n"
        
        if not self.disableTable(f'{table[0]}:{table[1]}',embedded=True):
            return f"\033[91mCouldn't disable {table[0]}:{table[1]}\033[0m\n"
            
        result += "   - Truncating table...\n"
        if not self.dropTable(f'{table[0]}:{table[1]}',embedded=True):
            return f"\033[91mCouldn't truncate {table[0]}:{table[1]}\033[0m\n"
            
        if not self.createTable(table[1],table[2],embedded=True):
            return f"\033[91mCouldn't truncate {table[0]}:{table[1]}\033[0m\n"
            
        result += f'     \033[95m{rows} \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'
        
        return result
    
    def getHelp(self,command=None):
        result = ''
        helps = {
            'create_namespace <namespace>': "DDL => Crea un nuevo namespace en el directorio.",
            'list_namespaces': "DDL => Lista todos los namespaces disponibles.",
            'create <namespace>?:<table_name> [column_families]': "DDL => Crea una nueva tabla con los column families descritos en el namespace indicado. Si no se especifica ningún namespace, se utiliza el 'default'.",
            'list [<namespace>?:regex]?': "DDL => Lista todas las tablas que coincidan con los parámetros dados. Si se especifica una regex, listará todas las tablas que coincidan. Si no se especifica el nombre del namespace, se buscará en el namespace 'default'.",
            'disable <namespace>?:<table_name>': "DDL => Deshabilita la tabla indicada. Si no se especifica el namespace, se tomará el namespace 'default'.",
            'enable <namespace>?:<table_name>': "DDL => Habilita la tabla indicada. Si no se especifica el namespace, se tomará el namespace 'default'.",
            'is_enabled <namespace>?:<table_name>': "DDL => Verifica el estado de la tabla descrita. Si no se especifica el namespace, se tomará el namespace 'default'.",
            "alter <namespace>?:<table_name> {NAME => <column_family>, [METHOD => 'add' | 'delete']?}": "DDL => Modifica la tabla descrita. El método 'add' añade el column family a la tabla, mientras que el método 'delete' la elimina de la tabla, así como todos los registros asignados a ella. Si no se especifica el namespace, se tomará el namespace 'default'.",
            "drop <namespace>?:<table_name>": "DDL => Elimina la tabla descrita y todo su contenido. Si no se especifica el namespace, se tomará el namespace 'default'.",
            "drop_all [<namespace>?:regex]?": "DDL => Elimina todas las tablas que coincidan con los parámetros dados. Si se especifica una regex, eliminará las tablas que coincidan. Si no se especifica el namespace, se tomará el namespace 'default'.",
            "describe <namespace>?:<table_name>": "DDL => Proporciona una breve descripción de la tabla indicada. Si no se especifica el namespace, se tomará el namespace 'default'.",
            "put <namespace>?:<table_name> <row_Id> <column_family>:<column> <value>": "DML => Crea un nuevo registro dentro de la tabla y columna indicadas, con el row_Id dado y el nuevo valor. Si ya hay un registro con esta combinación de <namespace>:<table_name> <row_Id> y <column_family>:<column>, se agregará un segundo valor como el más actualizado, manteniendo una copia de seguridad del antiguo. Si no se especifica el namespace, se tomará el namespace 'default'.",
            "get <namespace>?:<table_name> <row_Id> [<column_family>:<column>]?": "DML => Devuelve la fila que coincida con el row_id dado. Se pueden especificar las columnas que se deben devolver, con su column family respectivo. Si no se especifica el namespace, se tomará el namespace 'default'.",
            "scan <namespace>?:<table_name>": "DML => Devuelve todas las filas de la tabla indicada. Si no se especifica el namespace, se tomará el namespace 'default'.",
            "delete <namespace>?:<table_name> <row_Id> <column_family>:<column> <timestamp>": "DML => Elimina la fila que coincida con todos los parámetros. Si no se especifica el namespace, se tomará el namespace 'default'.",
            "deleteall <namespace>?:<table_name> <row_Id>": "DML => Elimina todas las filas con el row_Id indicado. Si no se especifica el namespace, se tomará el namespace 'default'.",
            "count <namespace>?:<table_name>": "DML => Cuenta la cantidad de filas en la tabla indicada. Si no se especifica el namespace, se tomará el namespace 'default'.",
            "truncate <namespace>?:<table_name>": "DML => Elimina todo el contenido de la tabla, manteniendo la estructura básica. Si no se especifica el namespace, se tomará el namespace 'default'."
        }
        
        if command:
            for c in helps.items():
                if command == c[0].split(' ')[0]: return f'{c[0]}\n\n{c[1]}'
            result += f"\033[91mEl comando '{command}' no es válido\033[0m\n\n"
        
        result += f'Para obtener más información acerca de un comando específico, escriba HELP seguido del nombre de comando\n'
        
        headers = ['\033[32mCOMANDO\033[0m','\033[32mDESCRIPCIÓN\033[0m']
        
        maxWidthDesc = 90
        maxWidthComm = 70
        
        data = []
        for c in helps.items():
            data.append([f'\033[96m{c[0].upper()}\033[0m','\033[0m'+c[1].split('.')[0]+'.'])
            data.append([' ',' '])
                
        for i in range(len(data)):
            command, description = data[i]
            if len(description) > maxWidthDesc:
                wrapped_description = '\n       '.join(textwrap.wrap(description, maxWidthDesc))
                data[i][1] = wrapped_description
            if len(command) > maxWidthComm:
                wrapped_command = '\n     \033[96m'.join(textwrap.wrap(command, maxWidthComm))
                data[i][0] = wrapped_command
            
        result += '\n'
        result += tabulate(data, headers=headers, tablefmt="plain")
        return result