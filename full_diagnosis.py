#!/usr/bin/env python3
"""
Análisis y corrección COMPLETA del workflow
"""

import json
import sys

print("="*80)
print("ANÁLISIS COMPLETO Y CORRECCIÓN")
print("="*80)

with open('Frepi_MVP2_Agent_Architecture.json', 'r') as f:
    w = json.load(f)

print(f"\n📊 Total nodos: {len(w['nodes'])}")

# PROBLEMA 1: Types incorrectos
print("\n" + "="*80)
print("PROBLEMA 1: TYPES INCORRECTOS")
print("="*80)

incorrect_types = []

for node in w['nodes']:
    name = node['name']
    node_type = node.get('type', 'unknown')

    # Buscar types incorrectos
    if '@n8n/n8n-nodes-langchain.supabase' in node_type:
        incorrect_types.append((name, node_type, 'DEBERÍA SER: n8n-nodes-base.supabase'))
        print(f"❌ {name}: {node_type}")
        print(f"   → DEBE SER: n8n-nodes-base.supabase")

if len(incorrect_types) > 0:
    print(f"\n⚠️ {len(incorrect_types)} nodos con type incorrecto")
else:
    print("✅ Todos los types son correctos")

# PROBLEMA 2: Nodos sin conexión de ENTRADA en el flujo main
print("\n" + "="*80)
print("PROBLEMA 2: NODOS SIN CONEXIÓN DE ENTRADA (main flow)")
print("="*80)

# Construir set de nodos que RECIBEN conexión main
receives_main = set()
for source, conn_data in w['connections'].items():
    if 'main' in conn_data:
        for conn_list in conn_data['main']:
            for conn in conn_list:
                receives_main.add(conn['node'])

# Nodos que deberían recibir conexión main
should_receive_main = []
entry_points = {'WhatsApp Trigger', 'Webhook WhatsApp'}

for node in w['nodes']:
    name = node['name']
    node_type = node.get('type', '')

    # Skip entry points, tools, memory, LLM
    if name in entry_points:
        continue
    if any(x in node_type for x in ['toolCode', 'memory', 'lmChat', 'embedding', 'vectorStore']):
        continue

    # Estos tipos DEBEN estar en el flujo main
    if any(x in node_type for x in ['code', 'supabase', 'if', 'switch', 'whatsApp', 'agent']):
        if 'agentTool' not in node_type:  # agentTool puede ser solo herramienta
            should_receive_main.append((name, node_type))

no_input = []
for name, node_type in should_receive_main:
    if name not in receives_main:
        no_input.append((name, node_type))
        print(f"❌ {name} ({node_type}) - NO recibe conexión main")

if len(no_input) > 0:
    print(f"\n⚠️ {len(no_input)} nodos sin entrada main")
else:
    print("✅ Todos los nodos necesarios reciben entrada main")

# PROBLEMA 3: Nodos sin conexión de SALIDA en el flujo main
print("\n" + "="*80)
print("PROBLEMA 3: NODOS SIN CONEXIÓN DE SALIDA (main flow)")
print("="*80)

# Nodos que envían main
sends_main = set()
for source, conn_data in w['connections'].items():
    if 'main' in conn_data:
        sends_main.add(source)

# Nodos que deberían enviar main
terminal_nodes = {'Enviar Respuesta', 'WhatsApp Send'}
no_output = []

for node in w['nodes']:
    name = node['name']
    node_type = node.get('type', '')

    # Skip terminal nodes, tools, memory, LLM
    if name in terminal_nodes:
        continue
    if any(x in node_type for x in ['toolCode', 'memory', 'lmChat', 'embedding', 'vectorStore']):
        continue

    # Estos tipos DEBEN tener salida main
    needs_output = False
    if any(x in node_type for x in ['trigger', 'code', 'supabase', 'if', 'switch']):
        needs_output = True
    if node_type == '@n8n/n8n-nodes-langchain.agent':  # Orchestrators
        needs_output = True
    if node_type == '@n8n/n8n-nodes-langchain.agentTool':
        # Sub-agents que están en el main flow (no solo como tools)
        # Verificar si reciben main input
        if name in receives_main:
            needs_output = True

    if needs_output and name not in sends_main:
        no_output.append((name, node_type))
        print(f"❌ {name} ({node_type}) - NO tiene salida main")

if len(no_output) > 0:
    print(f"\n⚠️ {len(no_output)} nodos sin salida main")
else:
    print("✅ Todos los nodos necesarios tienen salida main")

# PROBLEMA 4: AgentTools sin LLM o Memory
print("\n" + "="*80)
print("PROBLEMA 4: AGENTS SIN LLM O MEMORY")
print("="*80)

agent_nodes = [n for n in w['nodes'] if 'agent' in n.get('type', '').lower()]

for agent in agent_nodes:
    name = agent['name']

    # Buscar LLM
    has_llm = False
    for source, conn_data in w['connections'].items():
        if 'ai_languageModel' in conn_data:
            for conn_list in conn_data['ai_languageModel']:
                for conn in conn_list:
                    if conn['node'] == name:
                        has_llm = True
                        break

    # Buscar Memory
    has_memory = False
    for source, conn_data in w['connections'].items():
        if 'ai_memory' in conn_data:
            for conn_list in conn_data['ai_memory']:
                for conn in conn_list:
                    if conn['node'] == name:
                        has_memory = True
                        break

    status = ""
    if not has_llm:
        status += "❌ SIN LLM "
    if not has_memory:
        status += "❌ SIN MEMORY"

    if status:
        print(f"{status} - {name}")

# RESUMEN
print("\n" + "="*80)
print("RESUMEN DE PROBLEMAS")
print("="*80)
print(f"1. Types incorrectos: {len(incorrect_types)}")
print(f"2. Sin entrada main: {len(no_input)}")
print(f"3. Sin salida main: {len(no_output)}")

total_problems = len(incorrect_types) + len(no_input) + len(no_output)
print(f"\n⚠️ TOTAL PROBLEMAS: {total_problems}")

if total_problems > 0:
    print("\n🔧 Procediendo a corregir...")
    sys.exit(1)
else:
    print("\n✅ NO HAY PROBLEMAS")
    sys.exit(0)
