#!/usr/bin/env python3
"""
Diagnóstico HONESTO del workflow
"""

import json
from collections import defaultdict

with open('Frepi_MVP2_Agent_Architecture.json', 'r') as f:
    w = json.load(f)

print("="*80)
print("DIAGNÓSTICO REAL DEL WORKFLOW FREPI MVP2")
print("="*80)

all_nodes = {n['name']: n for n in w['nodes']}

print(f"\n📊 TOTAL NODOS: {len(all_nodes)}")

# Analizar CADA nodo individualmente
print("\n" + "="*80)
print("ANÁLISIS NODO POR NODO")
print("="*80)

# Categorizar nodos
infrastructure = []
agents = []
sub_agents = []
tools = []
llms = []
memory = []
other = []

for name, node in all_nodes.items():
    node_type = node.get('type', 'unknown')

    if 'trigger' in node_type.lower() or 'webhook' in node_type.lower():
        infrastructure.append((name, node_type, 'INFRASTRUCTURE'))
    elif 'code' in node_type.lower() and 'Agent' not in name:
        infrastructure.append((name, node_type, 'INFRASTRUCTURE'))
    elif 'supabase' in node_type.lower() and 'Agent' not in name:
        infrastructure.append((name, node_type, 'INFRASTRUCTURE'))
    elif 'if' in node_type.lower() or 'switch' in node_type.lower():
        infrastructure.append((name, node_type, 'INFRASTRUCTURE'))
    elif node_type == '@n8n/n8n-nodes-langchain.agent':
        agents.append((name, node_type, 'ORCHESTRATOR'))
    elif node_type == '@n8n/n8n-nodes-langchain.agentTool':
        sub_agents.append((name, node_type, 'SUB-AGENT'))
    elif 'toolCode' in node_type:
        tools.append((name, node_type, 'TOOL'))
    elif 'lmChat' in node_type:
        llms.append((name, node_type, 'LLM'))
    elif 'memory' in node_type.lower():
        memory.append((name, node_type, 'MEMORY'))
    else:
        other.append((name, node_type, 'OTHER'))

print(f"\n🏗️  INFRASTRUCTURE NODES: {len(infrastructure)}")
for name, typ, cat in infrastructure:
    # Check if has main connection
    has_out = name in w['connections'] and 'main' in w['connections'][name]
    has_in = any(name in [c['node'] for cl in cd.get('main', []) for c in cl]
                 for cd in w['connections'].values())
    status = "✅" if (has_out or has_in) else "❌ DESCONECTADO"
    print(f"  {status} {name}")

print(f"\n🤖 ORCHESTRATOR AGENTS: {len(agents)}")
for name, typ, cat in agents:
    has_main_out = name in w['connections'] and 'main' in w['connections'][name]
    has_main_in = any(name in [c['node'] for cl in cd.get('main', []) for c in cl]
                      for cd in w['connections'].values())

    # Count tools
    tool_count = 0
    if name in w['connections']:
        for conn_data in w['connections'].values():
            if 'ai_tool' in conn_data:
                for cl in conn_data['ai_tool']:
                    for c in cl:
                        if c['node'] == name:
                            tool_count += 1

    has_llm = any(name in [c['node'] for cl in cd.get('ai_languageModel', []) for c in cl]
                  for cd in w['connections'].values())
    has_memory = any(name in [c['node'] for cl in cd.get('ai_memory', []) for c in cl]
                     for cd in w['connections'].values())

    status_main = "✅ IN/OUT" if (has_main_out and has_main_in) else "⚠️ " + ("OUT" if has_main_out else "") + ("IN" if has_main_in else "NADA")
    print(f"  {status_main} {name}")
    print(f"     LLM: {'✅' if has_llm else '❌'}, Memory: {'✅' if has_memory else '❌'}, Tools: {tool_count}")

print(f"\n🔧 SUB-AGENTS: {len(sub_agents)}")
for name, typ, cat in sub_agents:
    # Sub-agents connect as tools to parent agents
    has_parent = name in w['connections'] and 'ai_tool' in w['connections'][name]

    # Count their own tools
    tool_count = 0
    for conn_data in w['connections'].values():
        if 'ai_tool' in conn_data:
            for cl in conn_data['ai_tool']:
                for c in cl:
                    if c['node'] == name:
                        tool_count += 1

    has_llm = any(name in [c['node'] for cl in cd.get('ai_languageModel', []) for c in cl]
                  for cd in w['connections'].values())
    has_memory = any(name in [c['node'] for cl in cd.get('ai_memory', []) for c in cl]
                     for cd in w['connections'].values())

    status = "✅" if has_parent else "❌ SIN PARENT"
    print(f"  {status} {name}")
    print(f"     LLM: {'✅' if has_llm else '❌'}, Memory: {'✅' if has_memory else '❌'}, Tools conectados a este agente: {tool_count}")

