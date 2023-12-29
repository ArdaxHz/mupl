## Aceita arquivos ZIP e pastas. Arquivos e pastas para upar precisam estar em uma pasta nomeada`to_upload`. Código foi testado em Python 3.9, então realize o download da linguagem e instale essa versão ou superior.
### Os nomes dos arquivos **PRECISAM** estar no formato `título_do_mangá [língua] - cXXX (vYY) (título_do_capítulo) {data_agendada} [grupo/scan]`
#### Para parar a checagem de atualização, adicione `--update` ou `-u` na parte final do arquivo.

----

- `título_do_mangá` pode tanto ser uma chave preenchida no  `name_id_map.json` ou adicionando o ID do mangá.
- `[língua]` não é obrigatório apenas pro Inglês. MangaDex usa o código ISO-639-2, então a lingua não é validada no script rodando em seu computador, mas sim deixada para a API da MDex validar. 
- Retire o prefixo de capítulo (c) se o capítulo for um oneshot, p.ex. `cXXX` > `XXX`.
- `(vYY)` Não é obrigatório se os capítulos não tiverem volumes, como os casos de grande parte dos Webtoons.
- `(título_do_capítulo)` não é obrigatório se o capítulo não tiver título. Use`{question_mark}` no lugar dos `?` na descrição do título caso houver.
- `{data_agendada}` não é obrigatória caso não agende e **PRECISA** estar no formato `AAAA-MM-DDTHH-MM-SS[+0300(GMT - Horário de Brasília como exemplo)]` se inclusa.
- `[grupo/scan]` já diz tudo. Separe cada grupo separando com um `+`. Os grupos/scans podem ser nomeados e identificados preenchendo o arquivo `name_id_map.json` ou inserindo diretamente a ID do grupo.

As imagens podem ser nomeadas ou organizadas do jeito que preferir contanto que estejam em ordem alfabética absoluta (se o capítulo tem 100 páginas, as anteriores de 100 **PRECISAM** ter os dois zeros antes), e elas **PRECISAM** estar em um dos seguintes formatos: `png`, `jpg`, `gif` ou `webp`. Nenhum outro além desses será aceito. 

*Obs: MangaDex não tem suporte para .webp; com isso, serão automaticamente convertidos pra um dos seguintes formatos durante o processo de upload: `png`, `jpg`, ou `gif`.*

----

## Exemplos
Suponho que tenho o arquivo `Yuru Camp - c001 (v01) [ABAM].cbz` como um capítulo que eu quero upar. No meu `name_id_map.json`, eu teria isso:
```
{
    "manga": {
        "Yuru Camp": "1ee97895-4796-4bcf-bcd1-5ef99c011f8b"
    },
    "group": {
        "ABAM": "d35b978c-a73b-48f1-9195-eb4a6d4afd57"
}
```
O script a partir de então pegará o arquivo com as chaves `Yuru Camp` e  `ABAM` e trocarão automaticamente pelos IDs correspondentes.

Se eu tenho um arquivo nomeado `efb4278c-a761-406b-9d69-19603c5e4c8b [spa] - 000 (Momi-san) [ABAM+00e03853-1b96-4f41-9542-c71b8692033b]`, o programa pegaria o ID do Mangá e Grupo diretamente do arquivo, a linguagem como Espanhol no código `es`, registrada como Oneshot e sem volume, o título do capítulo como `Momi-san` e os grupos/scans como `ABAM` (id retirado do `name_id_map.json`) e o grupo correspondente ao ID `00e03853-1b96-4f41-9542-c71b8692033b`.

----

## Linguagens

| Linguagem       | Código MDex   | Código ISO-639 | Linguagem       | Código MDex   | Código ISO-639 |
|:---------------:| ------------- | -------------- |:---------------:| ------------- | -------------- |
| Árabe           | ar            | ara            | Italiano        | it            | ita            |
| Bengali         | bd            | ben            | Japonês         | ja            | jpn            |
| Búlgaro         | bg            | bul            | Coreano         | ko            | kor            |
| Birmanês        | my            | bur            | Lituano         | li            | lit            |
| Bengali         | bn            | ben            | Malaio          | ms            | may            |
| Catalão         | ca            | cat            | Mongol          | mn            | mon            |
| Chinês (Simp.)  | zh            | chi            | Norueguês       | no            | nor            |
| Chinês (Trad.)  | zh-hk         | chi            | Persa           | fa            | per            |
| Checo           | cs            | cze            | Polandês        | pl            | pol            |
| Dinamarquês     | da            | dan            | Português (Br)  | pt-br         | por            |
| Holandês        | nl            | dut            | Português (Pt)  | pt            | por            |
| Inglês          | en            | eng            | Romeno          | ro            | rum            |
| Filipino        | tl            | fil            | Russo           | ru            | rus            |
| Finlandês       | fi            | fin            | Servo-Croata    | sh            | hrv            |
| Francês         | fr            | fre            | Espanhol (Es)   | es            | spa            |
| Alemão          | de            | ger            | Espanhol (LATAM)| es-la         | spa            |
| Grego           | el            | gre            | Sueco           | sv            | swe            |
| Hebraico        | he            | heb            | Tailandês       | th            | tha            |
| Hindi           | hi            | hin            | Turco           | tr            | tur            |
| Húngaro         | hu            | hun            | Ucraniano       | uk            | ukr            |
| Indonésio       | id            | ind            | Vietnamita      | vi            | vie            |

## Contribuição
- Tenha total certeza que não há nenhum pedido aberto igual antes do seu.
- Pull requests podem ser abertas tranquilamente se você achar necessário, mas por favor formate todo o código em Python Black nas configs padrão antes de realizar.
