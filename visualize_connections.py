#!/usr/bin/env python3
"""
Visualización completa de todas las conexiones del workflow
Para ver exactamente qué está conectado y qué no
"""

import json

with open('Frepi_MVP2_Agent_Architecture.json', 'r') as f:
    w = json.load(f)

print("="*100)
print("VISUALIZACIÓN COMPLETA DE CONEXIONES")
print("="*100)

# Construir mapa de todas las conexiones
receives_any = {}  # node -> [(source, type)]
sends_any = {}     # node -> [(target, type)]

for source, conn_data in w['connections'].items():
    for conn_type, conn_lists in conn_data.items():
        for conn_list in conn_lists:
            for conn in conn_list:
                target = conn['node']

                if source not in sends_any:
                    sends_any[source] = []
                sends_any[source].append((target, conn_type))

                if target not in receives_any:
                    receives_any[target] = []
                receives_any[target].append((source, conn_type))

# Mostrar cada nodo con sus conexiones
all_nodes = sorted([(n['name'], n.get('type', 'unknown')) for n in w['nodes']])

print(f"\nTotal nodos: {len(all_nodes)}\n")

for name, node_type in all_nodes:
    print(f"\n{'='*100}")
    print(f"📌 {name}")
    print(f"   Type: {node_type}")

    # Conexiones de entrada
    if name in receives_any:
        print(f"   ⬇️  RECIBE DE:")
        for source, conn_type in receives_any[name]:
            print(f"      ← {source} ({conn_type})")
    else:
        # Verificar si es entry point
        if any(x in node_type for x in ['trigger', 'webhook']):
            print(f"   ⬇️  ENTRY POINT")
        else:
            print(f"   ⚠️  NO RECIBE CONEXIONES")

    # Conexiones de salida
    if name in sends_any:
        print(f"   ⬆️  ENVÍA A:")
        for target, conn_type in sends_any[name]:
            print(f"      → {target} ({conn_type})")
    else:
        # Verificar si es terminal
        if 'whatsApp' in node_type and name in ['Enviar Respuesta', 'WhatsApp Send']:
            print(f"   ⬆️  TERMINAL NODE")
        # Tools, memory, LLM no necesitan enviar
        elif any(x in node_type for x in ['toolCode', 'memory', 'lmChat', 'embedding', 'vectorStore']):
            print(f"   ℹ️  (No necesita enviar - es tool/memory/llm)")
        else:
            print(f"   ⚠️  NO ENVÍA CONEXIONES")

print("\n" + "="*100)
print("RESUMEN")
print("="*100)

# Nodos totalmente sin conexiones
no_connections = []
for name, node_type in all_nodes:
    if name not in receives_any and name not in sends_any:
        # Skip si es tool/memory/llm (estos conectan HACIA agentes, no desde)
        if not any(x in node_type for x in ['toolCode', 'memory', 'lmChat', 'embedding', 'vectorStore']):
            # Skip si es entry point
            if not any(x in node_type for x in ['trigger', 'webhook']):
                no_connections.append((name, node_type))

print(f"\n❌ Nodos SIN NINGUNA CONEXIÓN: {len(no_connections)}")
for name, node_type in no_connections:
    print(f"   - {name} ({node_type})")

# Nodos con conexiones
with_connections = len(all_nodes) - len(no_connections)
print(f"\n✅ Nodos CON CONEXIONES: {with_connections}/{len(all_nodes)}")
print(f"📊 Porcentaje conectado: {with_connections/len(all_nodes)*100:.1f}%")
