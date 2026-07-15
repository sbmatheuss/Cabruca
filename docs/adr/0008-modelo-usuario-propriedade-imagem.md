# ADR 0008 — Modelo de Dados Usuário-Propriedade-Imagem

## Status
Aceito (2026-07-14)

## Contexto
A [ADR 0007](0007-autenticacao.md) resolveu autenticação, mas deixou explicitamente em aberto um ponto de modelo de dados: o usuário autenticado é um técnico/agrônomo que atende **várias propriedades**, então uma imagem não pode pertencer diretamente ao usuário — precisa pertencer a uma propriedade, e um usuário precisa poder se associar a várias propriedades.

Duas decisões do usuário definem o formato:
- **Compartilhamento**: uma propriedade pode ser acessada por **vários técnicos** ao longo do tempo (não é 1 técnico = 1 propriedade fixa) — exige uma relação N:N entre usuário e propriedade, não N:1.
- **Produtor**: não existe, por ora, uma entidade separada para o agricultor/produtor (nome, contato) — a propriedade é o registro mínimo, sem cadastro formal de pessoa física do produtor no MVP.

Adicionalmente, o usuário decidiu que o mecanismo pelo qual um técnico ganha acesso a uma propriedade já existente é um **código de propriedade** (compartilhável entre técnicos), e que **revogação de acesso individual** (remover um técnico específico, sem afetar os demais) é decidida nesta mesma ADR, não adiada: apenas quem criou a propriedade tem permissão de revogar o acesso de outro técnico.

## Opções consideradas

### Relação usuário↔propriedade
- **N:1 (uma propriedade pertence a um único técnico)** — mais simples, mas incompatível com a decisão do usuário de que vários técnicos acessam a mesma propriedade ao longo do tempo (ex.: substituição de técnico, equipe atendendo a mesma fazenda).
- **N:N via tabela de associação** (`user_properties`) — permite múltiplos técnicos por propriedade e múltiplas propriedades por técnico, com histórico de quem tem acesso. Custo: mais uma tabela e uma checagem de junção em toda regra de autorização, em vez de uma coluna simples de dono.

### Mecanismo de concessão de acesso a uma propriedade existente
- **Código de propriedade** (string compartilhável, gerada na criação da propriedade; outro técnico usa o código para se associar) — simples de implementar e de explicar para o usuário final, não depende de um técnico já associado aprovar ativamente cada novo acesso.
- **Convite direto** (um técnico já associado convida outro por email/usuário) — mais controle de quem entra, mas exige um fluxo de convite/aprovação mais complexo, não solicitado pelo usuário.
- **Nenhum controle** (qualquer técnico autenticado vê qualquer propriedade) — descartado: viola o princípio de que dados de propriedade/geolocalização são sensíveis (já sinalizado na ADR 0004 quanto à LGPD).

### Quem pode revogar o acesso de outro técnico
- **Só quem criou a propriedade** (`created_by`) — usa um campo que já existe no modelo, não exige schema novo nem conceito de papel adicional. Custo: concentra a permissão de revogar em uma única pessoa; se o criador sair da propriedade (ver Consequências), ninguém mais consegue revogar acesso de terceiros depois disso.
- **Qualquer técnico associado** — descartado: qualquer membro poderia remover qualquer outro, inclusive por má-fé ou engano, sem hierarquia nenhuma.
- **Papel explícito (admin/membro) em `user_properties`** — mais flexível (permite múltiplos admins, promoção/rebaixamento), mas exige coluna nova e decisões adicionais (quem vira admin por padrão, se pode haver mais de um) não solicitadas pelo usuário.

