#!/usr/bin/env python3
"""
Script para corregir la conexión usando Buscar Usuario en lugar de Get User Config
"""

import json

print("🔧 Corrigiendo Buscar Usuario en el backbone...\n")

# Cargar workflow
with open('Frepi_MVP2_Agent_Architecture.json', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

nodes_map = {node['name']: node['id'] for node in workflow['nodes']}

# ============================================================================
# CORREGIR CHAIN: Check Duplicate → Buscar Usuario → IF: Usuario Existe?
# ============================================================================

print("🔗 Reconectando backbone con Buscar Usuario...\n")

# 1. Check Duplicate Message → Buscar Usuario
if 'Check Duplicate Message' in nodes_map and 'Buscar Usuario' in nodes_map:
    workflow['connections']['Check Duplicate Message'] = {
        "main": [[{"node": "Buscar Usuario", "type": "main", "index": 0}]]
    }
    print("   ✓ Check Duplicate Message → Buscar Usuario")

# 2. Buscar Usuario → IF: Usuario Existe?
if 'Buscar Usuario' in nodes_map and 'IF: Usuario Existe?' in nodes_map:
    # Buscar Usuario ya tiene conexión ai_tool, agregar main
    if 'Buscar Usuario' not in workflow['connections']:
        workflow['connections']['Buscar Usuario'] = {}

    # Preservar ai_tool si existe, agregar main
    if 'ai_tool' in workflow['connections']['Buscar Usuario']:
        workflow['connections']['Buscar Usuario']['main'] = [[{"node": "IF: Usuario Existe?", "type": "main", "index": 0}]]
    else:
        workflow['connections']['Buscar Usuario'] = {
            "main": [[{"node": "IF: Usuario Existe?", "type": "main", "index": 0}]]
        }

    print("   ✓ Buscar Usuario → IF: Usuario Existe?")

# ============================================================================
# VERIFICAR NODE TYPE DE BUSCAR USUARIO
# ============================================================================

print("\n🔍 Verificando tipo de nodo Buscar Usuario...\n")

buscar_usuario_node = next((n for n in workflow['nodes'] if n['name'] == 'Buscar Usuario'), None)
if buscar_usuario_node:
    node_type = buscar_usuario_node.get('type', 'unknown')
    print(f"   ℹ️  Buscar Usuario type: {node_type}")

    # Si es un toolCode, necesitamos convertirlo a Supabase node
    if 'toolCode' in node_type or 'tool' in node_type.lower():
        print("   ⚠️  Buscar Usuario es un tool, debería ser un nodo Supabase")
        print("   ℹ️  Vamos a crear un nuevo nodo Supabase para buscar usuario")

        # Buscar el nodo actual de Buscar Usuario y modificarlo
        for i, node in enumerate(workflow['nodes']):
            if node['name'] == 'Buscar Usuario':
                # Convertir a nodo Supabase
                workflow['nodes'][i] = {
                    "parameters": {
                        "operation": "get",
                        "table": {
                            "__rl": True,
                            "mode": "list",
                            "value": "line_restaurants",
                            "cachedResultName": "line_restaurants"
                        },
                        "filterType": "manual",
                        "matchingColumns": [
                            {
                                "column": "phone_number",
                                "operator": "=",
                                "value": "={{ $json.phone_number }}"
                            }
                        ],
                        "options": {}
                    },
                    "type": "@n8n/n8n-nodes-langchain.supabase",
                    "typeVersion": 1.1,
                    "position": buscar_usuario_node.get('position', [-2240, 240]),
                    "id": buscar_usuario_node.get('id'),
                    "name": "Buscar Usuario",
                    "credentials": {
                        "supabaseApi": {
                            "id": "OKXSj3tzGQwuy8R3",
                            "name": "Supabase account"
                        }
                    }
                }
                print("   ✓ Buscar Usuario convertido a nodo Supabase")
                break

# ============================================================================
# GUARDAR
# ============================================================================
print("\n💾 Guardando workflow...\n")
with open('Frepi_MVP2_Agent_Architecture.json', 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("✅ BUSCAR USUARIO CORREGIDO!")
print(f"\n📊 ESTADÍSTICAS:")
print(f"   Total nodes: {len(workflow['nodes'])}")
print(f"   Total connections: {len(workflow['connections'])}")

print(f"\n📁 Archivo guardado: Frepi_MVP2_Agent_Architecture.json")
