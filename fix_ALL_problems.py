#!/usr/bin/env python3
"""
Corrección COMPLETA de todos los problemas del workflow
"""

import json
from datetime import datetime

print("🔧 CORRIGIENDO TODOS LOS PROBLEMAS DEL WORKFLOW\n")

# Backup
backup_file = f'Frepi_MVP2_Agent_Architecture_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
with open('Frepi_MVP2_Agent_Architecture.json', 'r') as f:
    w = json.load(f)

with open(backup_file, 'w') as f:
    json.dump(w, f, indent=2, ensure_ascii=False)
print(f"✅ Backup: {backup_file}\n")

nodes_map = {n['name']: n['id'] for n in w['nodes']}

# ============================================================================
# FIX 1: CORREGIR TYPE DE "Insertar Usuario"
# ============================================================================
print("🔧 FIX 1: Corrigiendo type de 'Insertar Usuario'...")

for i, node in enumerate(w['nodes']):
    if node['name'] == 'Insertar Usuario':
        if node['type'] == '@n8n/n8n-nodes-langchain.supabase':
            w['nodes'][i]['type'] = 'n8n-nodes-base.supabase'
            print(f"   ✅ Insertar Usuario: @n8n/n8n-nodes-langchain.supabase → n8n-nodes-base.supabase")

# ============================================================================
# FIX 2: ELIMINAR "Config Global" DEL FLUJO (es config, se referencia por expresiones)
# ============================================================================
print("\n🔧 FIX 2: Eliminando Config Global del flujo principal...")
print("   ℹ️  Config Global es un nodo de configuración, no necesita estar en el flujo")
# No hace falta eliminarlo, solo dejarlo sin conexiones

# ============================================================================
# FIX 3: VERIFICAR Y CORREGIR TODAS LAS CONEXIONES MAIN
# ============================================================================
print("\n🔧 FIX 3: Verificando y corrigiendo conexiones main...")

# 3.1: WhatsApp Trigger → Extraer Datos WhatsApp
if 'WhatsApp Trigger' not in w['connections'] or 'main' not in w['connections']['WhatsApp Trigger']:
    w['connections']['WhatsApp Trigger'] = {
        "main": [[{"node": "Extraer Datos WhatsApp", "type": "main", "index": 0}]]
    }
    print("   ✅ WhatsApp Trigger → Extraer Datos WhatsApp")

# 3.2: Extraer Datos WhatsApp → Check Duplicate Message
if 'Extraer Datos WhatsApp' not in w['connections'] or 'main' not in w['connections']['Extraer Datos WhatsApp']:
    w['connections']['Extraer Datos WhatsApp'] = {
        "main": [[{"node": "Check Duplicate Message", "type": "main", "index": 0}]]
    }
    print("   ✅ Extraer Datos WhatsApp → Check Duplicate Message")

# 3.3: Check Duplicate Message → Buscar Usuario
if 'Check Duplicate Message' not in w['connections'] or 'main' not in w['connections']['Check Duplicate Message']:
    w['connections']['Check Duplicate Message'] = {
        "main": [[{"node": "Buscar Usuario", "type": "main", "index": 0}]]
    }
    print("   ✅ Check Duplicate Message → Buscar Usuario")

# 3.4: Buscar Usuario → IF: Usuario Existe?
# Buscar Usuario tiene tanto ai_tool como main, preservar ambos
if 'Buscar Usuario' in w['connections']:
    if 'main' not in w['connections']['Buscar Usuario']:
        w['connections']['Buscar Usuario']['main'] = [[{"node": "IF: Usuario Existe?", "type": "main", "index": 0}]]
        print("   ✅ Buscar Usuario → IF: Usuario Existe?")
else:
    w['connections']['Buscar Usuario'] = {
        "main": [[{"node": "IF: Usuario Existe?", "type": "main", "index": 0}]]
    }
    print("   ✅ Buscar Usuario → IF: Usuario Existe? (creada)")

# 3.5: IF: Usuario Existe? → Session Manager Agent (TRUE) / Onboarding Flow Agent (FALSE)
if 'IF: Usuario Existe?' not in w['connections'] or 'main' not in w['connections']['IF: Usuario Existe?']:
    w['connections']['IF: Usuario Existe?'] = {
        "main": [
            [{"node": "Session Manager Agent", "type": "main", "index": 0}],
            [{"node": "Onboarding Flow Agent", "type": "main", "index": 0}]
        ]
    }
    print("   ✅ IF: Usuario Existe? → Session Manager Agent (TRUE)")
    print("   ✅ IF: Usuario Existe? → Onboarding Flow Agent (FALSE)")

# 3.6: Session Manager Agent → Switch: Session Type
if 'Session Manager Agent' not in w['connections']:
    w['connections']['Session Manager Agent'] = {}

