# ADR 0013 — Framework de Detecção de Objetos

## Status
Aceito (2026-08-02)

## Contexto
A [ADR 0001](0001-classificacao-vs-deteccao.md) decidiu detecção de objetos (bounding boxes) desde o MVP, e a [ADR 0011](0011-formato-anotacao-dataset.md) fechou o formato de anotação (COCO) e a taxonomia de classes (vassoura-de-bruxa, podridão-parda, moniliase). Faltava escolher o framework de treino/avaliação do modelo.

Fatores relevantes para a escolha:
- **Dataset pequeno no início**: `dataset/` ainda está vazio (só estrutura `.gitkeep`) — o treino vai começar com poucas imagens anotadas, o que favorece frameworks fortes em transfer learning a partir de pesos pré-treinados.
- **Inferência cloud-first no MVP** ([ADR 0002](0002-inferencia-on-device-vs-nuvem.md)), com on-device em fase 2 condicionado a modelo estável — não é um requisito bloqueante agora, mas pesa a favor de manter um caminho de exportação para mobile no futuro.
- **Stack backend em Python** ([ADR 0005](0005-stack-de-backend.md)) — o framework de treino precisa se integrar bem a esse ecossistema.
- **Modelo de negócio**: o usuário confirmou (2026-08-02) que o CABRUCA será distribuído como **open source**, o que remove restrições de licenciamento copyleft como bloqueio de uso.

## Opções consideradas

- **(a) Ultralytics YOLO (v8/v11)** — melhor resultado prático em transfer learning com dataset pequeno, API de treino/avaliação simples, exporta nativamente para ONNX/TFLite/CoreML (cobre fase 2 sem esforço extra), comunidade e material de anotação/augmentação abundantes. Licença AGPL-3.0 — sem problema dado que o projeto é open source, mas o usuário optou por não adotar mesmo assim.
- **(b) Detectron2 (Meta)** — desenhado nativamente em torno do formato/avaliação COCO (`pycocotools`, mAP COCO-style), o que casa diretamente com a decisão da ADR 0011. Licença Apache-2.0. Trade-offs: sem transfer learning tão forte para dataset pequeno sem tuning manual mais cuidadoso (learning rate, augmentation, escolha de backbone), sem caminho oficial de exportação para mobile (TFLite/CoreML) — se a fase 2 on-device avançar, vai exigir conversão manual ou reconsiderar o framework nesse momento —, e desenvolvimento do projeto mais lento nos últimos anos (Meta reduziu o ritmo de releases).
- **(c) Torchvision detection models** (`torchvision.models.detection`) — dependência mínima (vem com PyTorch), licença BSD, loader nativo para formato tipo-COCO. Trade-offs: bem menos tooling pronto (augmentation, scripts de treino, exportação) — exigiria escrever e manter mais código próprio.

## Decisão
Adotar **Detectron2** para treino e avaliação do modelo de detecção — decisão explícita do usuário (2026-08-02), priorizando integração nativa com COCO (formato já decidido na ADR 0011) e licença permissiva, mesmo sabendo que o projeto é open source e que isso removeria a única ressalva contra o YOLO.

## Consequências
- Scripts de treino/avaliação em `models/` vão usar a API do Detectron2 (`DefaultTrainer` ou customizado), consumindo diretamente os JSONs COCO de `dataset/annotations/` via `register_coco_instances`, sem etapa de conversão de formato.
- Avaliação de modelo usa métricas COCO-style (mAP) nativamente via `COCOEvaluator`.
- Não há caminho oficial de exportação para mobile (TFLite/CoreML) — se a fase 2 de inferência on-device (ADR 0002) avançar, será necessário avaliar conversão via ONNX (com possível perda de operações não suportadas) ou reabrir esta ADR para reconsiderar o framework nesse momento.
- Dataset pequeno no início exige atenção extra a transfer learning a partir de pesos pré-treinados no COCO/ImageNet (model zoo do Detectron2) e a augmentation mais agressiva — sem isso o risco de overfitting é maior do que seria com YOLO.
- Escolha de arquitetura específica dentro do Detectron2 (Faster R-CNN vs. RetinaNet vs. Mask R-CNN, backbone ResNet-50 vs. ResNet-101/FPN) e hiperparâmetros de treino ficam para quando o dataset tiver volume suficiente para os primeiros experimentos — não são decididos por esta ADR.

## # REVISAR:
- Arquitetura específica dentro do Detectron2 (modelo, backbone) — decisão de implementação, não arquitetural, fica para a etapa de treino.
- Estratégia de augmentation e hiperparâmetros de transfer learning para dataset pequeno — mesma observação acima.
