# ADR 0007 — Autenticação

## Status
Aceito (2026-07-14)

## Contexto
O [contrato de endpoints](../api/contrato-endpoints.md) foi desenhado com um placeholder (`owner_id`) para identidade de chamador, deixando autenticação explicitamente como `# REVISAR:` — combinado com o usuário que essa decisão seria tomada como checkpoint antes de qualquer código de implementação dos endpoints.

Dois pontos levantados com o usuário definem o formato da solução:
- **Usuário principal do app**: técnico/agrônomo (extensionista) que visita várias propriedades, tirando fotos em nome de diversos produtores diferentes — não é o agricultor final autenticando no próprio celular.
- **Fricção de login aceitável**: cadastro tradicional (email + senha), já que o público (profissionais de campo) tem familiaridade suficiente com esse fluxo, ao contrário do agricultor final, para quem cadastro leve ou zero fricção seria mais adequado (mas não é o caso aqui).

## Opções consideradas

### Mecanismo de login
- **Email + senha** — familiar para o público técnico já validado com o usuário. Alternativas descartadas sem aprofundar: SMS/OTP (mais adequado a usuário final não-técnico, não é o perfil aqui) e OAuth social (Google/Apple) (assume conta pessoal de email já vinculada, menos natural para uma conta profissional/corporativa).

### Quem implementa o armazenamento/verificação de credenciais
- **Auth própria** (backend guarda hash de senha, emite e valida JWT) — controle total, zero dependência externa nova, mas o backend passa a ser responsável por armazenar credenciais com segurança: hashing correto, rate limiting de tentativas de login, fluxo de recuperação de senha. É o tipo de código onde um erro de segurança é caro, e não é o foco de valor do produto.
- **AWS Cognito** (provedor de identidade gerenciado) — offload do armazenamento/segurança de senha para um serviço desenhado para isso; já estamos no ecossistema AWS pela [ADR 0004](0004-armazenamento-de-imagens.md) (S3), e o Cognito tem free tier generoso; emite JWT que a API valida sem guardar segredo de senha. Custo: mais uma dependência de serviço gerenciado, curva de configuração do Cognito.

## Decisão
Login via **email + senha**, com **AWS Cognito** como provedor de identidade. O backend nunca armazena nem processa a senha diretamente — o app autentica contra o Cognito, recebe um JWT, e envia esse token em cada chamada à API. A API valida o JWT (assinatura e expiração) e extrai o identificador do usuário (`sub` do token) para popular o campo antes chamado de `owner_id` no contrato de endpoints.

Consistente com a decisão da ADR 0005: fica registrado como razão principal evitar reconstruir manuseio de senha (superfície de risco de segurança), não reduzir fricção de login — a fricção do cadastro tradicional já foi aceita explicitamente pelo usuário.

## Consequências
- O contrato de endpoints (`docs/api/contrato-endpoints.md`) precisa ser atualizado: toda rota exige um header `Authorization: Bearer <JWT>`, e o placeholder `owner_id` passa a vir do claim `sub` do token validado, não de um campo enviado pelo cliente.
- Cria dependência de disponibilidade do AWS Cognito — se o Cognito estiver fora do ar, login/renovação de token param, mesmo que a API e o storage estejam saudáveis.
- Uso do free tier do Cognito precisa do mesmo tipo de monitoramento já previsto para o S3 na ADR 0004 (evitar cobrança surpresa se o uso ultrapassar os limites gratuitos).
- **Não resolvido por esta ADR**: o usuário principal é um técnico que atende várias propriedades — isso implica um modelo de dados onde uma imagem/detecção pertence a uma *propriedade*, não só a um *usuário autenticado*. Essa é uma decisão de modelo de dados (associação usuário↔propriedade↔imagem), não de mecanismo de autenticação, e fica marcada como pendência separada, não coberta aqui.
- Rate limiting por usuário (nota de gatilho futuro já registrada na [ADR 0005](0005-stack-de-backend.md)) agora tem um identificador real (`sub` do JWT) para se basear, mas a implementação de rate limiting em si continua não decidida.

## # REVISAR:
- Modelo de dados de associação técnico↔propriedade↔imagem (mencionado acima em Consequências) — decisão futura, fora do escopo desta ADR.
- Detalhes de configuração do Cognito (política de senha, expiração de token, refresh token) — decisão de implementação futura.
