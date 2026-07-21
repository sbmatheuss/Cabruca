import uuid

# REVISAR: usuário e propriedade fixos, usados só enquanto a autenticação real
# via Cognito (ADR 0007) não está implementada. Consumido por
# app/api/deps.py (get_current_user_id) e por scripts/seed_dev.py.
# Remover quando a validação de JWT entrar.
DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEV_PROPERTY_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