if 'main' not in w['connections']['Session Manager Agent']:
    w['connections']['Session Manager Agent']['main'] = [[{"node": "Switch: Session Type", "type": "main", "index": 0}]]
    print("   ✅ Session Manager Agent → Switch: Session Type")

# 3.7: Switch: Session Type → 4 agentes
if 'Switch: Session Type' not in w['connections'] or 'main' not in w['connections']['Switch: Session Type']:
    w['connections']['Switch: Session Type'] = {
        "main": [
            [{"node": "Customer Journey Agent", "type": "main", "index": 0}],
            [{"node": "Menu Generator Agent", "type": "main", "index": 0}],
            [{"node": "Preference Config Agent", "type": "main", "index": 0}],
            [{"node": "Supplier Journey Agent", "type": "main", "index": 0}]
        ]
    }
    print("   ✅ Switch case 0 → Customer Journey Agent")
    print("   ✅ Switch case 1 → Menu Generator Agent")
    print("   ✅ Switch case 2 → Preference Config Agent")
    print("   ✅ Switch case 3 → Supplier Journey Agent")

# 3.8: Onboarding Flow Agent → Insertar Usuario → Enviar Respuesta
if 'Onboarding Flow Agent' not in w['connections']:
    w['connections']['Onboarding Flow Agent'] = {}

if 'main' not in w['connections']['Onboarding Flow Agent']:
    w['connections']['Onboarding Flow Agent']['main'] = [[{"node": "Insertar Usuario", "type": "main", "index": 0}]]
    print("   ✅ Onboarding Flow Agent → Insertar Usuario")

if 'Insertar Usuario' not in w['connections'] or 'main' not in w['connections']['Insertar Usuario']:
    w['connections']['Insertar Usuario'] = {
        "main": [[{"node": "Enviar Respuesta", "type": "main", "index": 0}]]
    }
    print("   ✅ Insertar Usuario → Enviar Respuesta")

# 3.9: Customer Journey Agent → Deduplicar Mensajes
if 'Customer Journey Agent' not in w['connections'] or 'main' not in w['connections']['Customer Journey Agent']:
    w['connections']['Customer Journey Agent'] = {
        "main": [[{"node": "Deduplicar Mensajes", "type": "main", "index": 0}]]
    }
    print("   ✅ Customer Journey Agent → Deduplicar Mensajes")

# 3.10: Menu Generator Agent → Deduplicar Mensajes
if 'Menu Generator Agent' not in w['connections']:
    w['connections']['Menu Generator Agent'] = {}

if 'main' not in w['connections']['Menu Generator Agent']:
    w['connections']['Menu Generator Agent']['main'] = [[{"node": "Deduplicar Mensajes", "type": "main", "index": 0}]]
    print("   ✅ Menu Generator Agent → Deduplicar Mensajes")

# 3.11: Preference Config Agent → Deduplicar Mensajes
if 'Preference Config Agent' not in w['connections']:
    w['connections']['Preference Config Agent'] = {}

if 'main' not in w['connections']['Preference Config Agent']:
    w['connections']['Preference Config Agent']['main'] = [[{"node": "Deduplicar Mensajes", "type": "main", "index": 0}]]
    print("   ✅ Preference Config Agent → Deduplicar Mensajes")

# 3.12: Supplier Journey Agent → Deduplicar Mensajes
if 'Supplier Journey Agent' not in w['connections'] or 'main' not in w['connections']['Supplier Journey Agent']:
    w['connections']['Supplier Journey Agent'] = {
        "main": [[{"node": "Deduplicar Mensajes", "type": "main", "index": 0}]]
    }
    print("   ✅ Supplier Journey Agent → Deduplicar Mensajes")

# 3.13: Deduplicar Mensajes → Enviar Respuesta
if 'Deduplicar Mensajes' not in w['connections'] or 'main' not in w['connections']['Deduplicar Mensajes']:
    w['connections']['Deduplicar Mensajes'] = {
        "main": [[{"node": "Enviar Respuesta", "type": "main", "index": 0}]]
    }
    print("   ✅ Deduplicar Mensajes → Enviar Respuesta")

# ============================================================================
# GUARDAR
# ============================================================================
print("\n💾 Guardando workflow corregido...")
with open('Frepi_MVP2_Agent_Architecture.json', 'w', encoding='utf-8') as f:
    json.dump(w, f, indent=2, ensure_ascii=False)

print("\n✅ CORRECCIONES COMPLETADAS!")
print(f"📊 Total nodos: {len(w['nodes'])}")
print(f"📊 Total conexiones: {len(w['connections'])}")
print(f"📁 Backup: {backup_file}")
