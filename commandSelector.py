def commandSelector(hbase,command):
    if '{' in command:
        parts = command.split('{')
        parts = parts[0].strip().split(' ') + [f'{"{"}{parts[1]}']
    else:
        parts = command.split(' ')
    for i in range(len(parts)):
        if parts[i][0] in ["'",'"']:
            parts[i] = parts[i][1:]
        if parts[i][-1] == ',':
            parts[i] = parts[i][:-1]
        if parts[i][-1] in ["'",'"']:
            parts[i] = parts[i][:-1]
    
    command = parts[0].lower()

    try:
        if command == 'create_namespace':
            return hbase.createNamespace(parts[1])
        elif command == 'list_namespaces':
            return hbase.listNamespaces()
        elif command == 'create':
            return hbase.createTable(parts[1],parts[2:])
        elif command == 'list':
            param = parts[1] if len(parts) > 1 else None
            return hbase.listTables(param)
        elif command == 'disable':
            return hbase.disableTable(parts[1])
        elif command == 'enable':
            return hbase.enableTable(parts[1])
        elif command == 'is_enabled':
            return hbase.checkEnabledTable(parts[1])
        elif command == 'alter':
            return hbase.alterTable(parts[1], ' '.join(parts[2:]))
        elif command == 'drop':
            return hbase.dropTable(parts[1])
        elif command == 'drop_all':
            param = parts[1] if len(parts) > 1 else None
            return hbase.dropAllTables(param)
        elif command == 'describe':
            return hbase.describeTable(parts[1])
        elif command == 'put':
            return hbase.putRow(parts[1], parts[2], parts[3], parts[4],)
        else:
            return f"\033[91mError: El comando {parts[0]} no es válido\033[0m"
        
    except Exception:
        return f"\033[91mError: Parámetros insuficientes\033[0m"