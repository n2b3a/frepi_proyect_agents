#!/usr/bin/env python3
"""
Script para conectar los nodos huérfanos restantes
"""

import json

print("🔧 Conectando nodos huérfanos...\n")

# Cargar workflow
with open('Frepi_MVP2_Agent_Architecture.json', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# Mapa de nodos
nodes_map = {node['name']: node['id'] for node in workflow['nodes']}

# ============================================================================
# GRUPO 1: TOOLS DEL SESSION MANAGER AGENT
# ============================================================================
print("🔗 Conectando tools del Session Manager Agent...\n")

session_tools = [
    'check_active_session',
    'create_session',
    'get_active_sessions',
    'get_user_profile',
    'update_session_status'
]

for tool in session_tools:
    if tool in nodes_map:
        if tool not in workflow['connections']:
            workflow['connections'][tool] = {}
        workflow['connections'][tool]['ai_tool'] = [
            [{"node": "Session Manager Agent", "type": "ai_tool", "index": 0}]
        ]
        print(f"   ✓ {tool} → Session Manager Agent")

# ============================================================================
# GRUPO 2: EXECUTE_CHECKOUT TOOL PARA SHOPPING FLOW
# ============================================================================
print("\n🔗 Conectando execute_checkout...\n")

if 'execute_checkout' in nodes_map:
    workflow['connections']['execute_checkout'] = {
        "ai_tool": [[{"node": "Shopping Flow Agent", "type": "ai_tool", "index": 0}]]
    }
    print("   ✓ execute_checkout → Shopping Flow Agent")

# ============================================================================
# GRUPO 3: MEMORY Y LLM PARA CUSTOMER JOURNEY AGENT
# ============================================================================
print("\n🔗 Conectando Memory y LLM Customer Journey...\n")

if 'OpenAI Chat Customer' in nodes_map:
    workflow['connections']['OpenAI Chat Customer'] = {
        "ai_languageModel": [[{"node": "Customer Journey Agent", "type": "ai_languageModel", "index": 0}]]
    }
    print("   ✓ OpenAI Chat Customer → Customer Journey Agent")

if 'Memory Customer' in nodes_map:
    workflow['connections']['Memory Customer'] = {
        "ai_memory": [[{"node": "Customer Journey Agent", "type": "ai_memory", "index": 0}]]
    }
    print("   ✓ Memory Customer → Customer Journey Agent")

# ============================================================================
# GRUPO 4: MEMORY Y LLM PARA PREFERENCE CONFIG (adicionales si existen)
# ============================================================================
print("\n🔗 Verificando Memory y LLM Preference Config...\n")

if 'OpenAI Chat Preference' in nodes_map:
    workflow['connections']['OpenAI Chat Preference'] = {
        "ai_languageModel": [[{"node": "Preference Config Agent", "type": "ai_languageModel", "index": 0}]]
    }
    print("   ✓ OpenAI Chat Preference → Preference Config Agent")

if 'Memory Preference' in nodes_map:
    workflow['connections']['Memory Preference'] = {
        "ai_memory": [[{"node": "Preference Config Agent", "type": "ai_memory", "index": 0}]]
    }
    print("   ✓ Memory Preference → Preference Config Agent")

# ============================================================================
# GRUPO 5: MEMORY Y LLM PARA SUPPLIER MANAGER (adicionales si existen)
# ============================================================================
print("\n🔗 Verificando Memory y LLM Supplier Manager...\n")

if 'OpenAI Chat SupplierMgr' in nodes_map:
    workflow['connections']['OpenAI Chat SupplierMgr'] = {
        "ai_languageModel": [[{"node": "Supplier Manager Agent", "type": "ai_languageModel", "index": 0}]]
    }
    print("   ✓ OpenAI Chat SupplierMgr → Supplier Manager Agent")

if 'Memory SupplierMgr' in nodes_map:
    workflow['connections']['Memory SupplierMgr'] = {
        "ai_memory": [[{"node": "Supplier Manager Agent", "type": "ai_memory", "index": 0}]]
    }
    print("   ✓ Memory SupplierMgr → Supplier Manager Agent")

# ============================================================================
# GRUPO 6: CONFIG GLOBAL
# ============================================================================
print("\n🔗 Verificando Config Global...\n")

# Config Global podría ser un nodo de configuración que alimenta a múltiples nodos
# Por ahora lo dejamos sin conexión específica, ya que puede ser referenciado
# por expresiones en otros nodos
if 'Config Global' in nodes_map:
    print("   ℹ️  Config Global: Nodo de configuración (puede quedar sin conexión)")

# ============================================================================
# GRUPO 7: BUSCAR USUARIO
# ============================================================================
print("\n🔗 Conectando Buscar Usuario...\n")

# Buscar Usuario probablemente es el nodo que debería ser Get User Config
# Pero si existe separado, puede ser un tool del Onboarding o Session Manager
if 'Buscar Usuario' in nodes_map:
    # Conectar como alternativa a Get User Config
    # Webhook → Extraer Datos → Check Duplicate → Buscar Usuario ya NO se usa
    # porque usamos Get User Config
    # Lo conectamos como tool opcional del Session Manager
    workflow['connections']['Buscar Usuario'] = {
        "ai_tool": [[{"node": "Session Manager Agent", "type": "ai_tool", "index": 0}]]
    }
    print("   ✓ Buscar Usuario → Session Manager Agent (ai_tool)")

# ============================================================================
# GRUPO 8: WHATSAPP TRIGGER
# ============================================================================
print("\n🔗 Verificando WhatsApp Trigger...\n")

# WhatsApp Trigger podría ser un duplicado de Webhook WhatsApp
# Si existe y no está conectado, podría ser el nodo inicial alternativo
if 'WhatsApp Trigger' in nodes_map:
    # Verificar si Webhook WhatsApp ya existe
    if 'Webhook WhatsApp' in nodes_map:
        print("   ⚠️  WhatsApp Trigger: Duplicado de Webhook WhatsApp (considerar eliminar)")
    else:
        # Si no existe Webhook WhatsApp, este es el trigger principal
        workflow['connections']['WhatsApp Trigger'] = {
            "main": [[{"node": "Extraer Datos WhatsApp", "type": "main", "index": 0}]]
        }
        print("   ✓ WhatsApp Trigger → Extraer Datos WhatsApp")

# ============================================================================
# PASO ADICIONAL: CONECTAR WEBHOOK WHATSAPP SI NO ESTABA CONECTADO
# ============================================================================
print("\n🔗 Verificando Webhook WhatsApp...\n")

if 'Webhook WhatsApp' in nodes_map:
    if 'Webhook WhatsApp' not in workflow['connections']:
        workflow['connections']['Webhook WhatsApp'] = {
            "main": [[{"node": "Extraer Datos WhatsApp", "type": "main", "index": 0}]]
        }
        print("   ✓ Webhook WhatsApp → Extraer Datos WhatsApp")
    else:
        print("   ✓ Webhook WhatsApp ya conectado")

# ============================================================================
# PASO ADICIONAL: CONECTAR GET USER CONFIG Y CHECK DUPLICATE
# ============================================================================
print("\n🔗 Verificando conexiones faltantes...\n")

if 'Check Duplicate Message' in nodes_map:
    if 'Check Duplicate Message' not in workflow['connections']:
        workflow['connections']['Check Duplicate Message'] = {
            "main": [[{"node": "Get User Config", "type": "main", "index": 0}]]
        }
        print("   ✓ Check Duplicate Message → Get User Config")

if 'Get User Config' in nodes_map:
    if 'Get User Config' not in workflow['connections']:
        workflow['connections']['Get User Config'] = {
            "main": [[{"node": "IF: Usuario Existe?", "type": "main", "index": 0}]]
        }
        print("   ✓ Get User Config → IF: Usuario Existe?")

if 'Extraer Datos WhatsApp' in nodes_map:
    if 'Extraer Datos WhatsApp' not in workflow['connections']:
        workflow['connections']['Extraer Datos WhatsApp'] = {
            "main": [[{"node": "Check Duplicate Message", "type": "main", "index": 0}]]
        }
        print("   ✓ Extraer Datos WhatsApp → Check Duplicate Message")

# ============================================================================
# CONECTAR SUPABASE VECTOR STORE SI NO ESTÁ CONECTADO
# ============================================================================
print("\n🔗 Verificando Supabase Vector Store...\n")

if 'Supabase Vector Store' in nodes_map:
    if 'Supabase Vector Store' not in workflow['connections']:
        workflow['connections']['Supabase Vector Store'] = {
            "ai_vectorStore": [[{"node": "Vector Search Agent", "type": "ai_vectorStore", "index": 0}]]
        }
        print("   ✓ Supabase Vector Store → Vector Search Agent")

if 'OpenAI Embeddings' in nodes_map:
    if 'OpenAI Embeddings' not in workflow['connections']:
        workflow['connections']['OpenAI Embeddings'] = {
            "ai_embedding": [[{"node": "Supabase Vector Store", "type": "ai_embedding", "index": 0}]]
        }
        print("   ✓ OpenAI Embeddings → Supabase Vector Store")

# ============================================================================
# GUARDAR
# ============================================================================
print("\n💾 Guardando workflow...\n")
with open('Frepi_MVP2_Agent_Architecture.json', 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

# Verificar huérfanos nuevamente
all_node_names = set(nodes_map.keys())
connected_nodes = set(workflow['connections'].keys())
for conn_data in workflow['connections'].values():
    for conn_type_list in conn_data.values():
        for conn_list in conn_type_list:
            for conn in conn_list:
                connected_nodes.add(conn['node'])

orphaned = all_node_names - connected_nodes - {'Webhook WhatsApp', 'WhatsApp Trigger'}

print("✅ SEGUNDA PASADA COMPLETADA!")
print(f"\n📊 ESTADÍSTICAS:")
print(f"   Total nodes: {len(workflow['nodes'])}")
print(f"   Total connections: {len(workflow['connections'])}")

if orphaned:
    print(f"\n⚠️  NODOS HUÉRFANOS RESTANTES ({len(orphaned)}):")
    for node in sorted(orphaned):
        print(f"   - {node}")
else:
    print("\n✅ 0 NODOS HUÉRFANOS!")

print(f"\n📁 Archivo guardado: Frepi_MVP2_Agent_Architecture.json")