print(f"\n🛠️  TOOLS: {len(tools)}")
connected_tools = 0
for name, typ, cat in tools:
    has_parent = name in w['connections'] and 'ai_tool' in w['connections'][name]
    if has_parent:
        parent = w['connections'][name]['ai_tool'][0][0]['node']
        print(f"  ✅ {name} → {parent}")
        connected_tools += 1
    else:
        print(f"  ❌ {name} - DESCONECTADO")

print(f"\nTools conectados: {connected_tools}/{len(tools)}")

print(f"\n🧠 LLMs: {len(llms)}")
connected_llms = 0
for name, typ, cat in llms:
    has_agent = name in w['connections'] and 'ai_languageModel' in w['connections'][name]
    if has_agent:
        agent = w['connections'][name]['ai_languageModel'][0][0]['node']
        print(f"  ✅ {name} → {agent}")
        connected_llms += 1
    else:
        print(f"  ❌ {name} - DESCONECTADO")

print(f"\nLLMs conectados: {connected_llms}/{len(llms)}")

print(f"\n💾 MEMORY: {len(memory)}")
connected_memory = 0
for name, typ, cat in memory:
    has_agent = name in w['connections'] and 'ai_memory' in w['connections'][name]
    if has_agent:
        agent = w['connections'][name]['ai_memory'][0][0]['node']
        print(f"  ✅ {name} → {agent}")
        connected_memory += 1
    else:
        print(f"  ❌ {name} - DESCONECTADO")

print(f"\nMemory conectados: {connected_memory}/{len(memory)}")

# RESUMEN FINAL
print("\n" + "="*80)
print("RESUMEN FINAL")
print("="*80)

total_expected_connected = len(infrastructure) + len(agents) + len(sub_agents) + len(tools) + len(llms) + len(memory)
total_actually_connected = connected_tools + connected_llms + connected_memory

# Contar infrastructure conectados
infra_connected = 0
for name, typ, cat in infrastructure:
    has_out = name in w['connections'] and 'main' in w['connections'][name]
    has_in = any(name in [c['node'] for cl in cd.get('main', []) for c in cl]
                 for cd in w['connections'].values())
    if has_out or has_in:
        infra_connected += 1

# Contar agents conectados
agents_connected = 0
for name, typ, cat in agents:
    has_main_out = name in w['connections'] and 'main' in w['connections'][name]
    has_main_in = any(name in [c['node'] for cl in cd.get('main', []) for c in cl]
                      for cd in w['connections'].values())
    if has_main_out and has_main_in:
        agents_connected += 1

# Contar sub-agents conectados
subagents_connected = 0
for name, typ, cat in sub_agents:
    has_parent = name in w['connections'] and 'ai_tool' in w['connections'][name]
    if has_parent:
        subagents_connected += 1

total_connected = infra_connected + agents_connected + subagents_connected + connected_tools + connected_llms + connected_memory
total_nodes = len(all_nodes)

print(f"\nNodos totales: {total_nodes}")
print(f"Infrastructure conectados: {infra_connected}/{len(infrastructure)}")
print(f"Orchestrator agents conectados: {agents_connected}/{len(agents)}")
print(f"Sub-agents conectados: {subagents_connected}/{len(sub_agents)}")
print(f"Tools conectados: {connected_tools}/{len(tools)}")
print(f"LLMs conectados: {connected_llms}/{len(llms)}")
print(f"Memory conectados: {connected_memory}/{len(memory)}")

print(f"\n{'='*80}")
print(f"TOTAL CONECTADOS: {total_connected}/{total_nodes}")
print(f"PORCENTAJE CONECTADO: {total_connected/total_nodes*100:.1f}%")
print(f"PORCENTAJE DESCONECTADO: {(total_nodes-total_connected)/total_nodes*100:.1f}%")
print(f"{'='*80}")