### O que acontece quando o criador sai (transferência de posse)
- **Transferência explícita antes de sair, bloqueando a saída até lá** — o criador escolhe deliberadamente o sucessor entre os já associados; a propriedade nunca fica "sem dono" enquanto tiver outros membros. Custo: mais uma ação que o criador precisa lembrar de fazer.
- **Reatribuição automática** (ex.: o associado há mais tempo vira o novo criador) — não exige ação manual, mas concede poder de revogar terceiros a alguém sem esse alguém pedir ou ser avisado, o que é uma mudança de permissão silenciosa e potencialmente indesejada.
- **Deixar sem dono até alguém entrar de novo pelo código** — mais simples, mas trava revogação de terceiros indefinidamente enquanto a propriedade tiver membros e nenhum dono; escolhida apenas como comportamento residual para quando a propriedade fica **sem nenhum membro** (não quando ainda há membros e o criador tenta sair sem transferir — nesse caso a saída é bloqueada, não permitida).

## Decisão

**Entidades e relações:**
- `users` — espelha a identidade do Cognito (claim `sub` do JWT); sem dado de credencial (mora no Cognito, ADR 0007).
- `properties` — propriedade/talhão: nome, localização, `property_code` (código único, gerado na criação, usado para outros técnicos se associarem), `created_by` (técnico que criou), `created_at`.
- `user_properties` — tabela de associação N:N entre `users` e `properties` (`user_id`, `property_id`, `associated_at`). Um técnico só acessa uma propriedade se existir uma linha aqui.
- `images` — passa a referenciar `property_id` (não mais o usuário diretamente); mantém `uploaded_by` (qual técnico tirou aquela foto específica), para rastreabilidade mesmo com a propriedade sendo compartilhada.
- `detections` — inalterado, referenciando `image_id` (ADR 0001).

**Fluxo de acesso a propriedade:**
- Criar propriedade → o criador é automaticamente associado (linha em `user_properties`) e um `property_code` é gerado.
- Entrar em propriedade existente → técnico informa o `property_code`, API cria a linha de associação correspondente.

**Regra de autorização:** um usuário pode ver/modificar uma imagem se existir uma linha em `user_properties` ligando esse usuário à `property_id` daquela imagem — não mais "é o dono direto da imagem".

**Revogação de acesso:** remover a linha correspondente em `user_properties` remove o acesso de um técnico específico, sem afetar os demais associados. Duas formas de acionar:
- **Auto-remoção**: qualquer técnico associado pode remover a própria associação (sair da propriedade) — com uma exceção para o criador, ver abaixo.
- **Remoção de terceiro**: só o `created_by` da propriedade pode remover a associação de outro técnico.

**Transferência de posse (resolve o `# REVISAR:` anterior sobre criador sair):**
- O criador pode transferir a posse (`created_by`) para outro técnico já associado à propriedade, através de uma ação explícita.
- O criador **não pode sair** (auto-remoção) enquanto existirem outros técnicos associados — precisa transferir a posse antes. Se o criador for o único associado restante, pode sair livremente; a propriedade fica sem nenhum associado, mas não é apagada.
- Se uma propriedade sem nenhum associado receber uma nova entrada via `property_code`, esse técnico se torna automaticamente o novo `created_by` — não há dono conflitante para resolver, então não é necessária uma etapa de aprovação.

## Consequências
- O [contrato de endpoints](../api/contrato-endpoints.md) precisa de novos endpoints para propriedade (criar, entrar via código, listar, listar membros, revogar/sair) e o `POST /images` passa a exigir `property_id` no corpo da requisição — atualizado junto com esta ADR.
- A checagem de autorização em `GET`/`DELETE /images/{id}` muda de "comparar dono direto" para "existe associação usuário↔propriedade" — uma junção a mais em toda consulta de acesso.
- Rastreabilidade preservada: mesmo com propriedade compartilhada, cada imagem guarda `uploaded_by`, então sempre é possível saber qual técnico tirou qual foto — inclusive depois que esse técnico for revogado ou sair.
- Revogar o acesso de um técnico não apaga as imagens que ele enviou; elas continuam na propriedade, visíveis aos demais associados.

## # REVISAR:
- Geração/formato do `property_code` (tamanho, se é reutilizável após expirar, se pode ser regenerado) — decisão de implementação futura.
