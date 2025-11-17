#!/usr/bin/env python3
"""
Análisis del JSON que el usuario me mostró
"""

import json

# El JSON que el usuario me mostró
workflow_json = """
{el JSON completo está arriba}
"""

# Por ahora, analizar el archivo actual
with open('Frepi_MVP2_Agent_Architecture.json', 'r') as f:
    w = json.load(f)

print("="*80)
print("ANÁLISIS DEL JSON ACTUAL")
print("="*80)

all_nodes = {n['name']: n for n in w['nodes']}
print(f"\n📊 Total nodos en 'nodes': {len(all_nodes)}")
print(f"📊 Total keys en 'connections': {len(w['connections'])}")

# Ver qué nodos NO están en connections como SOURCE
nodes_not_in_connections = set(all_nodes.keys()) - set(w['connections'].keys())
print(f"\n❌ Nodos que NO están en 'connections' como SOURCE: {len(nodes_not_in_connections)}")
for node in sorted(nodes_not_in_connections):
    node_type = all_nodes[node].get('type', 'unknown')
    # Verificar si reciben conexión
    receives = False
    for conn_data in w['connections'].values():
        for conn_type_list in conn_data.values():
            for conn_list in conn_type_list:
                for conn in conn_list:
                    if conn['node'] == node:
                        receives = True
                        break
    status = "Recibe conexión" if receives else "⚠️ HUÉRFANO TOTAL"
    print(f"  - {node} ({node_type}) - {status}")

# Ahora verificar TODOS los nodos que deberían tener conexión main SALIENTE
print("\n" + "="*80)
print("NODOS QUE DEBERÍAN TENER 'main' SALIENTE")
print("="*80)

# Tipos de nodo que DEBEN tener main saliente
should_have_main_out = [
    'n8n-nodes-base.whatsAppTrigger',
    'n8n-nodes-base.code',
    'n8n-nodes-base.supabase',
    'n8n-nodes-base.if',
    'n8n-nodes-base.switch',
    '@n8n/n8n-nodes-langchain.agent',  # Orchestrator agents
    '@n8n/n8n-nodes-langchain.agentTool',  # Sub-agents cuando están en el flujo main
]

problems = []

for name, node in all_nodes.items():
    node_type = node.get('type', '')

    # Verificar si es un tipo que necesita main
    needs_main = False
    for t in should_have_main_out:
        if t in node_type:
            needs_main = True
            break

    # Skip terminal nodes
    if name in ['Enviar Respuesta', 'WhatsApp Send']:
        needs_main = False

    # Tools, Memory, LLM NO necesitan main
    if any(x in node_type for x in ['toolCode', 'memory', 'lmChat', 'embedding', 'vectorStore']):
        needs_main = False

    if needs_main:
        has_main = name in w['connections'] and 'main' in w['connections'][name]
        if not has_main:
            problems.append((name, node_type, 'NO tiene conexión main'))
            print(f"  ❌ {name} ({node_type})")

print(f"\n📊 Problemas encontrados: {len(problems)}")

# Verificar nodos que NO reciben NINGUNA conexión
print("\n" + "="*80)
print("NODOS TOTALMENTE HUÉRFANOS (no reciben ni envían)")
print("="*80)

# Construir set de todos los nodos que reciben conexión
receives_connection = set()
for source, conn_data in w['connections'].items():
    for conn_type_list in conn_data.values():
        for conn_list in conn_type_list:
            for conn in conn_list:
                receives_connection.add(conn['node'])

# Construir set de todos los nodos que envían conexión
sends_connection = set(w['connections'].keys())

# Nodos conectados de alguna forma
connected = receives_connection | sends_connection

# Huérfanos totales
orphans = set(all_nodes.keys()) - connected

# Skip entry points
orphans = orphans - {'WhatsApp Trigger', 'Webhook WhatsApp'}

print(f"Huérfanos totales: {len(orphans)}")
for node in sorted(orphans):
    node_type = all_nodes[node].get('type', 'unknown')
    print(f"  ❌ {node} ({node_type})")

# RESUMEN FINAL
print("\n" + "="*80)
print("RESUMEN REAL")
print("="*80)
print(f"Total nodos: {len(all_nodes)}")
print(f"Nodos conectados: {len(connected)}")
print(f"Nodos huérfanos: {len(orphans)}")
print(f"% Conectado: {len(connected)/len(all_nodes)*100:.1f}%")
print(f"% Huérfano: {len(orphans)/len(all_nodes)*100:.1f}%")
