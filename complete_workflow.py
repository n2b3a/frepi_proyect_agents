#!/usr/bin/env python3
"""
Complete Frepi MVP2 Agent Architecture Workflow
Adds remaining 24 nodes to reach ~59 total nodes
"""

import json
import uuid
from pathlib import Path

def generate_uuid():
    """Generate a unique UUID"""
    return str(uuid.uuid4())

def add_missing_nodes_and_connections(workflow):
    """Add all missing nodes and connections to complete the workflow"""

    # ========== 1. ADD execute_checkout TOOL ==========
    execute_checkout_id = "99999999-aaaa-bbbb-cccc-999999999999"
    execute_checkout = {
        "parameters": {
            "description": "Executa o pedido confirmado pelo usuário, criando registros em Supabase.",
            "jsCode": """const input = $input.first().json;
const orderData = input.order_data || {};
const phoneNumber = input.phone_number || input.channel_id;

if (!orderData.items || orderData.items.length === 0) {
  return {
    json: {
      error: true,
      message: "Nenhum item no pedido"
    }
  };
}

const credentials = await this.getCredentials('supabaseApi');
const supabaseUrl = credentials.host;
const supabaseKey = credentials.serviceRole;

try {
  // 1. Buscar user_id
  const user = await $request({
    method: 'GET',
    url: `${supabaseUrl}/rest/v1/restaurant_people`,
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json'
    },
    qs: {
      'whatsapp_number': `eq.${phoneNumber}`,
      'select': 'id'
    },
    json: true
  });

  if (!user || user.length === 0) {
    return {
      json: {
        error: true,
        message: "Usuário não encontrado"
      }
    };
  }

  const userId = user[0].id;

  // 2. Criar pedido
  const orderResponse = await $request({
    method: 'POST',
    url: `${supabaseUrl}/rest/v1/orders`,
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json',
      'Prefer': 'return=representation'
    },
    body: {
      restaurant_person_id: userId,
      total_value: orderData.total_value || 0,
      status: 'pending',
      created_at: new Date().toISOString()
    },
    json: true
  });

  const orderId = orderResponse[0].id;

  // 3. Criar items do pedido
  const orderItems = orderData.items.map(item => ({
    order_id: orderId,
    supplier_product_id: item.supplier_product_id,
    quantity: item.quantity,
    unit_price: item.price,
    subtotal: item.quantity * item.price
  }));

  await $request({
    method: 'POST',
    url: `${supabaseUrl}/rest/v1/order_items`,
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json'
    },
    body: orderItems,
    json: true
  });

  return {
    json: {
      success: true,
      order_id: orderId,
      items_count: orderItems.length,
      total_value: orderData.total_value,
      message: `✅ Pedido #${orderId} criado com sucesso!`
    }
  };
} catch (error) {
  return {
    json: {
      error: true,
      message: `Erro ao executar checkout: ${error.message}`
    }
  };
}"""
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [0, 2592],
        "id": execute_checkout_id,
        "name": "execute_checkout"
    }

    # ========== 2. VECTOR SEARCH AGENT + COMPONENTS ==========

    # Vector Search Agent
    vector_search_agent_id = "aaaaaaaa-1111-2222-3333-444444444444"
    vector_search_agent = {
        "parameters": {
            "name": "vector_search",
            "description": "Busca semântica inteligente de produtos no catálogo usando similaridade.",
            "promptType": "define",
            "text": "={{ $json.query || $json.message }}",
            "options": {
                "systemMessage": """# 🔍 VECTOR SEARCH AGENT

## RESPONSABILIDADE
Realizar buscas semânticas inteligentes no catálogo de produtos.
Encontrar produtos mesmo com descrições vagas ou imprecisas.

## TOOLS DISPONÍVEIS

### search_product_catalog
Busca produtos no catálogo por texto.
Retorna matches ordenados por relevância.

### find_similar_products
Encontra produtos similares a um produto específico.
Útil para sugerir alternativas.

### validate_product_match
Valida se produto mencionado corresponde a produto no catálogo.
Retorna confidence score.

## LÓGICA

1. Receber query do usuário (ex: "arroz tio joão 5kg")
2. Buscar em catálogo
3. Se múltiplos matches → retornar lista com scores
4. Se nenhum match → buscar similares
5. Validar match final

## CASOS DE USO

- Usuário digita "oleo de soja" → buscar todas marcas/formatos
- Usuário menciona "feijão preto" → identificar produto específico
- Produto não encontrado → sugerir alternativas

## OUTPUT
Retorna JSON:
{
  "products_found": int,
  "matches": [
    {
      "product_id": "uuid",
      "product_name": "string",
      "brand": "string",
      "format": "string",
      "confidence_score": float
    }
  ],
  "suggestions": []
}"""
            }
        },
        "type": "@n8n/n8n-nodes-langchain.agentTool",
        "typeVersion": 2.2,
        "position": [-1120, 1472],
        "id": vector_search_agent_id,
        "name": "Vector Search Agent"
    }

    # OpenAI for Vector Search
    openai_vector_id = "bbbbbbbb-1111-2222-3333-555555555555"
    openai_vector = {
        "parameters": {
            "model": {
                "__rl": True,
                "mode": "list",
                "value": "gpt-4o-mini"
            },
            "options": {
                "temperature": 0.1
            }
        },
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "typeVersion": 1.2,
        "position": [-896, 1696],
        "id": openai_vector_id,
        "name": "OpenAI Chat Vector",
        "credentials": {
            "openAiApi": {
                "id": "MdAepMtuPO5nFVI0",
                "name": "OpenAi account"
            }
        }
    }

    # Memory for Vector Search
    memory_vector_id = "cccccccc-1111-2222-3333-666666666666"
    memory_vector = {
        "parameters": {
            "sessionIdType": "customKey",
            "sessionKey": "={{ $('Extraer Datos WhatsApp').first().json.phone_number }}",
            "contextWindowLength": 10
        },
        "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
        "typeVersion": 1.3,
        "position": [-896, 1920],
        "id": memory_vector_id,
        "name": "Memory Vector"
    }

    # Tool: search_product_catalog
    search_catalog_id = "dddddddd-1111-2222-3333-777777777777"
    search_catalog = {
        "parameters": {
            "description": "Busca produtos no catálogo por nome, marca ou descrição.",
            "jsCode": """const input = $input.first().json;
const searchQuery = input.query || input.search || input.product_name;

if (!searchQuery) {
  return {
    json: {
      error: true,
      message: "Query de busca não fornecida"
    }
  };
}

const credentials = await this.getCredentials('supabaseApi');
const supabaseUrl = credentials.host;
const supabaseKey = credentials.serviceRole;

try {
  const response = await $request({
    method: 'GET',
    url: `${supabaseUrl}/rest/v1/products`,
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json'
    },
    qs: {
      'or': `(name.ilike.%${searchQuery}%,brand.ilike.%${searchQuery}%,category.ilike.%${searchQuery}%)`,
      'select': 'id,name,brand,format,category,unit',
      'limit': '20'
    },
    json: true
  });

  const matches = response.map((product, index) => {
    const nameMatch = product.name.toLowerCase().includes(searchQuery.toLowerCase());
    const brandMatch = product.brand?.toLowerCase().includes(searchQuery.toLowerCase());
    const categoryMatch = product.category?.toLowerCase().includes(searchQuery.toLowerCase());

    let score = 0;
    if (nameMatch) score += 60;
    if (brandMatch) score += 30;
    if (categoryMatch) score += 10;

    return {
      product_id: product.id,
      product_name: product.name,
      brand: product.brand || 'N/A',
      format: product.format || 'N/A',
      category: product.category || 'N/A',
      unit: product.unit || 'un',
      confidence_score: score
    };
  }).sort((a, b) => b.confidence_score - a.confidence_score);

  return {
    json: {
      success: true,
      query: searchQuery,
      products_found: matches.length,
      matches: matches
    }
  };
} catch (error) {
  return {
    json: {
      error: true,
      message: `Erro ao buscar produtos: ${error.message}`
    }
  };
}"""
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [-672, 1472],
        "id": search_catalog_id,
        "name": "search_product_catalog"
    }

    # Tool: find_similar_products
    find_similar_id = "eeeeeeee-1111-2222-3333-888888888888"
    find_similar = {
        "parameters": {
            "description": "Encontra produtos similares baseado em categoria e características.",
            "jsCode": """const input = $input.first().json;
const productId = input.product_id;
const category = input.category;

const credentials = await this.getCredentials('supabaseApi');
const supabaseUrl = credentials.host;
const supabaseKey = credentials.serviceRole;

try {
  let qs = {
    'select': 'id,name,brand,format,category,unit',
    'limit': '10'
  };

  if (productId) {
    qs['id'] = `neq.${productId}`;
  }

  if (category) {
    qs['category'] = `eq.${category}`;
  }

  const response = await $request({
    method: 'GET',
    url: `${supabaseUrl}/rest/v1/products`,
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json'
    },
    qs: qs,
    json: true
  });

  const similar = response.map(product => ({
    product_id: product.id,
    product_name: product.name,
    brand: product.brand || 'N/A',
    format: product.format || 'N/A',
    category: product.category || 'N/A'
  }));

  return {
    json: {
      success: true,
      similar_found: similar.length,
      similar_products: similar
    }
  };
} catch (error) {
  return {
    json: {
      error: true,
      message: `Erro ao buscar similares: ${error.message}`
    }
  };
}"""
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [-672, 1696],
        "id": find_similar_id,
        "name": "find_similar_products"
    }

    # Tool: validate_product_match
    validate_match_id = "ffffffff-1111-2222-3333-999999999999"
    validate_match = {
        "parameters": {
            "description": "Valida correspondência entre texto do usuário e produto do catálogo.",
            "jsCode": """const input = $input.first().json;
const userText = (input.user_text || '').toLowerCase();
const productName = (input.product_name || '').toLowerCase();
const productBrand = (input.product_brand || '').toLowerCase();

if (!userText || !productName) {
  return {
    json: {
      error: true,
      message: "Dados insuficientes para validação"
    }
  };
}

// Calcular score de similaridade
let score = 0;

// Palavras em comum
const userWords = userText.split(/\\s+/);
const productWords = productName.split(/\\s+/);

const commonWords = userWords.filter(word =>
  productWords.some(pWord => pWord.includes(word) || word.includes(pWord))
);

score += (commonWords.length / userWords.length) * 70;

// Match de marca
if (productBrand && userText.includes(productBrand)) {
  score += 30;
}

// Match exato
if (userText === productName) {
  score = 100;
}

const confidence = Math.min(Math.round(score), 100);

return {
  json: {
    is_valid_match: confidence >= 60,
    confidence_score: confidence,
    confidence_level: confidence >= 80 ? 'high' : confidence >= 60 ? 'medium' : 'low',
    matched_words: commonWords
  }
};"""
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [-672, 1920],
        "id": validate_match_id,
        "name": "validate_product_match"
    }

    # ========== 3. PREFERENCE CONFIG AGENT + COMPONENTS ==========

    # Preference Config Agent
    preference_agent_id = "aaaabbbb-2222-3333-4444-555555555555"
    preference_agent = {
        "parameters": {
            "name": "preference_config",
            "description": "Configura preferências de compra do restaurante (marcas, formatos, frequências).",
            "promptType": "define",
            "text": "={{ $json.query || $json.message }}",
            "options": {
                "systemMessage": """# ⚙️ PREFERENCE CONFIG AGENT

## RESPONSABILIDADE
Gerenciar configuração de preferências de compra do restaurante.

## TOOLS DISPONÍVEIS

### save_user_preferences
Salva preferências gerais do usuário.
Campos: preferred_brands, preferred_formats, special_restrictions.

### update_delivery_preferences
Atualiza preferências de entrega.
Campos: order_frequency, delivery_schedule, preferred_suppliers.

## FLUXO DE CONFIGURAÇÃO

1. Perguntar campo por campo (não todos de uma vez)
2. Validar entrada do usuário
3. Salvar incrementalmente
4. Mostrar progresso (% completude)
5. Confirmar salvamento

## CAMPOS DE PREFERÊNCIA

### preferred_brands (array)
"Quais marcas você costuma comprar?"
Exemplos: Tio João, Sadia, Aurora

### preferred_formats (array)
"Quais formatos/tamanhos prefere?"
Exemplos: 5kg, caixa com 12 unidades, fardo

### order_frequency (string)
"Com que frequência faz pedidos?"
Opções: diário, semanal, quinzenal, mensal

### delivery_schedule (string)
"Qual melhor horário para entregas?"
Exemplos: manhã (8h-12h), tarde (13h-17h)

### special_restrictions (text)
"Alguma restrição especial?"
Exemplos: sem glúten, orgânicos, fornecedor local

## REGRAS

- UMA pergunta por vez
- Aceitar respostas em formato livre
- Normalizar antes de salvar
- Permitir pular campos (opcional)
- Calcular completude após cada salvamento

## OUTPUT
Português brasileiro, tom conversacional, emojis: ⚙️✅📋⭐"""
            }
        },
        "type": "@n8n/n8n-nodes-langchain.agentTool",
        "typeVersion": 2.2,
        "position": [-1120, 2144],
        "id": preference_agent_id,
        "name": "Preference Config Agent"
    }

    # OpenAI for Preference
    openai_preference_id = "bbbbcccc-2222-3333-4444-666666666666"
    openai_preference = {
        "parameters": {
            "model": {
                "__rl": True,
                "mode": "list",
                "value": "gpt-4o-mini"
            },
            "options": {
                "temperature": 0.2
            }
        },
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "typeVersion": 1.2,
        "position": [-896, 2368],
        "id": openai_preference_id,
        "name": "OpenAI Chat Preference",
        "credentials": {
            "openAiApi": {
                "id": "MdAepMtuPO5nFVI0",
                "name": "OpenAi account"
            }
        }
    }

    # Memory for Preference
    memory_preference_id = "ccccdddd-2222-3333-4444-777777777777"
    memory_preference = {
        "parameters": {
            "sessionIdType": "customKey",
            "sessionKey": "={{ $('Extraer Datos WhatsApp').first().json.phone_number }}",
            "contextWindowLength": 15
        },
        "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
        "typeVersion": 1.3,
        "position": [-896, 2592],
        "id": memory_preference_id,
        "name": "Memory Preference"
    }

    # Tool: save_user_preferences
    save_preferences_id = "ddddeeee-2222-3333-4444-888888888888"
    save_preferences = {
        "parameters": {
            "description": "Salva ou atualiza preferências gerais do usuário em Supabase.",
            "jsCode": """const input = $input.first().json;
const phoneNumber = input.phone_number || input.channel_id;
const preferences = input.preferences || {};

if (!phoneNumber) {
  return {
    json: {
      error: true,
      message: "Phone number não fornecido"
    }
  };
}

const credentials = await this.getCredentials('supabaseApi');
const supabaseUrl = credentials.host;
const supabaseKey = credentials.serviceRole;

try {
  // Buscar usuário
  const user = await $request({
    method: 'GET',
    url: `${supabaseUrl}/rest/v1/restaurant_people`,
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json'
    },
    qs: {
      'whatsapp_number': `eq.${phoneNumber}`,
      'select': 'id'
    },
    json: true
  });

  if (!user || user.length === 0) {
    return {
      json: {
        error: true,
        message: "Usuário não encontrado"
      }
    };
  }

  const userId = user[0].id;

  // Atualizar preferências
  const updateData = {};

  if (preferences.preferred_brands) {
    updateData.preferred_brands = Array.isArray(preferences.preferred_brands)
      ? preferences.preferred_brands
      : preferences.preferred_brands.split(',').map(b => b.trim());
  }

  if (preferences.preferred_formats) {
    updateData.preferred_formats = Array.isArray(preferences.preferred_formats)
      ? preferences.preferred_formats
      : preferences.preferred_formats.split(',').map(f => f.trim());
  }

  if (preferences.special_restrictions) {
    updateData.special_restrictions = preferences.special_restrictions;
  }

  await $request({
    method: 'PATCH',
    url: `${supabaseUrl}/rest/v1/restaurant_people`,
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json'
    },
    qs: {
      'id': `eq.${userId}`
    },
    body: updateData,
    json: true
  });

  return {
    json: {
      success: true,
      user_id: userId,
      updated_fields: Object.keys(updateData),
      message: "✅ Preferências salvas com sucesso!"
    }
  };
} catch (error) {
  return {
    json: {
      error: true,
      message: `Erro ao salvar preferências: ${error.message}`
    }
  };
}"""
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [-672, 2144],
        "id": save_preferences_id,
        "name": "save_user_preferences"
    }

    # Tool: update_delivery_preferences
    update_delivery_id = "eeeefffff-2222-3333-4444-999999999999"
    update_delivery = {
        "parameters": {
            "description": "Atualiza preferências de entrega e frequência de pedidos.",
            "jsCode": """const input = $input.first().json;
const phoneNumber = input.phone_number || input.channel_id;
const deliveryPrefs = input.delivery_preferences || {};

const credentials = await this.getCredentials('supabaseApi');
const supabaseUrl = credentials.host;
const supabaseKey = credentials.serviceRole;

try {
  const user = await $request({
    method: 'GET',
    url: `${supabaseUrl}/rest/v1/restaurant_people`,
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json'
    },
    qs: {
      'whatsapp_number': `eq.${phoneNumber}`,
      'select': 'id'
    },
    json: true
  });

  if (!user || user.length === 0) {
    return {
      json: {
        error: true,
        message: "Usuário não encontrado"
      }
    };
  }

  const userId = user[0].id;

  const updateData = {};

  if (deliveryPrefs.order_frequency) {
    const validFrequencies = ['diário', 'semanal', 'quinzenal', 'mensal'];
    const frequency = deliveryPrefs.order_frequency.toLowerCase();
    if (validFrequencies.some(f => frequency.includes(f))) {
      updateData.order_frequency = frequency;
    }
  }

  if (deliveryPrefs.delivery_schedule) {
    updateData.delivery_schedule = deliveryPrefs.delivery_schedule;
  }

  if (deliveryPrefs.preferred_suppliers) {
    updateData.preferred_suppliers = Array.isArray(deliveryPrefs.preferred_suppliers)
      ? deliveryPrefs.preferred_suppliers
      : deliveryPrefs.preferred_suppliers.split(',').map(s => s.trim());
  }

  await $request({
    method: 'PATCH',
    url: `${supabaseUrl}/rest/v1/restaurant_people`,
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json'
    },
    qs: {
      'id': `eq.${userId}`
    },
    body: updateData,
    json: true
  });

  return {
    json: {
      success: true,
      updated_fields: Object.keys(updateData),
      message: "✅ Preferências de entrega atualizadas!"
    }
  };
} catch (error) {
  return {
    json: {
      error: true,
      message: `Erro ao atualizar: ${error.message}`
    }
  };
}"""
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [-672, 2368],
        "id": update_delivery_id,
        "name": "update_delivery_preferences"
    }

    # ========== 4. SUPPLIER MANAGER AGENT + COMPONENTS ==========

    # Supplier Manager Agent
    supplier_manager_id = "aaaa1111-3333-4444-5555-666666666666"
    supplier_manager = {
        "parameters": {
            "name": "supplier_manager",
            "description": "Gerencia cadastro e atualização de dados de fornecedores.",
            "promptType": "define",
            "text": "={{ $json.query || $json.message }}",
            "options": {
                "systemMessage": """# 📦 SUPPLIER MANAGER AGENT

## RESPONSABILIDADE
Gerenciar cadastro de fornecedores no sistema.

## TOOLS DISPONÍVEIS

### register_supplier
Registra novo fornecedor no Supabase.
Campos obrigatórios: name, cnpj, contact_phone, city.

### update_supplier_data
Atualiza dados de fornecedor existente.

## FLUXO DE REGISTRO

1. Cumprimentar fornecedor
2. Coletar dados essenciais:
   - Nome da empresa
   - CNPJ (validar formato)
   - Telefone de contato
   - Cidade
   - Categorias de produtos que fornece
3. Validar dados
4. Salvar no Supabase
5. Confirmar registro
6. Oferecer próximo passo (upload de preços)

## VALIDAÇÕES

### CNPJ
- Formato: XX.XXX.XXX/XXXX-XX
- 14 dígitos numéricos
- Se inválido → pedir reenvio

### Telefone
- Formato: (XX) XXXXX-XXXX
- Aceitar com ou sem formatação

### Categorias
- hortifruti, carnes, grãos, laticínios, bebidas, limpeza
- Aceitar múltiplas categorias

## FLUXO DE ATUALIZAÇÃO

1. Identificar fornecedor (por CNPJ ou nome)
2. Perguntar o que deseja atualizar
3. Coletar novo valor
4. Confirmar atualização

## REGRAS

- Sempre validar CNPJ único (não duplicar)
- Confirmar dados antes de salvar
- Tom profissional mas amigável
- Explicar próximos passos claramente

## OUTPUT
Português brasileiro, emojis: 📦✅📝📋"""
            }
        },
        "type": "@n8n/n8n-nodes-langchain.agentTool",
        "typeVersion": 2.2,
        "position": [-448, 2144],
        "id": supplier_manager_id,
        "name": "Supplier Manager Agent"
    }

    # OpenAI for Supplier Manager
    openai_supplier_mgr_id = "bbbb1111-3333-4444-5555-777777777777"
    openai_supplier_mgr = {
        "parameters": {
            "model": {
                "__rl": True,
                "mode": "list",
                "value": "gpt-4o-mini"
            },
            "options": {
                "temperature": 0.2
            }
        },
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "typeVersion": 1.2,
        "position": [-224, 2368],
        "id": openai_supplier_mgr_id,
        "name": "OpenAI Chat SupplierMgr",
        "credentials": {
            "openAiApi": {
                "id": "MdAepMtuPO5nFVI0",
                "name": "OpenAi account"
            }
        }
    }

    # Memory for Supplier Manager
    memory_supplier_mgr_id = "cccc1111-3333-4444-5555-888888888888"
    memory_supplier_mgr = {
        "parameters": {
            "sessionIdType": "customKey",
            "sessionKey": "={{ $('Extraer Datos WhatsApp').first().json.phone_number }}",
            "contextWindowLength": 15
        },
        "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
        "typeVersion": 1.3,
        "position": [-224, 2592],
        "id": memory_supplier_mgr_id,
        "name": "Memory SupplierMgr"
    }

    # Tool: register_supplier
    register_supplier_id = "dddd1111-3333-4444-5555-999999999999"
    register_supplier = {
        "parameters": {
            "description": "Registra novo fornecedor no sistema Supabase.",
            "jsCode": """const input = $input.first().json;
const supplierData = input.supplier_data || {};

// Validações
const required = ['name', 'cnpj', 'contact_phone', 'city'];
for (const field of required) {
  if (!supplierData[field]) {
    return {
      json: {
        error: true,
        message: `Campo obrigatório faltando: ${field}`
      }
    };
  }
}

// Validar CNPJ (remover formatação)
const cnpj = supplierData.cnpj.replace(/[^\\d]/g, '');
if (cnpj.length !== 14) {
  return {
    json: {
      error: true,
      message: "CNPJ inválido. Deve ter 14 dígitos."
    }
  };
}

const credentials = await this.getCredentials('supabaseApi');
const supabaseUrl = credentials.host;
const supabaseKey = credentials.serviceRole;

try {
  // Verificar se CNPJ já existe
  const existing = await $request({
    method: 'GET',
    url: `${supabaseUrl}/rest/v1/suppliers`,
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json'
    },
    qs: {
      'cnpj': `eq.${cnpj}`
    },
    json: true
  });

  if (existing && existing.length > 0) {
    return {
      json: {
        error: true,
        message: "CNPJ já cadastrado no sistema."
      }
    };
  }

  // Criar fornecedor
  const response = await $request({
    method: 'POST',
    url: `${supabaseUrl}/rest/v1/suppliers`,
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json',
      'Prefer': 'return=representation'
    },
    body: {
      name: supplierData.name,
      cnpj: cnpj,
      contact_phone: supplierData.contact_phone,
      city: supplierData.city,
      categories: supplierData.categories || [],
      created_at: new Date().toISOString()
    },
    json: true
  });

  const supplier = response[0];

  return {
    json: {
      success: true,
      supplier_id: supplier.id,
      supplier_name: supplier.name,
      message: `✅ Fornecedor ${supplier.name} cadastrado com sucesso!`
    }
  };
} catch (error) {
  return {
    json: {
      error: true,
      message: `Erro ao registrar fornecedor: ${error.message}`
    }
  };
}"""
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [0, 2144],
        "id": register_supplier_id,
        "name": "register_supplier"
    }

    # Tool: update_supplier_data
    update_supplier_id = "eeee1111-3333-4444-5555-000000000000"
    update_supplier = {
        "parameters": {
            "description": "Atualiza dados de fornecedor existente no Supabase.",
            "jsCode": """const input = $input.first().json;
const supplierId = input.supplier_id;
const cnpj = input.cnpj;
const updateData = input.update_data || {};

if (!supplierId && !cnpj) {
  return {
    json: {
      error: true,
      message: "Necessário fornecer supplier_id ou cnpj"
    }
  };
}

const credentials = await this.getCredentials('supabaseApi');
const supabaseUrl = credentials.host;
const supabaseKey = credentials.serviceRole;

try {
  let filterKey = 'id';
  let filterValue = supplierId;

  if (!supplierId && cnpj) {
    filterKey = 'cnpj';
    filterValue = cnpj.replace(/[^\\d]/g, '');
  }

  const allowedFields = ['name', 'contact_phone', 'city', 'categories', 'address'];
  const cleanUpdate = {};

  for (const field of allowedFields) {
    if (updateData[field] !== undefined) {
      cleanUpdate[field] = updateData[field];
    }
  }

  if (Object.keys(cleanUpdate).length === 0) {
    return {
      json: {
        error: true,
        message: "Nenhum campo válido para atualizar"
      }
    };
  }

  await $request({
    method: 'PATCH',
    url: `${supabaseUrl}/rest/v1/suppliers`,
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json'
    },
    qs: {
      [filterKey]: `eq.${filterValue}`
    },
    body: cleanUpdate,
    json: true
  });

  return {
    json: {
      success: true,
      updated_fields: Object.keys(cleanUpdate),
      message: "✅ Dados do fornecedor atualizados!"
    }
  };
} catch (error) {
  return {
    json: {
      error: true,
      message: `Erro ao atualizar: ${error.message}`
    }
  };
}"""
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [0, 2368],
        "id": update_supplier_id,
        "name": "update_supplier_data"
    }

    # ========== 5. PRICE UPLOAD AGENT + COMPONENTS ==========

    # Price Upload Agent
    price_upload_agent_id = "aaaa2222-4444-5555-6666-777777777777"
    price_upload_agent = {
        "parameters": {
            "name": "price_upload",
            "description": "Gerencia upload e processamento de listas de preços de fornecedores.",
            "promptType": "define",
            "text": "={{ $json.query || $json.message }}",
            "options": {
                "systemMessage": """# 💰 PRICE UPLOAD AGENT

## RESPONSABILIDADE
Processar listas de preços enviadas por fornecedores.

## TOOLS DISPONÍVEIS

### parse_price_list
Interpreta lista de preços em texto livre.
Extrai: produto, marca, formato, preço.

### bulk_update_prices
Atualiza preços em massa no Supabase.
Cria produtos se não existirem.

## FORMATOS ACEITOS

### Formato Simples
Arroz Tio João 5kg - R$ 28,90
Feijão Camil 1kg - 8,50
Óleo Liza 900ml - R$ 7.80

### Formato Tabular
Produto | Marca | Formato | Preço
Arroz | Tio João | 5kg | 28.90
Feijão | Camil | 1kg | 8.50

### Formato CSV
produto,marca,formato,preco
Arroz,Tio João,5kg,28.90
Feijão,Camil,1kg,8.50

## FLUXO DE PROCESSAMENTO

1. Receber lista (texto)
2. Parsear e estruturar
3. Validar produtos (existem no catálogo?)
4. Para novos produtos → adicionar ao catálogo
5. Atualizar preços em suppliers_products
6. Retornar resumo: X produtos atualizados, Y novos

## VALIDAÇÕES

- Preço deve ser numérico positivo
- Formato deve ser válido
- Se produto não existe → criar em products primeiro
- Associar ao supplier_id correto

## MANEJO DE ERROS

- Linha mal formatada → avisar e pular
- Produto duplicado → atualizar preço
- Preço inválido → pedir correção

## OUTPUT
Retorna resumo:
{
  "total_processed": int,
  "updated": int,
  "created": int,
  "errors": [],
  "summary": "string formatado"
}"""
            }
        },
        "type": "@n8n/n8n-nodes-langchain.agentTool",
        "typeVersion": 2.2,
        "position": [-448, 2816],
        "id": price_upload_agent_id,
        "name": "Price Upload Agent"
    }

    # OpenAI for Price Upload
    openai_price_id = "bbbb2222-4444-5555-6666-888888888888"
    openai_price = {
        "parameters": {
            "model": {
                "__rl": True,
                "mode": "list",
                "value": "gpt-4o-mini"
            },
            "options": {
                "temperature": 0.1
            }
        },
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "typeVersion": 1.2,
        "position": [-224, 3040],
        "id": openai_price_id,
        "name": "OpenAI Chat Price",
        "credentials": {
            "openAiApi": {
                "id": "MdAepMtuPO5nFVI0",
                "name": "OpenAi account"
            }
        }
    }

    # Memory for Price Upload
    memory_price_id = "cccc2222-4444-5555-6666-999999999999"
    memory_price = {
        "parameters": {
            "sessionIdType": "customKey",
            "sessionKey": "={{ $('Extraer Datos WhatsApp').first().json.phone_number }}",
            "contextWindowLength": 20
        },
        "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
        "typeVersion": 1.3,
        "position": [-224, 3264],
        "id": memory_price_id,
        "name": "Memory Price"
    }

    # Tool: parse_price_list
    parse_price_list_id = "dddd2222-4444-5555-6666-000000000000"
    parse_price_list = {
        "parameters": {
            "description": "Interpreta e estrutura lista de preços em texto livre.",
            "jsCode": """const input = $input.first().json;
const priceListText = input.price_list || input.text || input.message;

if (!priceListText) {
  return {
    json: {
      error: true,
      message: "Lista de preços não fornecida"
    }
  };
}

const lines = priceListText.split('\\n').filter(line => line.trim());
const items = [];
const errors = [];

for (let i = 0; i < lines.length; i++) {
  const line = lines[i].trim();

  // Ignorar cabeçalhos
  if (line.toLowerCase().includes('produto') && line.toLowerCase().includes('preço')) {
    continue;
  }

  // Padrão: Produto Marca Formato - R$ Preço
  const pattern1 = /^(.+?)\\s+[-–]\\s*R?\\$?\\s*([\\d.,]+)$/i;
  const match1 = line.match(pattern1);

  if (match1) {
    const productPart = match1[1].trim();
    const price = parseFloat(match1[2].replace(',', '.'));

    // Tentar separar produto, marca, formato
    const parts = productPart.split(/\\s+/);
    let product = '';
    let brand = '';
    let format = '';

    if (parts.length >= 3) {
      product = parts.slice(0, -2).join(' ');
      brand = parts[parts.length - 2];
      format = parts[parts.length - 1];
    } else if (parts.length === 2) {
      product = parts[0];
      brand = parts[1];
    } else {
      product = productPart;
    }

    items.push({
      product_name: product,
      brand: brand || 'N/A',
      format: format || 'un',
      price: price,
      original_line: line
    });
    continue;
  }

  // Padrão CSV/Tabular: produto,marca,formato,preço ou separado por |
  const pattern2 = /^(.+?)[,|](.+?)[,|](.+?)[,|]\\s*R?\\$?\\s*([\\d.,]+)$/i;
  const match2 = line.match(pattern2);

  if (match2) {
    items.push({
      product_name: match2[1].trim(),
      brand: match2[2].trim(),
      format: match2[3].trim(),
      price: parseFloat(match2[4].replace(',', '.')),
      original_line: line
    });
    continue;
  }

  // Linha não reconhecida
  errors.push({
    line_number: i + 1,
    line: line,
    error: "Formato não reconhecido"
  });
}

return {
  json: {
    success: true,
    items_parsed: items.length,
    items: items,
    errors: errors,
    errors_count: errors.length
  }
};"""
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [0, 2816],
        "id": parse_price_list_id,
        "name": "parse_price_list"
    }

    # Tool: bulk_update_prices
    bulk_update_prices_id = "eeee2222-4444-5555-6666-111111111111"
    bulk_update_prices = {
        "parameters": {
            "description": "Atualiza preços em massa no Supabase, criando produtos se necessário.",
            "jsCode": """const input = $input.first().json;
const items = input.items || [];
const supplierId = input.supplier_id;
const phoneNumber = input.phone_number || input.channel_id;

if (!items || items.length === 0) {
  return {
    json: {
      error: true,
      message: "Nenhum item para processar"
    }
  };
}

const credentials = await this.getCredentials('supabaseApi');
const supabaseUrl = credentials.host;
const supabaseKey = credentials.serviceRole;

try {
  // Se não tiver supplier_id, buscar por phone
  let finalSupplierId = supplierId;

  if (!finalSupplierId && phoneNumber) {
    const supplier = await $request({
      method: 'GET',
      url: `${supabaseUrl}/rest/v1/suppliers`,
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json'
      },
      qs: {
        'contact_phone': `ilike.%${phoneNumber}%`,
        'select': 'id'
      },
      json: true
    });

    if (supplier && supplier.length > 0) {
      finalSupplierId = supplier[0].id;
    }
  }

  if (!finalSupplierId) {
    return {
      json: {
        error: true,
        message: "Fornecedor não identificado"
      }
    };
  }

  let updated = 0;
  let created = 0;
  const errors = [];

  for (const item of items) {
    try {
      // Buscar ou criar produto
      let product = await $request({
        method: 'GET',
        url: `${supabaseUrl}/rest/v1/products`,
        headers: {
          'apikey': supabaseKey,
          'Authorization': `Bearer ${supabaseKey}`,
          'Content-Type': 'application/json'
        },
        qs: {
          'name': `ilike.${item.product_name}`,
          'brand': `ilike.${item.brand}`,
          'select': 'id'
        },
        json: true
      });

      let productId;

      if (!product || product.length === 0) {
        // Criar produto
        const newProduct = await $request({
          method: 'POST',
          url: `${supabaseUrl}/rest/v1/products`,
          headers: {
            'apikey': supabaseKey,
            'Authorization': `Bearer ${supabaseKey}`,
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
          },
          body: {
            name: item.product_name,
            brand: item.brand,
            format: item.format,
            unit: 'un'
          },
          json: true
        });
        productId = newProduct[0].id;
        created++;
      } else {
        productId = product[0].id;
      }

      // Atualizar ou criar preço em suppliers_products
      const existing = await $request({
        method: 'GET',
        url: `${supabaseUrl}/rest/v1/suppliers_products`,
        headers: {
          'apikey': supabaseKey,
          'Authorization': `Bearer ${supabaseKey}`,
          'Content-Type': 'application/json'
        },
        qs: {
          'supplier_id': `eq.${finalSupplierId}`,
          'product_id': `eq.${productId}`
        },
        json: true
      });

      if (existing && existing.length > 0) {
        // Atualizar preço
        await $request({
          method: 'PATCH',
          url: `${supabaseUrl}/rest/v1/suppliers_products`,
          headers: {
            'apikey': supabaseKey,
            'Authorization': `Bearer ${supabaseKey}`,
            'Content-Type': 'application/json'
          },
          qs: {
            'supplier_id': `eq.${finalSupplierId}`,
            'product_id': `eq.${productId}`
          },
          body: {
            price: item.price,
            updated_at: new Date().toISOString()
          },
          json: true
        });
        updated++;
      } else {
        // Criar relação
        await $request({
          method: 'POST',
          url: `${supabaseUrl}/rest/v1/suppliers_products`,
          headers: {
            'apikey': supabaseKey,
            'Authorization': `Bearer ${supabaseKey}`,
            'Content-Type': 'application/json'
          },
          body: {
            supplier_id: finalSupplierId,
            product_id: productId,
            price: item.price,
            created_at: new Date().toISOString()
          },
          json: true
        });
        created++;
      }
    } catch (itemError) {
      errors.push({
        item: item.product_name,
        error: itemError.message
      });
    }
  }

  return {
    json: {
      success: true,
      total_processed: items.length,
      updated: updated,
      created: created,
      errors: errors,
      summary: `✅ Processado: ${items.length} itens\\n📊 Atualizados: ${updated}\\n➕ Novos: ${created}\\n❌ Erros: ${errors.length}`
    }
  };
} catch (error) {
  return {
    json: {
      error: true,
      message: `Erro no processamento: ${error.message}`
    }
  };
}"""
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [0, 3040],
        "id": bulk_update_prices_id,
        "name": "bulk_update_prices"
    }

    # ========== ADD ALL NEW NODES TO WORKFLOW ==========

    new_nodes = [
        execute_checkout,
        vector_search_agent, openai_vector, memory_vector,
        search_catalog, find_similar, validate_match,
        preference_agent, openai_preference, memory_preference,
        save_preferences, update_delivery,
        supplier_manager, openai_supplier_mgr, memory_supplier_mgr,
        register_supplier, update_supplier,
        price_upload_agent, openai_price, memory_price,
        parse_price_list, bulk_update_prices
    ]

    workflow["nodes"].extend(new_nodes)

    # ========== ADD ALL CONNECTIONS ==========

    # execute_checkout → Shopping Flow Agent
    workflow["connections"]["execute_checkout"] = {
        "ai_tool": [[{
            "node": "Shopping Flow Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    # Vector Search Agent connections
    workflow["connections"]["Vector Search Agent"] = {
        "ai_tool": [[{
            "node": "Customer Journey Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    workflow["connections"]["OpenAI Chat Vector"] = {
        "ai_languageModel": [[{
            "node": "Vector Search Agent",
            "type": "ai_languageModel",
            "index": 0
        }]]
    }

    workflow["connections"]["Memory Vector"] = {
        "ai_memory": [[{
            "node": "Vector Search Agent",
            "type": "ai_memory",
            "index": 0
        }]]
    }

    workflow["connections"]["search_product_catalog"] = {
        "ai_tool": [[{
            "node": "Vector Search Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    workflow["connections"]["find_similar_products"] = {
        "ai_tool": [[{
            "node": "Vector Search Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    workflow["connections"]["validate_product_match"] = {
        "ai_tool": [[{
            "node": "Vector Search Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    # Preference Config Agent connections
    workflow["connections"]["Preference Config Agent"] = {
        "ai_tool": [[{
            "node": "Customer Journey Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    workflow["connections"]["OpenAI Chat Preference"] = {
        "ai_languageModel": [[{
            "node": "Preference Config Agent",
            "type": "ai_languageModel",
            "index": 0
        }]]
    }

    workflow["connections"]["Memory Preference"] = {
        "ai_memory": [[{
            "node": "Preference Config Agent",
            "type": "ai_memory",
            "index": 0
        }]]
    }

    workflow["connections"]["save_user_preferences"] = {
        "ai_tool": [[{
            "node": "Preference Config Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    workflow["connections"]["update_delivery_preferences"] = {
        "ai_tool": [[{
            "node": "Preference Config Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    # Supplier Manager Agent connections
    workflow["connections"]["Supplier Manager Agent"] = {
        "ai_tool": [[{
            "node": "Supplier Journey Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    workflow["connections"]["OpenAI Chat SupplierMgr"] = {
        "ai_languageModel": [[{
            "node": "Supplier Manager Agent",
            "type": "ai_languageModel",
            "index": 0
        }]]
    }

    workflow["connections"]["Memory SupplierMgr"] = {
        "ai_memory": [[{
            "node": "Supplier Manager Agent",
            "type": "ai_memory",
            "index": 0
        }]]
    }

    workflow["connections"]["register_supplier"] = {
        "ai_tool": [[{
            "node": "Supplier Manager Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    workflow["connections"]["update_supplier_data"] = {
        "ai_tool": [[{
            "node": "Supplier Manager Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    # Price Upload Agent connections
    workflow["connections"]["Price Upload Agent"] = {
        "ai_tool": [[{
            "node": "Supplier Journey Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    workflow["connections"]["OpenAI Chat Price"] = {
        "ai_languageModel": [[{
            "node": "Price Upload Agent",
            "type": "ai_languageModel",
            "index": 0
        }]]
    }

    workflow["connections"]["Memory Price"] = {
        "ai_memory": [[{
            "node": "Price Upload Agent",
            "type": "ai_memory",
            "index": 0
        }]]
    }

    workflow["connections"]["parse_price_list"] = {
        "ai_tool": [[{
            "node": "Price Upload Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    workflow["connections"]["bulk_update_prices"] = {
        "ai_tool": [[{
            "node": "Price Upload Agent",
            "type": "ai_tool",
            "index": 0
        }]]
    }

    return workflow


def main():
    """Main execution function"""

    # Read current workflow
    workflow_path = Path("/home/user/frepi_proyect_agents/Frepi_MVP2_Agent_Architecture.json")

    print(f"📖 Reading workflow from: {workflow_path}")
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Current nodes: {len(workflow['nodes'])}")

    # Add missing nodes and connections
    print("🔧 Adding missing nodes and connections...")
    workflow = add_missing_nodes_and_connections(workflow)

    print(f"✅ Total nodes after update: {len(workflow['nodes'])}")

    # Save updated workflow
    print(f"💾 Saving updated workflow...")
    with open(workflow_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Workflow completed successfully!")
    print(f"\n📊 Summary:")
    print(f"   - Total nodes: {len(workflow['nodes'])}")
    print(f"   - Total connections: {len(workflow['connections'])}")
    print(f"\n🎉 Frepi MVP2 Agent Architecture is now complete!")


if __name__ == "__main__":
    main()
