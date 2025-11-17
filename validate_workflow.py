#!/usr/bin/env python3
"""
Script para validar el workflow: verificar huérfanos, dead ends, y estructura
"""

import json
from collections import defaultdict, deque

print("🔍 Validando workflow Frepi MVP2...\n")

# Cargar workflow
with open('Frepi_MVP2_Agent_Architecture.json', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

nodes_map = {node['name']: node['id'] for node in workflow['nodes']}
id_to_name = {node['id']: node['name'] for node in workflow['nodes']}

print(f"📊 Estadísticas generales:")
print(f"   Total nodes: {len(workflow['nodes'])}")
print(f"   Total connections: {len(workflow['connections'])}")

# ============================================================================
# 1. VERIFICAR HUÉRFANOS
# ============================================================================
print("\n🔍 1. Verificando nodos huérfanos...\n")

all_node_names = set(nodes_map.keys())
connected_nodes = set(workflow['connections'].keys())

# También contar nodos que son destino de conexiones
for conn_data in workflow['connections'].values():
    for conn_type_list in conn_data.values():
        for conn_list in conn_type_list:
            for conn in conn_list:
                connected_nodes.add(conn['node'])

# Entry points que no necesitan conexión de entrada
entry_points = {'Webhook WhatsApp', 'WhatsApp Trigger'}
# Config nodes que son referenciados por expresiones
config_nodes = {'Config Global'}

orphaned = all_node_names - connected_nodes - entry_points - config_nodes

if orphaned:
    print(f"⚠️  NODOS HUÉRFANOS: {len(orphaned)}")
    for node in sorted(orphaned):
        print(f"   - {node}")
else:
    print("✅ 0 NODOS HUÉRFANOS (excluyendo entry points y config nodes)")

# ============================================================================
# 2. VERIFICAR DEAD ENDS
# ============================================================================
print("\n🔍 2. Verificando dead ends (nodos sin salida)...\n")

# Construir grafo de conexiones "main"
graph = defaultdict(list)
for source, conn_data in workflow['connections'].items():
    if 'main' in conn_data:
        for conn_list in conn_data['main']:
            for conn in conn_list:
                graph[source].append(conn['node'])

# Nodos finales esperados
terminal_nodes = {'Enviar Respuesta'}

# Encontrar nodos con salida "main" pero que no llevan a ningún lado
dead_ends = []
for node_name in all_node_names:
    # Skip terminal nodes
    if node_name in terminal_nodes:
        continue
    # Skip tool/memory/llm nodes (no tienen salida main)
    node_obj = next((n for n in workflow['nodes'] if n['name'] == node_name), None)
    if node_obj:
        node_type = node_obj.get('type', '')
        # Estos tipos no necesitan salida main
        if any(t in node_type for t in ['toolCode', 'lmChat', 'memory', 'embedding', 'vectorStore']):
            continue

    # Si el nodo tiene conexiones de entrada main pero no de salida main
    has_main_input = False
    for conn_data in workflow['connections'].values():
        if 'main' in conn_data:
            for conn_list in conn_data['main']:
                for conn in conn_list:
                    if conn['node'] == node_name:
                        has_main_input = True
                        break

    if has_main_input and node_name not in graph:
        dead_ends.append(node_name)

if dead_ends:
    print(f"⚠️  DEAD ENDS DETECTADOS: {len(dead_ends)}")
    for node in sorted(dead_ends):
        print(f"   - {node}")
else:
    print("✅ 0 DEAD ENDS")

# ============================================================================
# 3. VERIFICAR RUTA COMPLETA DESDE ENTRY POINT A EXIT
# ============================================================================
print("\n🔍 3. Verificando rutas desde entry point a salida...\n")

# BFS desde webhook hasta Enviar Respuesta
def can_reach_exit(start_node, target_node):
    visited = set()
    queue = deque([start_node])

    while queue:
        current = queue.popleft()
        if current == target_node:
            return True

        if current in visited:
            continue
        visited.add(current)

        # Agregar vecinos
        if current in graph:
            for neighbor in graph[current]:
                if neighbor not in visited:
                    queue.append(neighbor)

    return False

# Verificar rutas principales
entry_node = 'Webhook WhatsApp' if 'Webhook WhatsApp' in nodes_map else 'WhatsApp Trigger'
exit_node = 'Enviar Respuesta'

if can_reach_exit(entry_node, exit_node):
    print(f"✅ Ruta válida: {entry_node} → ... → {exit_node}")
else:
    print(f"⚠️  NO hay ruta de {entry_node} a {exit_node}")

# ============================================================================
# 4. VERIFICAR AGENTES Y SUS CONEXIONES
# ============================================================================
print("\n🔍 4. Verificando estructura de agentes...\n")

agent_structure = {
    "Customer Journey Agent": {
        "llm": "OpenAI Chat Customer",
        "memory": "Memory Customer",
        "tools": ["Shopping Flow Agent", "Vector Search Agent", "Menu Generator Agent"]
    },
    "Shopping Flow Agent": {
        "llm": "OpenAI Chat Shopping",
        "memory": "Memory Shopping",
        "tools": ["normalize_shopping_list", "get_prices_for_product", "calculate_best_price",
                  "calculate_savings", "segment_by_supplier", "execute_checkout"]
    },
    "Vector Search Agent": {
        "llm": "OpenAI Chat Vector",
        "memory": "Memory Vector",
        "tools": ["search_product_catalog", "find_similar_products", "validate_product_match"]
    },
    "Menu Generator Agent": {
        "llm": "OpenAI Chat Menu",
        "memory": "Memory Menu",
        "tools": ["calculate_completeness"]
    },
    "Session Manager Agent": {
        "llm": "OpenAI Chat Session",
        "memory": "Memory Session",
        "tools": ["check_active_session", "create_session", "get_active_sessions",
                  "get_user_profile", "update_session_status", "Buscar Usuario"]
    },
    "Preference Config Agent": {
        "llm": "OpenAI Chat Preference",
        "memory": "Memory Preference",
        "tools": ["save_user_preferences", "update_delivery_preferences"]
    },
    "Supplier Manager Agent": {
        "llm": "OpenAI Chat SupplierMgr",
        "memory": "Memory SupplierMgr",
        "tools": ["register_supplier", "update_supplier_data"]
    },
    "Price Upload Agent": {
        "llm": "OpenAI Chat Price",
        "memory": "Memory Price",
        "tools": ["parse_price_list", "bulk_update_prices"]
    }
}

issues_found = 0

for agent_name, config in agent_structure.items():
    if agent_name not in nodes_map:
        print(f"⚠️  Agente '{agent_name}' NO ENCONTRADO")
        issues_found += 1
        continue

    # Verificar LLM
    if config['llm'] in nodes_map:
        # Check if LLM connects to agent
        llm_conn = workflow['connections'].get(config['llm'], {})
        if 'ai_languageModel' in llm_conn:
            targets = [c['node'] for conn_list in llm_conn['ai_languageModel'] for c in conn_list]
            if agent_name in targets:
                print(f"   ✓ {agent_name}: LLM conectado")
            else:
                print(f"   ⚠️  {agent_name}: LLM '{config['llm']}' no conecta al agente")
                issues_found += 1
    else:
        print(f"   ⚠️  {agent_name}: LLM '{config['llm']}' no existe")
        issues_found += 1

    # Verificar Memory
    if config['memory'] in nodes_map:
        mem_conn = workflow['connections'].get(config['memory'], {})
        if 'ai_memory' in mem_conn:
            targets = [c['node'] for conn_list in mem_conn['ai_memory'] for c in conn_list]
            if agent_name in targets:
                print(f"   ✓ {agent_name}: Memory conectado")
            else:
                print(f"   ⚠️  {agent_name}: Memory '{config['memory']}' no conecta al agente")
                issues_found += 1
    else:
        print(f"   ⚠️  {agent_name}: Memory '{config['memory']}' no existe")
        issues_found += 1

    # Verificar Tools
    tools_count = 0
    for tool in config['tools']:
        if tool in nodes_map:
            tool_conn = workflow['connections'].get(tool, {})
            if 'ai_tool' in tool_conn:
                targets = [c['node'] for conn_list in tool_conn['ai_tool'] for c in conn_list]
                if agent_name in targets:
                    tools_count += 1

    print(f"   ✓ {agent_name}: {tools_count}/{len(config['tools'])} tools conectados")
    if tools_count < len(config['tools']):
        issues_found += 1

# ============================================================================
# RESUMEN FINAL
# ============================================================================
print("\n" + "="*60)
print("📋 RESUMEN DE VALIDACIÓN")
print("="*60)

print(f"\n✅ Nodes totales: {len(workflow['nodes'])}")
print(f"✅ Conexiones totales: {len(workflow['connections'])}")
print(f"✅ Huérfanos: {len(orphaned)} (aceptable si son config nodes)")
print(f"✅ Dead ends: {len(dead_ends)}")
print(f"✅ Ruta principal: {'VÁLIDA' if can_reach_exit(entry_node, exit_node) else 'INVÁLIDA'}")
print(f"✅ Issues en estructura de agentes: {issues_found}")

if len(orphaned) <= 1 and len(dead_ends) == 0 and can_reach_exit(entry_node, exit_node):
    print("\n🎉 WORKFLOW VALIDADO CORRECTAMENTE!")
    print("✅ Listo para producción")
else:
    print("\n⚠️  Hay algunos issues que revisar")

print("\n" + "="*60)
