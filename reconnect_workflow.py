#!/usr/bin/env python3
"""
Script para reconectar completamente el workflow Frepi MVP2 siguiendo el patrón espina dorsal
"""

import json
import uuid
from datetime import datetime

print("🔧 Iniciando reconexión completa del workflow Frepi MVP2...\n")

# Cargar workflow actual
with open('Frepi_MVP2_Agent_Architecture.json', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# Backup
backup_file = f'Frepi_MVP2_Agent_Architecture_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
with open(backup_file, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)
print(f"✅ Backup creado: {backup_file}\n")

# Resetear todas las conexiones para reconstruir desde cero
workflow['connections'] = {}

print("📊 Análisis del workflow:")
print(f"   Total nodes: {len(workflow['nodes'])}")

# Identificar nodos clave por nombre
nodes_map = {node['name']: node['id'] for node in workflow['nodes']}
print(f"   Nodos mapeados: {len(nodes_map)}")

# ============================================================================
# PASO 1: ESPINA DORSAL PRINCIPAL
# ============================================================================
print("\n🔗 PASO 1: Construyendo espina dorsal principal...\n")

# 1.1: Webhook WhatsApp → Extraer Datos WhatsApp
if 'Webhook WhatsApp' in nodes_map and 'Extraer Datos WhatsApp' in nodes_map:
    workflow['connections']['Webhook WhatsApp'] = {
        "main": [[{"node": "Extraer Datos WhatsApp", "type": "main", "index": 0}]]
    }
    print("   ✓ Webhook WhatsApp → Extraer Datos WhatsApp")

# 1.2: Extraer Datos WhatsApp → Check Duplicate Message
if 'Extraer Datos WhatsApp' in nodes_map and 'Check Duplicate Message' in nodes_map:
    workflow['connections']['Extraer Datos WhatsApp'] = {
        "main": [[{"node": "Check Duplicate Message", "type": "main", "index": 0}]]
    }
    print("   ✓ Extraer Datos WhatsApp → Check Duplicate Message")

# 1.3: Check Duplicate Message → Get User Config
if 'Check Duplicate Message' in nodes_map and 'Get User Config' in nodes_map:
    workflow['connections']['Check Duplicate Message'] = {
        "main": [[{"node": "Get User Config", "type": "main", "index": 0}]]
    }
    print("   ✓ Check Duplicate Message → Get User Config")

# 1.4: Get User Config → IF: Usuario Existe?
if 'Get User Config' in nodes_map and 'IF: Usuario Existe?' in nodes_map:
    workflow['connections']['Get User Config'] = {
        "main": [[{"node": "IF: Usuario Existe?", "type": "main", "index": 0}]]
    }
    print("   ✓ Get User Config → IF: Usuario Existe?")

# 1.5: IF: Usuario Existe? (TRUE) → Session Manager Agent
if 'IF: Usuario Existe?' in nodes_map and 'Session Manager Agent' in nodes_map:
    workflow['connections']['IF: Usuario Existe?'] = {
        "main": [
            [{"node": "Session Manager Agent", "type": "main", "index": 0}],  # true branch
            [{"node": "Onboarding Flow Agent", "type": "main", "index": 0}]   # false branch
        ]
    }
    print("   ✓ IF: Usuario Existe? → Session Manager Agent (true)")
    print("   ✓ IF: Usuario Existe? → Onboarding Flow Agent (false)")

# 1.6: Session Manager Agent → Switch: Session Type
if 'Session Manager Agent' in nodes_map and 'Switch: Session Type' in nodes_map:
    workflow['connections']['Session Manager Agent'] = {
        "main": [[{"node": "Switch: Session Type", "type": "main", "index": 0}]]
    }
    print("   ✓ Session Manager Agent → Switch: Session Type")

# ============================================================================
# PASO 2: CREAR Y CONECTAR NODO "Insertar Usuario"
# ============================================================================
print("\n🔗 PASO 2: Creando nodo Insertar Usuario...\n")

# Verificar si ya existe
if 'Insertar Usuario' not in nodes_map:
    insertar_usuario_node = {
        "parameters": {
            "operation": "insert",
            "table": {
                "__rl": True,
                "mode": "list",
                "value": "line_restaurants",
                "cachedResultName": "line_restaurants"
            },
            "columns": {
                "mappingMode": "defineBelow",
                "value": {
                    "phone_number": "={{ $json.phone_number }}",
                    "name": "={{ $json.restaurant_name || 'Novo Restaurante' }}",
                    "city": "={{ $json.city || '' }}",
                    "preferred_brands": "={{ $json.preferred_brands || '[]' }}",
                    "preferred_formats": "={{ $json.preferred_formats || '[]' }}",
                    "created_at": "={{ $now.toISO() }}"
                },
                "matchingColumns": [],
                "schema": []
            },
            "options": {}
        },
        "type": "@n8n/n8n-nodes-langchain.supabase",
        "typeVersion": 1.1,
        "position": [-2240, 880],
        "id": str(uuid.uuid4()),
        "name": "Insertar Usuario",
        "credentials": {
            "supabaseApi": {
                "id": "OKXSj3tzGQwuy8R3",
                "name": "Supabase account"
            }
        }
    }
    workflow['nodes'].append(insertar_usuario_node)
    nodes_map['Insertar Usuario'] = insertar_usuario_node['id']
    print("   ✓ Nodo 'Insertar Usuario' creado")

# 2.1: Onboarding Flow Agent → Insertar Usuario
if 'Onboarding Flow Agent' in nodes_map and 'Insertar Usuario' in nodes_map:
    workflow['connections']['Onboarding Flow Agent'] = {
        "main": [[{"node": "Insertar Usuario", "type": "main", "index": 0}]]
    }
    print("   ✓ Onboarding Flow Agent → Insertar Usuario")

# 2.2: Insertar Usuario → Enviar Respuesta
if 'Insertar Usuario' in nodes_map and 'Enviar Respuesta' in nodes_map:
    workflow['connections']['Insertar Usuario'] = {
        "main": [[{"node": "Enviar Respuesta", "type": "main", "index": 0}]]
    }
    print("   ✓ Insertar Usuario → Enviar Respuesta")

# 2.3: Enviar Respuesta → Session Manager Agent (loop back)
# Note: This creates a loop for continuing after onboarding
if 'Enviar Respuesta' in nodes_map:
    # Enviar Respuesta ya tiene su conexión principal que termina el flujo
    # Pero podemos agregar una segunda salida que vuelve al Session Manager
    # En n8n esto se hace con múltiples outputs en el mismo array
    pass  # La conexión ya existe en el flujo normal

# ============================================================================
# PASO 3: CONECTAR CUSTOMER JOURNEY AGENT Y SUS SUB-AGENTS
# ============================================================================
print("\n🔗 PASO 3: Conectando Customer Journey Agent...\n")

# 3.1: Switch → Customer Journey Agent (case 0: compra)
if 'Switch: Session Type' in nodes_map and 'Customer Journey Agent' in nodes_map:
    workflow['connections']['Switch: Session Type'] = {
        "main": [
            [{"node": "Customer Journey Agent", "type": "main", "index": 0}],  # case 0: compra
            [{"node": "Menu Generator Agent", "type": "main", "index": 0}],     # case 1: menu
            [{"node": "Preference Config Agent", "type": "main", "index": 0}],  # case 2: preferencias
            [{"node": "Supplier Journey Agent", "type": "main", "index": 0}]    # case 3: fornecedor
        ]
    }
    print("   ✓ Switch case 0 → Customer Journey Agent")
    print("   ✓ Switch case 1 → Menu Generator Agent")
    print("   ✓ Switch case 2 → Preference Config Agent")
    print("   ✓ Switch case 3 → Supplier Journey Agent")

# 3.2: Customer Journey Agent connections
# Customer Journey agent tiene varios sub-agents como tools
sub_agents_cj = [
    'Shopping Flow Agent',
    'Vector Search Agent',
    'Menu Generator Agent'
]

# Shopping Flow Agent y sus tools
if 'Shopping Flow Agent' in nodes_map:
    shopping_tools = [
        'normalize_shopping_list',
        'get_prices_for_product',
        'calculate_best_price',
        'calculate_savings',
        'segment_by_supplier'
    ]

    workflow['connections']['Shopping Flow Agent'] = {
        "ai_tool": [[{"node": "Customer Journey Agent", "type": "ai_tool", "index": 0}]]
    }
    print("   ✓ Shopping Flow Agent → Customer Journey Agent (ai_tool)")

    # Conectar LLM y Memory al Shopping Flow Agent
    if 'OpenAI Chat Shopping' in nodes_map:
        workflow['connections']['OpenAI Chat Shopping'] = {
            "ai_languageModel": [[{"node": "Shopping Flow Agent", "type": "ai_languageModel", "index": 0}]]
        }
        print("   ✓ OpenAI Chat Shopping → Shopping Flow Agent")

    if 'Memory Shopping' in nodes_map:
        workflow['connections']['Memory Shopping'] = {
            "ai_memory": [[{"node": "Shopping Flow Agent", "type": "ai_memory", "index": 0}]]
        }
        print("   ✓ Memory Shopping → Shopping Flow Agent")

    # Conectar tools al Shopping Flow Agent
    for tool in shopping_tools:
        if tool in nodes_map:
            workflow['connections'][tool] = {
                "ai_tool": [[{"node": "Shopping Flow Agent", "type": "ai_tool", "index": 0}]]
            }
            print(f"   ✓ {tool} → Shopping Flow Agent")

# Vector Search Agent y sus tools
if 'Vector Search Agent' in nodes_map:
    vector_tools = [
        'search_product_catalog',
        'find_similar_products',
        'validate_product_match'
    ]

    workflow['connections']['Vector Search Agent'] = {
        "ai_tool": [[{"node": "Customer Journey Agent", "type": "ai_tool", "index": 0}]]
    }
    print("   ✓ Vector Search Agent → Customer Journey Agent (ai_tool)")

    # Conectar LLM y Memory
    if 'OpenAI Chat Vector' in nodes_map:
        workflow['connections']['OpenAI Chat Vector'] = {
            "ai_languageModel": [[{"node": "Vector Search Agent", "type": "ai_languageModel", "index": 0}]]
        }
        print("   ✓ OpenAI Chat Vector → Vector Search Agent")

    if 'Memory Vector' in nodes_map:
        workflow['connections']['Memory Vector'] = {
            "ai_memory": [[{"node": "Vector Search Agent", "type": "ai_memory", "index": 0}]]
        }
        print("   ✓ Memory Vector → Vector Search Agent")

    # Conectar Supabase Vector Store
    if 'Supabase Vector Store' in nodes_map:
        workflow['connections']['Supabase Vector Store'] = {
            "ai_vectorStore": [[{"node": "Vector Search Agent", "type": "ai_vectorStore", "index": 0}]]
        }
        print("   ✓ Supabase Vector Store → Vector Search Agent")

    # Conectar OpenAI Embeddings
    if 'OpenAI Embeddings' in nodes_map:
        workflow['connections']['OpenAI Embeddings'] = {
            "ai_embedding": [[{"node": "Supabase Vector Store", "type": "ai_embedding", "index": 0}]]
        }
        print("   ✓ OpenAI Embeddings → Supabase Vector Store")

    # Conectar tools
    for tool in vector_tools:
        if tool in nodes_map:
            workflow['connections'][tool] = {
                "ai_tool": [[{"node": "Vector Search Agent", "type": "ai_tool", "index": 0}]]
            }
            print(f"   ✓ {tool} → Vector Search Agent")

# ============================================================================
# PASO 4: CONECTAR MENU GENERATOR AGENT
# ============================================================================
print("\n🔗 PASO 4: Conectando Menu Generator Agent...\n")

if 'Menu Generator Agent' in nodes_map:
    # Menu Generator como tool de Customer Journey
    if 'Menu Generator Agent' not in workflow['connections']:
        workflow['connections']['Menu Generator Agent'] = {}

    workflow['connections']['Menu Generator Agent']['ai_tool'] = [
        [{"node": "Customer Journey Agent", "type": "ai_tool", "index": 0}]
    ]
    print("   ✓ Menu Generator Agent → Customer Journey Agent (ai_tool)")

    # LLM y Memory para Menu Generator
    if 'OpenAI Chat Menu' in nodes_map:
        workflow['connections']['OpenAI Chat Menu'] = {
            "ai_languageModel": [[{"node": "Menu Generator Agent", "type": "ai_languageModel", "index": 0}]]
        }
        print("   ✓ OpenAI Chat Menu → Menu Generator Agent")

    if 'Memory Menu' in nodes_map:
        workflow['connections']['Memory Menu'] = {
            "ai_memory": [[{"node": "Menu Generator Agent", "type": "ai_memory", "index": 0}]]
        }
        print("   ✓ Memory Menu → Menu Generator Agent")

    # Tools
    menu_tools = ['calculate_completeness']
    for tool in menu_tools:
        if tool in nodes_map:
            workflow['connections'][tool] = {
                "ai_tool": [[{"node": "Menu Generator Agent", "type": "ai_tool", "index": 0}]]
            }
            print(f"   ✓ {tool} → Menu Generator Agent")

# ============================================================================
# PASO 5: CONECTAR PREFERENCE CONFIG AGENT
# ============================================================================
print("\n🔗 PASO 5: Conectando Preference Config Agent...\n")

if 'Preference Config Agent' in nodes_map:
    # Preference Config recibe del Switch y va a Deduplicar
    workflow['connections']['Preference Config Agent'] = {
        "main": [[{"node": "Deduplicar Mensajes", "type": "main", "index": 0}]]
    }
    print("   ✓ Preference Config Agent → Deduplicar Mensajes")

    # LLM y Memory
    if 'OpenAI Chat Preferences' in nodes_map:
        workflow['connections']['OpenAI Chat Preferences'] = {
            "ai_languageModel": [[{"node": "Preference Config Agent", "type": "ai_languageModel", "index": 0}]]
        }
        print("   ✓ OpenAI Chat Preferences → Preference Config Agent")

    if 'Memory Preferences' in nodes_map:
        workflow['connections']['Memory Preferences'] = {
            "ai_memory": [[{"node": "Preference Config Agent", "type": "ai_memory", "index": 0}]]
        }
        print("   ✓ Memory Preferences → Preference Config Agent")

    # Tools
    pref_tools = ['save_user_preferences', 'update_delivery_preferences']
    for tool in pref_tools:
        if tool in nodes_map:
            workflow['connections'][tool] = {
                "ai_tool": [[{"node": "Preference Config Agent", "type": "ai_tool", "index": 0}]]
            }
            print(f"   ✓ {tool} → Preference Config Agent")

# ============================================================================
# PASO 6: CONECTAR SUPPLIER JOURNEY AGENT
# ============================================================================
print("\n🔗 PASO 6: Conectando Supplier Journey Agent...\n")

if 'Supplier Journey Agent' in nodes_map:
    # Supplier Journey tiene sub-agents
    workflow['connections']['Supplier Journey Agent'] = {
        "main": [[{"node": "Deduplicar Mensajes", "type": "main", "index": 0}]]
    }
    print("   ✓ Supplier Journey Agent → Deduplicar Mensajes")

    # LLM y Memory
    if 'OpenAI Chat Supplier Journey' in nodes_map:
        workflow['connections']['OpenAI Chat Supplier Journey'] = {
            "ai_languageModel": [[{"node": "Supplier Journey Agent", "type": "ai_languageModel", "index": 0}]]
        }
        print("   ✓ OpenAI Chat Supplier Journey → Supplier Journey Agent")

    if 'Memory Supplier Journey' in nodes_map:
        workflow['connections']['Memory Supplier Journey'] = {
            "ai_memory": [[{"node": "Supplier Journey Agent", "type": "ai_memory", "index": 0}]]
        }
        print("   ✓ Memory Supplier Journey → Supplier Journey Agent")

    # Sub-agents del Supplier Journey
    # Supplier Manager Agent
    if 'Supplier Manager Agent' in nodes_map:
        workflow['connections']['Supplier Manager Agent'] = {
            "ai_tool": [[{"node": "Supplier Journey Agent", "type": "ai_tool", "index": 0}]]
        }
        print("   ✓ Supplier Manager Agent → Supplier Journey Agent")

        # LLM y Memory para Supplier Manager
        if 'OpenAI Chat Supplier' in nodes_map:
            workflow['connections']['OpenAI Chat Supplier'] = {
                "ai_languageModel": [[{"node": "Supplier Manager Agent", "type": "ai_languageModel", "index": 0}]]
            }
            print("   ✓ OpenAI Chat Supplier → Supplier Manager Agent")

        if 'Memory Supplier' in nodes_map:
            workflow['connections']['Memory Supplier'] = {
                "ai_memory": [[{"node": "Supplier Manager Agent", "type": "ai_memory", "index": 0}]]
            }
            print("   ✓ Memory Supplier → Supplier Manager Agent")

        # Tools
        supplier_tools = ['register_supplier', 'update_supplier_data']
        for tool in supplier_tools:
            if tool in nodes_map:
                workflow['connections'][tool] = {
                    "ai_tool": [[{"node": "Supplier Manager Agent", "type": "ai_tool", "index": 0}]]
                }
                print(f"   ✓ {tool} → Supplier Manager Agent")

    # Price Upload Agent
    if 'Price Upload Agent' in nodes_map:
        workflow['connections']['Price Upload Agent'] = {
            "ai_tool": [[{"node": "Supplier Journey Agent", "type": "ai_tool", "index": 0}]]
        }
        print("   ✓ Price Upload Agent → Supplier Journey Agent")

        # LLM y Memory para Price Upload
        if 'OpenAI Chat Price' in nodes_map:
            workflow['connections']['OpenAI Chat Price'] = {
                "ai_languageModel": [[{"node": "Price Upload Agent", "type": "ai_languageModel", "index": 0}]]
            }
            print("   ✓ OpenAI Chat Price → Price Upload Agent")

        if 'Memory Price' in nodes_map:
            workflow['connections']['Memory Price'] = {
                "ai_memory": [[{"node": "Price Upload Agent", "type": "ai_memory", "index": 0}]]
            }
            print("   ✓ Memory Price → Price Upload Agent")

        # Tools
        price_tools = ['parse_price_list', 'bulk_update_prices']
        for tool in price_tools:
            if tool in nodes_map:
                workflow['connections'][tool] = {
                    "ai_tool": [[{"node": "Price Upload Agent", "type": "ai_tool", "index": 0}]]
                }
                print(f"   ✓ {tool} → Price Upload Agent")

# ============================================================================
# PASO 7: CONECTAR CUSTOMER JOURNEY AGENT → DEDUPLICAR → ENVIAR
# ============================================================================
print("\n🔗 PASO 7: Conectando salidas finales...\n")

# Customer Journey → Deduplicar Mensajes
if 'Customer Journey Agent' in nodes_map and 'Deduplicar Mensajes' in nodes_map:
    workflow['connections']['Customer Journey Agent'] = {
        "main": [[{"node": "Deduplicar Mensajes", "type": "main", "index": 0}]]
    }
    print("   ✓ Customer Journey Agent → Deduplicar Mensajes")

# Deduplicar Mensajes → Enviar Respuesta
if 'Deduplicar Mensajes' in nodes_map and 'Enviar Respuesta' in nodes_map:
    workflow['connections']['Deduplicar Mensajes'] = {
        "main": [[{"node": "Enviar Respuesta", "type": "main", "index": 0}]]
    }
    print("   ✓ Deduplicar Mensajes → Enviar Respuesta")

# ============================================================================
# PASO 8: CONECTAR ONBOARDING FLOW AGENT
# ============================================================================
print("\n🔗 PASO 8: Conectando Onboarding Flow Agent...\n")

if 'Onboarding Flow Agent' in nodes_map:
    # LLM y Memory
    if 'OpenAI Chat Onboarding' in nodes_map:
        workflow['connections']['OpenAI Chat Onboarding'] = {
            "ai_languageModel": [[{"node": "Onboarding Flow Agent", "type": "ai_languageModel", "index": 0}]]
        }
        print("   ✓ OpenAI Chat Onboarding → Onboarding Flow Agent")

    if 'Memory Onboarding' in nodes_map:
        workflow['connections']['Memory Onboarding'] = {
            "ai_memory": [[{"node": "Onboarding Flow Agent", "type": "ai_memory", "index": 0}]]
        }
        print("   ✓ Memory Onboarding → Onboarding Flow Agent")

# ============================================================================
# PASO 9: CONECTAR SESSION MANAGER AGENT
# ============================================================================
print("\n🔗 PASO 9: Conectando Session Manager Agent...\n")

if 'Session Manager Agent' in nodes_map:
    # LLM y Memory
    if 'OpenAI Chat Session' in nodes_map:
        workflow['connections']['OpenAI Chat Session'] = {
            "ai_languageModel": [[{"node": "Session Manager Agent", "type": "ai_languageModel", "index": 0}]]
        }
        print("   ✓ OpenAI Chat Session → Session Manager Agent")

    if 'Memory Session' in nodes_map:
        workflow['connections']['Memory Session'] = {
            "ai_memory": [[{"node": "Session Manager Agent", "type": "ai_memory", "index": 0}]]
        }
        print("   ✓ Memory Session → Session Manager Agent")

    # Tools
    session_tools = ['classify_intent', 'get_active_session']
    for tool in session_tools:
        if tool in nodes_map:
            workflow['connections'][tool] = {
                "ai_tool": [[{"node": "Session Manager Agent", "type": "ai_tool", "index": 0}]]
            }
            print(f"   ✓ {tool} → Session Manager Agent")

# ============================================================================
# GUARDAR WORKFLOW RECONECTADO
# ============================================================================
print("\n💾 Guardando workflow reconectado...\n")
with open('Frepi_MVP2_Agent_Architecture.json', 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("✅ RECONEXIÓN COMPLETADA!")
print(f"\n📊 ESTADÍSTICAS FINALES:")
print(f"   Total nodes: {len(workflow['nodes'])}")
print(f"   Total connections: {len(workflow['connections'])}")
print(f"   Nodos conectados: {len([n for n in workflow['connections'].values() if n])}")

# Validar huérfanos
all_node_names = set(nodes_map.keys())
connected_nodes = set(workflow['connections'].keys())
for conn_data in workflow['connections'].values():
    for conn_type_list in conn_data.values():
        for conn_list in conn_type_list:
            for conn in conn_list:
                connected_nodes.add(conn['node'])

# Nodos que no son Webhook ni están conectados
orphaned = all_node_names - connected_nodes - {'Webhook WhatsApp'}
if orphaned:
    print(f"\n⚠️  NODOS HUÉRFANOS DETECTADOS ({len(orphaned)}):")
    for node in sorted(orphaned):
        print(f"   - {node}")
else:
    print("\n✅ 0 NODOS HUÉRFANOS")

print(f"\n📁 Archivo guardado: Frepi_MVP2_Agent_Architecture.json")
print(f"📁 Backup: {backup_file}")
