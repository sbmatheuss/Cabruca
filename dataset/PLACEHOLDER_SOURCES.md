# Imagens placeholder — teste de pipeline (não é o dataset de treino real)

Estas 5 imagens foram adicionadas em 2026-08-05 só para testar o pipeline
completo do dataset (CVAT → export COCO → `validate_dataset.py` → DVC), não
para treinar o modelo de detecção de verdade. Critério: imagens com licença
verificável (CC0), não fotos do Google Images sem procedência clara — ver
discussão registrada na sessão. Devem ser **removidas e substituídas por
fotos de campo reais** assim que houver.

Cobertura: só `podridao-parda` e `moniliase`. `vassoura-de-bruxa` ficou de
fora — nenhuma imagem com licença livre encontrada mostra o sintoma real
(broto malformado em formato de vassoura); só havia fotos de estúdio do
corpo de frutificação do fungo, o que ensinaria o modelo a reconhecer a
coisa errada.

| Arquivo | Classe | Fonte | Autor | Licença | URL |
|---|---|---|---|---|---|
| `podridao-parda_01.jpg` | podridao-parda | Wikimedia Commons (via Flickr) | Scot Nelson | CC0 1.0 | https://commons.wikimedia.org/wiki/File:Cacao_black_pod_rot_39572305384.jpg |
| `podridao-parda_02.jpg` | podridao-parda | Wikimedia Commons (via Flickr) | Scot Nelson | CC0 1.0 | https://commons.wikimedia.org/wiki/File:Cacao_black_pod_rot_39744592361.jpg |
| `podridao-parda_03.jpg` | podridao-parda | Wikimedia Commons (via Flickr) | Scot Nelson | CC0 1.0 | https://commons.wikimedia.org/wiki/File:Cacao_black_pod_rot_38577373995.jpg |
| `podridao-parda_04.jpg` | podridao-parda | Wikimedia Commons (via Flickr) | Scot Nelson | CC0 1.0 | https://commons.wikimedia.org/wiki/File:Cacao_black_pod_rot_29064726523.jpg |
| `moniliase_01.jpg` | moniliase | iNaturalist | unclecactus | CC0 | https://www.inaturalist.org/observations/58102409 |

Nenhuma anotação COCO ainda existe para estas imagens — próximo passo é
subir o CVAT (ADR 0012) e desenhar as bounding boxes.
