#!/usr/bin/env python3
"""
Script para asegurar que TODAS las conexiones del backbone principal existan
"""

import json

print("🔧 Reparando conexiones del backbone principal...\n")

# Cargar workflow
with open('Frepi_MVP2_Agent_Architecture.json', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

nodes_map = {node['name']: node['id'] for node in workflow['nodes']}

# Definir el backbone completo con todas las conexiones necesarias
backbone_connections = [
    # Entry point
    ('WhatsApp Trigger', 'Extraer Datos WhatsApp'),

    # Processing chain
    ('Extraer Datos WhatsApp', 'Check Duplicate Message'),
    ('Check Duplicate Message', 'Get User Config'),
    ('Get User Config', 'IF: Usuario Existe?'),

    # Branch handling (IF outputs)
    # TRUE: IF → Session Manager
    # FALSE: IF → Onboarding

    # Session Manager → Switch
    ('Session Manager Agent', 'Switch: Session Type'),

    # Switch outputs (handled separately below)

    # Onboarding flow
    ('Onboarding Flow Agent', 'Insertar Usuario'),
    ('Insertar Usuario', 'Enviar Respuesta'),

    # Final outputs
    ('Customer Journey Agent', 'Deduplicar Mensajes'),
    ('Menu Generator Agent', 'Deduplicar Mensajes'),
    ('Preference Config Agent', 'Deduplicar Mensajes'),
    ('Supplier Journey Agent', 'Deduplicar Mensajes'),
    ('Deduplicar Mensajes', 'Enviar Respuesta')
]

print("🔗 Verificando y agregando conexiones del backbone...\n")

for source, target in backbone_connections:
    if source not in nodes_map or target not in nodes_map:
        print(f"   ⚠️  SKIP: {source} → {target} (nodo no existe)")
        continue

    # Verificar si la conexión existe
    if source not in workflow['connections']:
        workflow['connections'][source] = {}

    if 'main' not in workflow['connections'][source]:
        workflow['connections'][source]['main'] = []

    # Verificar si ya tiene esta conexión específica
    existing_targets = []
    if workflow['connections'][source]['main']:
        for conn_list in workflow['connections'][source]['main']:
            for conn in conn_list:
                existing_targets.append(conn['node'])

    if target not in existing_targets:
        # Agregar la conexión
        # Si ya hay conexiones, es una bifurcación
        workflow['connections'][source]['main'].append([{"node": target, "type": "main", "index": 0}])
        print(f"   ✓ AGREGADA: {source} → {target}")
    else:
        print(f"   ✓ OK: {source} → {target}")

# ============================================================================
# MANEJAR IF: Usuario Existe? (tiene 2 outputs)
# ============================================================================
print("\n🔗 Configurando IF: Usuario Existe? (bifurcación)...\n")

if 'IF: Usuario Existe?' in nodes_map:
    workflow['connections']['IF: Usuario Existe?'] = {
        "main": [
            [{"node": "Session Manager Agent", "type": "main", "index": 0}],   # TRUE branch (index 0)
            [{"node": "Onboarding Flow Agent", "type": "main", "index": 0}]    # FALSE branch (index 1)
        ]
    }
    print("   ✓ IF: Usuario Existe? → Session Manager Agent (TRUE)")
    print("   ✓ IF: Usuario Existe? → Onboarding Flow Agent (FALSE)")

# ============================================================================
# MANEJAR SWITCH: Session Type (tiene múltiples outputs)
# ============================================================================
print("\n🔗 Configurando Switch: Session Type (multi-branch)...\n")

if 'Switch: Session Type' in nodes_map:
    switch_outputs = []

    # Case 0: compra → Customer Journey Agent
    if 'Customer Journey Agent' in nodes_map:
        switch_outputs.append([{"node": "Customer Journey Agent", "type": "main", "index": 0}])
        print("   ✓ Switch case 0 (compra) → Customer Journey Agent")
    else:
        switch_outputs.append([])

    # Case 1: menu → Menu Generator Agent
    if 'Menu Generator Agent' in nodes_map:
        switch_outputs.append([{"node": "Menu Generator Agent", "type": "main", "index": 0}])
        print("   ✓ Switch case 1 (menu) → Menu Generator Agent")
    else:
        switch_outputs.append([])

    # Case 2: preferencias → Preference Config Agent
    if 'Preference Config Agent' in nodes_map:
        switch_outputs.append([{"node": "Preference Config Agent", "type": "main", "index": 0}])
        print("   ✓ Switch case 2 (preferencias) → Preference Config Agent")
    else:
        switch_outputs.append([])

    # Case 3: fornecedor → Supplier Journey Agent
    if 'Supplier Journey Agent' in nodes_map:
        switch_outputs.append([{"node": "Supplier Journey Agent", "type": "main", "index": 0}])
        print("   ✓ Switch case 3 (fornecedor) → Supplier Journey Agent")
    else:
        switch_outputs.append([])

    workflow['connections']['Switch: Session Type'] = {
        "main": switch_outputs
    }

# ============================================================================
# GUARDAR
# ============================================================================
print("\n💾 Guardando workflow con backbone completo...\n")
with open('Frepi_MVP2_Agent_Architecture.json', 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("✅ BACKBONE REPARADO!")
print(f"\n📊 ESTADÍSTICAS:")
print(f"   Total nodes: {len(workflow['nodes'])}")
print(f"   Total connections: {len(workflow['connections'])}")

print(f"\n📁 Archivo guardado: Frepi_MVP2_Agent_Architecture.json")
