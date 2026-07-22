import uuid

# Stub deliberado: usuário e propriedade fixos, usados enquanto não existe
# um User Pool do Cognito (ADR 0007) contra o qual validar JWT de verdade —
# não é uma decisão em aberto, é uma dependência de infraestrutura ainda não
# criada. Consumido por app/api/deps.py (get_current_user_id) e por
# scripts/seed_dev.py. Remover quando o Cognito existir e a validação de JWT
# entrar.
DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEV_PROPERTY_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
