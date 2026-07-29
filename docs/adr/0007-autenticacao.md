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

## Atualização 2026-07-28 — política de senha, expiração de token e provisionamento de usuário

### Contexto
Os dois primeiros itens do REVISAR original ficaram em aberto até agora: configuração de senha/token do Cognito, e como a linha em `users` é criada para um `sub` novo do Cognito (gap identificado depois desta ADR: nada no repo provisiona essa linha, então um usuário recém-cadastrado no Cognito receberia erro na primeira chamada à API). Fechado com o usuário em 2026-07-28.

### Decisões

**Política de senha**: padrão do Cognito (mínimo 8 caracteres, exige maiúscula, minúscula, número e símbolo). Alternativas consideradas: política focada em comprimento mínimo maior sem exigir classes de caractere (mais alinhada à recomendação atual do NIST 800-63B, que considera complexidade forçada uma prática ultrapassada) e verificação de senha vazada via Cognito Advanced Security (mais segura, mas sai do free tier — custo recorrente incompatível com a prática de monitorar uso gratuito já adotada na ADR 0004). Optou-se pelo padrão do serviço.

**Duração do access/id token**: 24 horas (teto permitido pelo Cognito). Razão: o app captura fotos offline e sobe numa fila assíncrona quando a conectividade volta (ADR 0002) — um token de vida curta (padrão de 60 minutos) aumentaria a chance de expirar durante uma visita a propriedade sem sinal, exigindo login manual antes de esvaziar a fila. Trade-off aceito: janela de exposição maior se o aparelho for perdido ou roubado antes do logout.

**Duração do refresh token**: 7 dias. Prioriza segurança sobre conveniência — a sessão expira em uma semana mesmo sem logout explícito, limitando a janela de risco em caso de perda/roubo do aparelho, às custas de o técnico precisar refazer login semanalmente.

**Provisionamento da linha em `users`**: lazy-create na API. A dependency que valida o JWT e extrai o claim `sub` (substituindo `get_current_user_id` em `app/api/deps.py`) passa a checar se já existe uma linha em `users` com aquele id e, se não existir, cria (upsert, para evitar condição de corrida entre requests concorrentes do mesmo usuário novo). Alternativa descartada: Cognito Post-Confirmation Lambda trigger — arquiteturalmente mais "limpo" (provisionamento acontece uma vez, no cadastro), mas introduz um componente de infra novo (Lambda + deploy + acesso de rede ao Postgres) num projeto que ainda não tem decisão de deploy/serverless (ver ADR 0005); complexidade não justificada agora.

### Consequências
- `app/core/config.py` precisa ganhar os settings de Cognito (user pool id, client id, region) quando a implementação entrar.
- `app/api/deps.py` deixa de retornar `DEV_USER_ID` fixo; `app/core/dev_auth.py` é removido quando a validação real entrar.
- Testes que hoje dependem do stub (`test_images.py`, `test_properties.py`) vão precisar de uma forma de gerar/mockar um JWT válido.

## # REVISAR:
- Modelo de dados de associação técnico↔propriedade↔imagem (mencionado acima em Consequências) — decisão futura, fora do escopo desta ADR.
- Detalhes de implementação do lazy-create de `users`: onde exatamente no código (dependency de auth vs. middleware) e se o upsert é feito via `INSERT ... ON CONFLICT DO NOTHING` seguido de leitura, ou `SELECT` com fallback de `INSERT` tratando exceção de unicidade — decisão de implementação, não arquitetural, fica para quando o código for escrito.
