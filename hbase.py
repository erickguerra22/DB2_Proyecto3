import os
import json
from time import time
import glob
import shutil
import re
from datetime import datetime
from tabulate import tabulate

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
            return '\033[91mError: Debe especificar el namespace.\033[0m'
        
        if name == '':
            return '\033[91mError: Debe especificar el nombre de la tabla.\033[0m'

        if current_namespace not in self.metadata:
            return '\033[91mNamespaceNotFoundException: El namespace especificado no existe.\033[0m'
        
        tables = [(namespace,t,atributes['families'],atributes['enabled']) for namespace,tables in self.metadata.items() for t,atributes in tables.items() if namespace == current_namespace and t == name]
        return tables[0] if len(tables) > 0 else (current_namespace,name)

    def readMetadata(self):
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)

    def writeMetadata(self):
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

    def createTable(self, name, columnFamilies):
        inicio = time()
        result = ''
        
        if ':' in name:
            current_namespace, name = name.split(':')
        else: current_namespace = 'default'

        if current_namespace == '':
            return '\033[91mError: Debe especificar el namespace.\033[0m'
        
        if name == '':
            return '\033[91mError: Debe especificar el nombre de la tabla.\033[0m'

        if current_namespace not in self.metadata:
            return '\033[91mNamespaceNotFoundException: El namespace especificado no existe.\033[0m'
        
        if not len(columnFamilies):
            return '\033[91mError: Debe especificar al menos una column family.\033[0m'
        
        tables = self.metadata[current_namespace]

        if name in tables:
            return f"\033[91mTableExistsException: La tabla '{name}' ya existe dentro del namespace {current_namespace}\033[0m"
        
        tables[name] = {'families': columnFamilies, 'enabled':True}
        self.writeMetadata()

        table_path = os.path.join(f'namespaces/{current_namespace}', name)
        os.makedirs(table_path, exist_ok=True)
        
        result += f'\033[95m0 \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds\n'
        result += f'=> \033[91mHbase::Table\033[0m - {name}'
        return result

    def listTables(self, param=None):
        inicio = time()
        regex = None
        current_namespace = 'default'
        if not param:
            regex = '.*'
        elif ':' not in param: regex = param
        else: current_namespace, regex = param.split(':')

        if current_namespace == '':
            return '\033[91mError: Debe especificar el namespace.\033[0m'
        
        if not regex:
            return '\033[91mError: La expresión regular no es válida.\033[0m'
        
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
            return '\033[91mError: Debe especificar el namespace.\033[0m'
        
        if not regex:
            return '\033[91mError: La expresión regular no es válida.\033[0m'
        
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
            if not self.disableTable(t,embedded=True):
                result += f"Couldn't disable {current_namespace}:{t}\n"
                counter -= 1
        
        for t in tables:
            counter += 1
            result += f"Dropping table {current_namespace}:{t}\n"
            if not self.dropTable(t,embedded=True):
                result += f"Couldn't drop {current_namespace}:{t}\n"
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
            return f"\033[91mError: Debe especificar el column family al que pertenece la columna\033[0m"
        
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
                
        if 'data' in hfile.keys() and len(hfile['data']) > 50:
            fileName = f'HFile_{files+1}.json'
            file_path = os.path.join(table_path, fileName)
            hfile['data'] = {}
            hfile['metadata']['creation_time'] = datetime.now().isoformat()

        if 'metadata' not in hfile.keys():
            hfile['metadata'] = {
                'table_name': table[1],
                'enabled': True,
                'column_families': table[2],
                'creation_time': datetime.now().isoformat()
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
            
        if len(hfile['data'][rowId][cf][column]) == 3:
            hfile['data'][rowId][cf][column].popitem()

        with open(file_path, 'w') as f:
            json.dump(hfile, f, indent=2)
            
        return f'\033[95m{1} \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'
    
    
    def getData(self, table, rowId, cols=None, filters=None):
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
        
        if cols:
            for col in cols:
                if ':' not in col:
                    return f"\033[91mError: Debe especificar el column family al que pertenece cada columna\033[0m"
                
                cf, column = col.split(':')

                if cf not in table[2]:
                    return f"\033[91mFamilyNotFoundException: La familia '{cf}' no existe en la tabla '{table[1]}'\033[0m"
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
                for c in result.keys():
                    result[c] = r[rowId][c[0]][c[1]]
            continue
    
        headers = ['\033[94mCOLUMN','\033[95mCELL\033[0m']
        
        data = []
        for r in result.items():
            for v in r[1].items():
                data.append([f'{r[0][0]}:{r[0][1]}',f'value={v[1]} timestamp={v[0]}'])
                rowCounter += 1
                
        resultMessage += tabulate(data, headers=headers, tablefmt="plain")
        resultMessage += '\n'
        resultMessage += f'\033[95m{rowCounter} \033[96mrow\033[0m(s) in \033[95m{round(time() - inicio,6)} \033[0mseconds'
        return resultMessage
        
        
        
hbase = HBase()
# hbase.getData('tabla2','123',['cf_2:name'])
print(hbase.getData('tabla2','123'))
        




