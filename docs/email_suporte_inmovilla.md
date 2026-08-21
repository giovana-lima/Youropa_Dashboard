Assunto: Campo personalizado "Projeto" não é retornado pela API REST v1

Olá,

Somos a agência Youropa Real Estate (nº de agência 14287) e usamos a API REST v1 (procesos.inmovilla.com/api/v1) para automatizar a leitura dos nossos dados de imóveis.

Criamos um campo personalizado chamado "Projeto" (usado para agrupar várias referências de imóveis que pertencem ao mesmo empreendimento, ex: "Prime Living", "Jardins do Marquês"). Esse campo é filtrável normalmente na interface do CRM (em Imóveis > Filtros), onde aparece como um campo do tipo "que contenha", com etiqueta interna "projeto".

No entanto, ao consultar o endpoint GET /propiedades/?cod_ofer={cod_ofer} pela API REST, o campo "Projeto" não aparece em nenhum lugar da resposta JSON, mesmo verificando todos os ~246 campos retornados.

Perguntas:
1. É possível que a API retorne esse campo personalizado? Se sim, qual o nome exato da chave que devemos usar na consulta ou que aparece na resposta?
2. Se não for possível hoje, é uma funcionalidade que pode ser adicionada à API?

Isso é importante para nós porque precisamos automatizar relatórios agrupados por projeto/empreendimento (novos imóveis por projeto, leads por projeto) sem depender de leitura manual da interface — o que não escala à medida que o número de imóveis cresce.

Obrigada,
Giovana Lima
Youropa Real Estate (Agência 14287)
