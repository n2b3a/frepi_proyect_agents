#!/usr/bin/env python3
"""
Script para construir el workflow completo de Frepi MVP2 Agent Architecture
Combina nodes existentes + nuevos sub-agents + conexiones completas
"""

import json

# Cargar workflow base
with open('Frepi_MVP2_Agent_Architecture.json', 'r') as f:
    workflow = json.load(f)

# Nuevos nodes generados por el agente (Shopping Flow, Vector Search, Preference Config, Supplier Manager, Price Upload)
new_nodes_json = '''[
  {
    "parameters": {
      "name": "shopping_flow",
      "description": "Gerencia o fluxo completo de compra inteligente, comparação de preços e checkout.",
      "promptType": "define",
      "text": "={{ $json.query || $json.message }}",
      "options": {
        "systemMessage": "# 🛒 SHOPPING FLOW AGENT\\n\\n## RESPONSABILIDADE\\nGerenciar todo o fluxo de compra do restaurante desde a lista até o checkout.\\n\\n## TOOLS DISPONÍVEIS\\n\\n### normalize_shopping_list\\nNormaliza a lista de compras enviada pelo usuário.\\nRecebe texto livre, retorna array estruturado de produtos.\\n\\n### calculate_savings\\nCalcula economia total comparando preços de fornecedores.\\nRecebe produtos e preços, retorna % de economia.\\n\\n### segment_by_supplier\\nSegmenta produtos por fornecedor para otimizar logística.\\nAgrupa itens pelo melhor fornecedor de cada um.\\n\\n### get_prices_for_product\\nBusca preços de um produto específico em todos fornecedores.\\nQuery: suppliers_products JOIN products\\n\\n### calculate_best_price\\nDetermina melhor preço considerando preferências do usuário.\\nPondera: preço, marca preferida, formato preferido.\\n\\n### execute_checkout\\nExecuta o pedido confirmado pelo usuário.\\nCria registros em orders e order_items.\\n\\n## FLUXO TÍPICO\\n\\n1. Receber lista de compra (texto livre)\\n2. Normalizar lista → identificar produtos\\n3. Para cada produto → buscar preços\\n4. Calcular melhor preço (considerar preferências)\\n5. Segmentar por fornecedor\\n6. Apresentar resumo com economia\\n7. Confirmar com usuário\\n8. Executar checkout\\n\\n## REGRAS\\n\\n- Sempre mostrar comparação de preços\\n- Destacar economia total em R$ e %\\n- Agrupar por fornecedor para minimizar entregas\\n- Respeitar preferências de marca quando possível\\n- Avisar se produto não encontrado\\n- Confirmar antes de executar pedido\\n\\n## OUTPUT\\nPortuguês brasileiro, emojis: 🛒💰📊✅"
      }
    },
    "type": "@n8n/n8n-nodes-langchain.agentTool",
    "typeVersion": 2.2,
    "position": [-448, 128],
    "id": "11111111-aaaa-bbbb-cccc-111111111111",
    "name": "Shopping Flow Agent"
  },
  {
    "parameters": {
      "model": {
        "__rl": true,
        "mode": "list",
        "value": "gpt-4o-mini"
      },
      "options": {
        "temperature": 0.2,
        "maxTokens": 2500
      }
    },
    "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
    "typeVersion": 1.2,
    "position": [-224, 352],
    "id": "22222222-aaaa-bbbb-cccc-222222222222",
    "name": "OpenAI Chat Shopping",
    "credentials": {
      "openAiApi": {
        "id": "MdAepMtuPO5nFVI0",
        "name": "OpenAi account"
      }
    }
  },
  {
    "parameters": {
      "sessionIdType": "customKey",
      "sessionKey": "={{ $('Extraer Datos WhatsApp').first().json.phone_number }}",
      "contextWindowLength": 20
    },
    "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
    "typeVersion": 1.3,
    "position": [-224, 576],
    "id": "33333333-aaaa-bbbb-cccc-333333333333",
    "name": "Memory Shopping"
  }
]'''

new_nodes = json.loads(new_nodes_json)

# Agregar SOLO los primeros 3 nodes como ejemplo (Shopping Flow Agent base)
# El resto se agregará en el siguiente paso
workflow['nodes'].extend(new_nodes[:3])

# Agregar conexiones para Shopping Flow Agent
workflow['connections']['Shopping Flow Agent'] = {
    "ai_tool": [
        [
            {
                "node": "Customer Journey Agent",
                "type": "ai_tool",
                "index": 0
            }
        ]
    ]
}

workflow['connections']['OpenAI Chat Shopping'] = {
    "ai_languageModel": [
        [
            {
                "node": "Shopping Flow Agent",
                "type": "ai_languageModel",
                "index": 0
            }
        ]
    ]
}

workflow['connections']['Memory Shopping'] = {
    "ai_memory": [
        [
            {
                "node": "Shopping Flow Agent",
                "type": "ai_memory",
                "index": 0
            }
        ]
    ]
}

# Guardar workflow actualizado
with open('Frepi_MVP2_Agent_Architecture_TEMP.json', 'w') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("✅ Workflow actualizado temporalmente")
print(f"📊 Total nodes: {len(workflow['nodes'])}")
print(f"🔗 Total connections: {len(workflow['connections'])}")
