#!/usr/bin/env python3
"""
Script para corregir los últimos issues:
1. Menu Generator Agent dead end
2. Verificar entry point correcto
"""

import json

print("🔧 Corrigiendo issues finales...\n")

# Cargar workflow
with open('Frepi_MVP2_Agent_Architecture.json', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

nodes_map = {node['name']: node['id'] for node in workflow['nodes']}

# ============================================================================
# 1. CORREGIR MENU GENERATOR AGENT DEAD END
# ============================================================================
print("🔗 1. Conectando Menu Generator Agent → Deduplicar Mensajes...\n")

# Menu Generator Agent debe tener salida main a Deduplicar
if 'Menu Generator Agent' in nodes_map and 'Deduplicar Mensajes' in nodes_map:
    # Verificar conexión actual
    if 'Menu Generator Agent' in workflow['connections']:
        # Ya tiene conexiones ai_tool, agregar main
        workflow['connections']['Menu Generator Agent']['main'] = [
            [{"node": "Deduplicar Mensajes", "type": "main", "index": 0}]
        ]
    else:
        workflow['connections']['Menu Generator Agent'] = {
            "ai_tool": [[{"node": "Customer Journey Agent", "type": "ai_tool", "index": 0}]],
            "main": [[{"node": "Deduplicar Mensajes", "type": "main", "index": 0}]]
        }
    print("   ✓ Menu Generator Agent → Deduplicar Mensajes")

# ============================================================================
# 2. VERIFICAR Y CONSOLIDAR ENTRY POINT
# ============================================================================
print("\n🔗 2. Consolidando entry point...\n")

# Determinar cuál es el webhook real mirando el tipo de nodo
webhook_node = None
for node in workflow['nodes']:
    if node['name'] == 'Webhook WhatsApp':
        webhook_node = 'Webhook WhatsApp'
        print(f"   ℹ️  Entry point principal: Webhook WhatsApp (tipo: {node.get('type', 'N/A')})")
        break
    elif node['name'] == 'WhatsApp Trigger':
        webhook_node = 'WhatsApp Trigger'
        print(f"   ℹ️  Entry point alternativo: WhatsApp Trigger (tipo: {node.get('type', 'N/A')})")

# Si ambos existen, eliminar el duplicado WhatsApp Trigger
if 'Webhook WhatsApp' in nodes_map and 'WhatsApp Trigger' in nodes_map:
    print("   ⚠️  Detectados dos webhooks. Eliminando WhatsApp Trigger duplicado...")

    # Eliminar WhatsApp Trigger de nodes
    workflow['nodes'] = [n for n in workflow['nodes'] if n['name'] != 'WhatsApp Trigger']

    # Eliminar de connections
    if 'WhatsApp Trigger' in workflow['connections']:
        del workflow['connections']['WhatsApp Trigger']

    # Verificar que Webhook WhatsApp esté conectado
    if 'Webhook WhatsApp' not in workflow['connections']:
        workflow['connections']['Webhook WhatsApp'] = {
            "main": [[{"node": "Extraer Datos WhatsApp", "type": "main", "index": 0}]]
        }

    print("   ✓ WhatsApp Trigger eliminado")
    print("   ✓ Webhook WhatsApp configurado como entry point único")

elif 'WhatsApp Trigger' in nodes_map:
    # Solo existe WhatsApp Trigger, asegurar que esté conectado
    if 'WhatsApp Trigger' not in workflow['connections']:
        workflow['connections']['WhatsApp Trigger'] = {
            "main": [[{"node": "Extraer Datos WhatsApp", "type": "main", "index": 0}]]
        }
        print("   ✓ WhatsApp Trigger → Extraer Datos WhatsApp")

# ============================================================================
# 3. VERIFICAR CADENA COMPLETA DESDE ENTRY POINT
# ============================================================================
print("\n🔗 3. Verificando cadena completa...\n")

# Reconstruir nodos_map sin WhatsApp Trigger
nodes_map = {node['name']: node['id'] for node in workflow['nodes']}

# Lista de conexiones críticas que deben existir
critical_chain = [
    ('Webhook WhatsApp', 'Extraer Datos WhatsApp'),
    ('Extraer Datos WhatsApp', 'Check Duplicate Message'),
    ('Check Duplicate Message', 'Get User Config'),
    ('Get User Config', 'IF: Usuario Existe?'),
    ('Customer Journey Agent', 'Deduplicar Mensajes'),
    ('Menu Generator Agent', 'Deduplicar Mensajes'),
    ('Preference Config Agent', 'Deduplicar Mensajes'),
    ('Supplier Journey Agent', 'Deduplicar Mensajes'),
    ('Deduplicar Mensajes', 'Enviar Respuesta')
]

missing_connections = []

for source, target in critical_chain:
    if source not in nodes_map or target not in nodes_map:
        continue

    if source not in workflow['connections']:
        missing_connections.append((source, target))
        continue

    # Verificar si existe conexión main
    conn_data = workflow['connections'][source]
    if 'main' not in conn_data:
        missing_connections.append((source, target))
        continue

    # Verificar si target está en la lista
    targets = [c['node'] for conn_list in conn_data['main'] for c in conn_list]
    if target not in targets:
        missing_connections.append((source, target))

if missing_connections:
    print("   ⚠️  Conexiones críticas faltantes:")
    for source, target in missing_connections:
        print(f"      - {source} → {target}")

    # Intentar agregar conexiones faltantes
    for source, target in missing_connections:
        if source in workflow['connections'] and 'main' in workflow['connections'][source]:
            # Verificar si ya tiene otra conexión, no sobrescribir
            existing = [c['node'] for conn_list in workflow['connections'][source]['main'] for c in conn_list]
            if target not in existing:
                print(f"      ℹ️  {source} ya tiene conexión main a {existing}, no sobrescribiremos")
        else:
            # Agregar la conexión
            if source not in workflow['connections']:
                workflow['connections'][source] = {}
            workflow['connections'][source]['main'] = [[{"node": target, "type": "main", "index": 0}]]
            print(f"      ✓ Agregada: {source} → {target}")
else:
    print("   ✅ Todas las conexiones críticas presentes")

# ============================================================================
# GUARDAR
# ============================================================================
print("\n💾 Guardando workflow corregido...\n")
with open('Frepi_MVP2_Agent_Architecture.json', 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("✅ CORRECCIONES FINALES APLICADAS!")
print(f"\n📊 ESTADÍSTICAS:")
print(f"   Total nodes: {len(workflow['nodes'])}")
print(f"   Total connections: {len(workflow['connections'])}")

print(f"\n📁 Archivo guardado: Frepi_MVP2_Agent_Architecture.json")
