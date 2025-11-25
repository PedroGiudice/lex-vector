graph LR
    classDef start fill:#000,stroke:#50FA7B,stroke-width:2px,color:#fff;
    classDef end fill:#000,stroke:#FF5555,stroke-width:2px,color:#fff;
    classDef agent fill:#000,stroke:#8BE9FD,stroke-width:1px,color:#fff;
    classDef decision fill:#000,stroke:#FF79C6,stroke-width:1px,color:#fff;
    classDef default fill:#000,stroke:#888,stroke-width:1px,color:#fff;

    1(["Início"]):::start
    2["CARTÓGRAFO - Motor de Layout"]:::script
    3["Leitura Estrutura Página"]:::script
    4["Detecção Sistema Judicial"]:::script
    5{"PJE | ESAJ | EPROC | PROJUDI"}:::decision
    6["Cálculo Histograma Densidade"]:::script
    7["Identificação Picos/Tarjas"]:::script
    8["Definição Safe BBox"]:::script
    9["Output layout.json"]:::script
    10["SANEADOR - Motor de Visão"]:::script
    11["Verificação Tipo Página"]:::script
    12["Bypass (Texto Digital)"]:::script
    13["Rasterização Página"]:::script
    14["ImageCleaner.detect_mode()"]:::script
    15{"Digital ou Scanned?"}:::decision
    16["remove_gray_watermarks()"]:::script
    17["has_speckle_noise()"]:::script
    18{"Tem Ruído?"}:::decision
    19["remove_speckles()"]:::script
    20["remove_color_stamps()"]:::script
    21["clean_dirty_scan()"]:::script
    22["remove_speckles()"]:::script
    23["Output images/*.png"]:::script
    24["EXTRATOR - Motor de Extração"]:::script
    25["Leitura layout.json + images"]:::script
    26{"Método de Extração?"}:::decision
    27["pdfplumber (bbox filter)"]:::script
    28["Tesseract OCR"]:::script
    29["Unificação Fragmentos Texto"]:::script
    30["CleaningEngine (75+ patterns)"]:::script
    31["Aplicação Marcadores Fronteira"]:::script
    32["Output final.md"]:::script
    33["BIBLIOTECÁRIO - Classificador"]:::script
    34["Leitura final.md"]:::script
    35["Taxonomia Legal (12 categorias)"]:::script
    36["Segmentação por Peças (janela adaptativa)"]:::script
    37{"Seção ANEXOS?"}:::decision
    38["Boundary Detector (conservador)"]:::script
    39["Refinamento Subsecões"]:::script
    40["Output structure.json + final_tagged.md"]:::script
    41(["Fim"]):::end

    1 -->|next| 2
    2 -->|next| 3
    3 -->|next| 4
    4 -->|next| 5
    5 -->|next| 6
    6 -->|next| 7
    7 -->|next| 8
    8 -->|next| 9
    9 -->|next| 10
    10 -->|next| 11
    11 -->|Texto Digital| 12
    11 -->|Imagem ou Híbrido| 13
    13 -->|next| 14
    14 -->|next| 15
    15 -->|Digital| 16
    15 -->|Scanned| 20
    16 -->|next| 17
    17 -->|next| 18
    18 -->|Sim| 19
    18 -->|Não| 23
    19 -->|next| 23
    20 -->|next| 21
    21 -->|next| 22
    22 -->|next| 23
    12 -->|merge| 24
    23 -->|merge| 24
    24 -->|next| 25
    25 -->|next| 26
    26 -->|Texto Digital| 27
    26 -->|Imagem| 28
    27 -->|next| 29
    28 -->|next| 29
    29 -->|next| 30
    30 -->|next| 31
    31 -->|next| 32
    32 -->|next| 33
    33 -->|next| 34
    34 -->|next| 35
    35 -->|next| 36
    36 -->|next| 37
    37 -->|Sim| 38
    37 -->|Não| 40
    38 -->|next| 39
    39 -->|next| 40
    40 -->|finish| 41
