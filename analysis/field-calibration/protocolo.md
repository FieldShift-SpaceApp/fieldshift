# Protocolo de campo: medir a cobertura de palha com uma corda de 15 m (uns 20 minutos por talhão)

> Versão em inglês: [`protocol.md`](protocol.md). O método da corda é o transecto linear usado pela Embrapa Soja no Documentos 454 (Franchini et al. 2023, pp. 25–29, a partir de Morrison et al. 1993). As etapas de foto, localização e condição da superfície vêm do protocolo Land Cover do NASA GLOBE Observer (ver "O que vem do GLOBE" abaixo). O FieldShift não faz parte do GLOBE e não tem acordo com a NASA nem com a Embrapa.

## O que precisa

- uma corda ou trena de **15 m**, marcada **a cada 15 cm** (100 marcas; com trena, leia a cada 15 cm);
- um celular com câmera e GPS (Google Maps);
- esta folha ou a tela `/calibrate` do app (ela conta por você e guarda tudo no próprio celular).

## Quando

- **Antes da semeadura ou logo depois**, quando o talhão mostra palha e solo, não um dossel verde fechado. Planta verde esconde o sinal da palha no satélite (o Documentos 454 descarta NDVI > 0,3).
- **Solo seco.** Não meça no dia seguinte a uma chuva: solo e palha molhados mudam o índice do satélite. Anote se o solo estava úmido.
- **No dia do satélite ou perto dele.** Landsat 8/9 e Sentinel-2 passam a cada poucos dias; quanto mais perto da passagem, melhor (o app GLOBE Observer mostra os horários; ±5 dias é o limite útil, porque a semeadura muda a cobertura depressa).

## Passos

1. **Escolha um ponto uniforme** pelo menos 50 m para dentro do talhão, longe de estrada, cabeceira e mancha úmida. O pixel do satélite tem 30 m; a área em volta, uns 100 m × 100 m, deve parecer igual (o tamanho de sítio do GLOBE Observer).
2. **Estique a corda na diagonal** das linhas de plantio (45°), reta e rente ao chão.
3. **Olhe de cima cada uma das 100 marcas** e anote uma letra para o que está embaixo da marca:
   - **P** palha (qualquer resto de planta morta: trigo, aveia, milho, resteva de soja);
   - **S** solo exposto (terra ou torrão visível embaixo da marca);
   - **V** planta verde (cultura viva ou invasora).
   Conte só o que está exatamente embaixo da marca, do tamanho da ponta de um lápis. Não escolha: se encosta na palha, é palha.
4. **Cobertura de palha = marcas P ÷ 100.** Exemplo: 87 P, 9 S, 4 V → 87% de palha.
5. **Repita em 3 cordas** em pontos diferentes do mesmo talhão, se puder (a conta do README mostra por que uma corda só não basta perto da linha dos 90%).
6. **Uma foto vertical** no meio da corda, celular nivelado na altura do peito, apontado para baixo (a foto "down" do GLOBE). Opcional: quatro fotos para norte, leste, sul e oeste.
   - *Foto no lugar da corda:* ponha uma grade de 10 × 10 sobre a foto vertical e conte os 100 cruzamentos do mesmo jeito (P / S / V). É mais rápido e menos exato que a corda; marque como "foto".
7. **Localização:** no meio da corda, abra o Google Maps, segure o dedo sobre o ponto azul e copie as coordenadas (por exemplo `-28.6385, -53.6063`). Elas ficam com você e com o analista; **nunca são publicadas**.
8. **Anote:** data, o que havia no talhão no inverno (trigo, aveia, azevém, pousio, outro) e se foi dessecado ou colhido, e se o solo estava seco ou úmido.

## O que acontece com a medição

O analista roda `fetch_pixel.py` com as coordenadas e a data: ele acha o pixel NASA HLS ou Landsat do dia limpo mais próximo e o seu NDTI (o índice de palha). Depois o `calibrate.py` junta o seu ponto à régua da Embrapa e recalcula a incerteza. O arquivo público guarda só data, contagens, cobertura, cultura de inverno e os valores do satélite, **nunca as coordenadas nem o seu nome**.

## O que vem do GLOBE, e o que não vem

| GLOBE Observer Land Cover (NASA) | Aqui |
|---|---|
| Seis fotos: norte, leste, sul, oeste, para cima, **para baixo** (cobertura do chão) | **Adotado:** a foto para baixo é obrigatória, as quatro laterais opcionais; sem foto para cima (não há dossel) |
| Observar uma área uniforme de 100 m × 100 m (50 m para cada lado) | **Adotado** como "escolha um ponto uniforme" |
| Registrar a condição da superfície (água parada, neve, folhas) | **Adotado** como solo seco / úmido (a umidade muda o NDTI) |
| Mostrar os horários de passagem do Landsat / Sentinel-2 | **Adotado** como "meça perto do dia do satélite" |
| Classificar cada foto pela Classificação UNESCO Modificada (MUC) com barras de porcentagem | **Não adotado:** contamos 100 pontos em vez de estimar no olho, porque a régua do satélite precisa de uma porcentagem medida |
| Enviar ao banco de dados do GLOBE (dado aberto) | **O FieldShift não envia.** Você pode registrar o mesmo local no app oficial GLOBE Observer por conta própria |

Fontes: GLOBE Observer, "Land Cover: taking observations", https://observer.globe.gov/do-globe-observer/land-cover/taking-observations (acesso em 15/11/2026); protocolo GLOBE Land Cover Classification, https://www.globe.gov/web/biosphere/protocols/land-cover-classification; Embrapa Soja Documentos 454, https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1156802/1/DOC-454.pdf.
