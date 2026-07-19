# ADR 0009 — Formato das Coordenadas de Bounding Box

## Status
Aceito (2026-07-19)

## Contexto
A [ADR 0001](0001-classificacao-vs-deteccao.md) decidiu que a API retorna detecções como caixas delimitadoras (classe + caixa + confiança), mas não especificou a unidade das coordenadas. O schema inicial (`backend/app/models/detection.py`) e o contrato de API (`docs/api/contrato-endpoints.md`) ficaram com um `bbox: [x, y, largura, altura]` sem unidade definida, marcado como `REVISAR` — sem isso alinhado, o pipeline de inferência e o app mobile podem interpretar o mesmo valor de formas incompatíveis.

## Opções consideradas
- **Pixels absolutos** — coordenadas em pixels da imagem original enviada. Fácil de ler/depurar diretamente no banco. Se o modelo de detecção rodar inferência sobre uma versão redimensionada da imagem (comum em arquiteturas como YOLO, que frequentemente redimensionam para uma entrada fixa, ex. 640×640), é necessário reconverter a predição para a resolução original antes de gravar — passo extra no pipeline de inferência.
- **Normalizado 0-1 (convenção YOLO)** — coordenadas relativas ao tamanho da imagem, escala-invariante. É a saída nativa da família YOLO, uma das arquiteturas candidatas citadas na ADR 0001, o que evita um passo de conversão no pipeline caso essa família seja adotada. Para renderizar a caixa sobre a foto, o app mobile multiplica pelas dimensões da própria imagem — dimensão que ele já tem, por ser o autor da foto.

## Decisão
Adotar coordenadas **normalizadas 0-1** para `bbox_x`, `bbox_y`, `bbox_width`, `bbox_height`.

## Consequências
- Nenhuma mudança de tipo de coluna é necessária — os campos já são `float`, compatíveis com valores em 0-1.
- O pipeline de inferência é responsável por entregar as coordenadas já normalizadas antes de persistir a detecção, independentemente da resolução em que a inferência de fato rodou.
- O app mobile precisa multiplicar `bbox_x`/`bbox_width` pela largura e `bbox_y`/`bbox_height` pela altura da imagem exibida para desenhar a caixa corretamente.
- O contrato de API (`docs/api/contrato-endpoints.md`) deve deixar essa convenção explícita no exemplo de resposta, para não repetir a ambiguidade que motivou esta ADR.

## # REVISAR:
Nenhum ponto pendente nesta ADR — decisão confirmada explicitamente pelo usuário.
