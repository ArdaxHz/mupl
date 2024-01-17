# mupl - MangaDex Bulk Uploader
Realiza uploads em massa de pastas e arquivos zip (.zip/.cbz) para o MangaDex de maneira rápida e fácil.

Leia isso em outros idiomas:
[Idiomas](/readme.md)

## Sumário
- [Como usar](#como-usar)
  - [Argumentos da Linha de Comando](#argumentos-da-linha-de-comando)
- [Formato do Nome do Arquivo](#formato-do-nome-do-arquivo)
  - [Formato do Nome](#formato-do-nome)
  - [Parâmetros do Nome](#parâmetros-do-nome)
  - [Formatos de Imagem Aceitos](#formatos-de-imagem-aceitos)
- [Configuração](#configuração)
  - [Opções do Usuário](#ppções)
  - [Credenciais do MangaDex](#credenciais)
  - [Caminhos do Programa](#paths)
- [Mapa de Nome para ID](#mapa-de-nome-para-id)
  - [Exemplos de Arquivo de Mapeamento](#exemplo)
- [Contribuição](#contribuição)
- [Tradução](#tradução)


## Como usar
Baixe a [última versão](https://github.com/OneDefauter/mupl/releases/latest) (o arquivo zip do código-fonte) da página de releases, descompacte o arquivo em uma pasta e abra um terminal nessa localização.

No terminal (bash, powershell, cmd), digite `python mupl.py` para executar o uploader.
Certifique-se de ter o Python 3.9+ instalado, use `python` para o Windows e `python3` para o macOS e Linux.

### Argumentos da Linha de Comando
Existem argumentos da linha de comando que podem ser adicionados após o comando principal para alterar o comportamento do programa, por exemplo: `python mupl.py -u`.

##### Opções:
- `--update` `-u` Não verifica se há uma nova atualização no início do programa.
- `--verbose` `-v` Torna as mensagens e logs da linha de comando mais detalhados.

## Formato do Nome do Arquivo
#### Formato do Nome
`titulo_do_manga [idioma] - cXXX (vYY) (titulo_do_capitulo) {data_de_publicacao} [grupo]`

#### Parâmetros do Nome
- `titulo_do_manga` Título do manga (mesmo que a chave em `name_id_map.json`) ou o ID do MangaDex.
- `[idioma]` Código de idioma no formato ISO. *Omitido para o inglês.*
- `cXXX` Número do capítulo. *Omita o prefixo do capítulo se o capítulo for único, por exemplo, `cXXX` > `XXX`.*
- `(vYY)` Volume do capítulo. *Opcional.*
- `(titulo_do_capitulo)` Título do capítulo. Use `{question_mark}` no lugar onde haveria um `?`. *Opcional.*
- `{data_de_publicacao}` Data futura de lançamento do capítulo pelo lado do MangaDex. ***DEVE** estar no formato `AAAA-MM-DDTHH-MM-SS` se incluído.* *Opcional.*
- `[grupo]` Lista de nomes ou IDs de grupos. Se forem nomes de grupos, eles devem estar incluídos no `name_id_map.json` para os IDs. *Separe vários grupos usando `+`.* *Opcional.*

#### Formato em Pasta
- `Linguagem`
  - `Obra`
    - `Grupo`
      - `Volume`
        - `Capítulo`
          - `Título {data}`
      - `Capítulo`
        - `Título {data}`

#### Parâmetros do Formato Pasta
- `Linguagem` Código de idioma no formato ISO. *Obrigatório*
- `Obra` Título do manga (mesmo que a chave em `name_id_map.json`) ou o ID do MangaDex.
- `Grupo` Lista de nomes ou IDs de grupos. Se forem nomes de grupos, eles devem estar incluídos no `name_id_map.json` para os IDs. *Separe vários grupos usando `+`.* *Deixe como 0 (zero) para caso seja sem grupo.*
- `Volume` Volume do capítulo. *Opcional.* *Exemplo: v5*
- `Capítulo` Número do capítulo.
- `Título {data}` Em *Título* coloque o título do capítulo, em *{data}* coloque um tempo máximo de duas semanas. *Mantenha as chaves {}*

##### Exemplo de {data}
A data pode ser definida de algumas formas diferentes.
**{1d}** == Daqui 1 dia

**{5h}** == Daqui 5 horas

**{40m}** == Daqui 40 minutos

**{30s}** ==  Daqui 30 segundos

Ou da forma comum.
**{2024-01-16 22-00-00}**

Você pode juntar também.
**{1d 5h 40m 30s}** == Daqui 1 dia, 5 horas, 40 minutos e 30 segundos

Não precisa se preocupar com a ordem.
**{30s 5h 1d 40m}**

Não deixe os valores juntos, se não não vai funcionar.
**{1d5h40m30s}**





#### Formatos de Imagem Aceitos
- `png`
- `jpg`/`jpeg`
- `gif`
- `webp` *Será convertido para `png`, `jpg` ou `gif` durante o processo de upload.*

## Configuração
Configurações alteráveis pelo usuário estão disponíveis no arquivo `config.json`. É também onde você insere suas credenciais do MangaDex.
Copie e remova o `.example` de `config.json.example` para começar a usar o arquivo de configuração.

*Observação: os valores JSON não podem estar vazios, portanto, use (`null`) onde um valor deve estar vazio, uma string (`"usuário"`) para valores de string ou um dígito (`1`) para valores numéricos.*

#### Opções
- `number_of_images_upload` Número de imagens a serem carregadas de uma vez. *Padrão: 10*
- `upload_retry` Tentativas de reenvio de upload de imagem ou capítulo. *Padrão: 3*
- `ratelimit_time` Tempo (em segundos) para dormir após chamadas de API. *Padrão: 2*
- `max_log_days` Dias para manter logs. *Padrão: 30*
- `group_fallback_id` ID do grupo a ser usado se não encontrado no arquivo ou mapa de ID, deixe em branco para não carregar para um grupo. *Padrão: null*
- `number_threads`: Número de threads para upload simultâneo de imagens. **Isso pode limitar a taxa de upload.** As threads são limitadas ao intervalo de 1 a 3 (inclusive). *Padrão: 3*
- `language`: Idioma para mensagens da linha de comando. *Padrão: null*

#### Credenciais
***Esses valores não podem estar vazios, caso contrário, o uploader não será executado.***
- `mangadex_username` Nome de usuário do MangaDex.
- `mangadex_password` Senha do MangaDex.
- `client_id` ID do cliente para o Cliente da API MangaDex.
- `client_secret` Segredo do cliente para o Cliente da API MangaDex.

#### Paths
*Essas opções podem ser deixadas como estão, não precisam ser alteradas.*
- `name_id_map_file` Nome do arquivo para o mapa de nome para ID. *Padrão: name_id_map.json*
- `uploads_folder` Diretório para obter novos uploads. *Padrão: to_upload*
- `uploaded_files` Diretório para mover capítulos carregados. *Padrão: uploaded*
- `mangadex_api_url` URL da API MangaDex. *Padrão: https://api.mangadex.org*
- `mangadex_auth_url` URL de Autenticação MangaDex. *Padrão: https://auth.mangadex.org/realms/mangadex/protocol/openid-connect*
- `mdauth_path` Arquivo de salvamento local para o token de login do MangaDex. *Padrão: .mdauth*

<details>
  <summary>Como obter um ID e segredo de cliente.</summary>

  ![uma captura de tela do mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_1.png?raw=true)
  ![uma captura de tela do mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_2.png?raw=true)
</details>
<br />


## Mapa de Nome para ID
O `name_id_map.json` tem o seguinte formato:
```json
{
    "manga": {
        "hyakkano": "efb4278c-a761-406b-9d69-19603c5e4c8b"
    },
    "group": {
        "XuN": "b6d57ade-cab7-4be7-b2b8-be68484b3ad3"
    }
}
```
`manga` e `group` contêm o mapa de nome para ID para o manga a ser carregado e o grupo a ser carregado, respectivamente. O nome deve ser o mesmo que o nome do arquivo de upload. Para evitar problemas potenciais ao carregar, tente usar um nome que seja em minúsculas e sem espaços.

Cada novo par de nome-ID deve ser separado por uma vírgula no final da linha e dois pontos entre o nome e o ID. O último par de cada mapa não deve ter uma vírgula.

#### Exemplo

Suponha que eu queira carregar o capítulo `hyakkano - c025 (v04) [XuN].cbz`. No meu `name_id_map.json`, eu teria a chave `hyakkano` e o valor `efb4278c-a761-406b-9d69-19603c5e4c8b` para o ID do manga a ser carregado. Eu também teria `XuN` para o mapa de grupo com o valor `b6d57ade-cab7-4be7-b2b8-be68484b3ad3`.

O programa então procuraria por essa chave no arquivo para o `hyakkano` e para a chave `XuN` para seus IDs atribuídos.

Se eu tiver um arquivo chamado `efb4278c-a761-406b-9d69-19603c5e4c8b [spa] - 000 (Momi-san) [XuN+00e03853-1b96-4f41-9542-c71b8692033b]`, o programa pegaria o ID do manga diretamente do arquivo, o idioma como espanhol com o código `es`, número do capítulo como nulo (capítulo único) sem volume, título do capítulo como `Momi-san` com os grupos `XuN` (ID retirado de `name_id_map.json`) e `00e03853-1b96-4f41-9542-c71b8692033b`.


## Contribuição
- Certifique-se de que não há problemas duplicados abertos antes de abrir um
- Pull requests são livres para serem abertos se você achar necessário, mas formate qualquer código com o Python Black (configurações padrão) antes de fazê-lo.

## Tradução
Existem dois arquivos para traduzir, este documento e o arquivo [/mupl/loc/en.json](/mupl/loc/en.json).

O documento traduzido deve ser colocado em [/doc/](/doc/) com o nome `Doc.<>.md` com o código de idioma ISO entre os pontos, por exemplo: `Doc.pt-br.md`.

O arquivo json traduzido deve ter o nome `<>.json` com o código de idioma ISO sendo usado e colocado dentro do diretório [/mupl/loc/](/mupl/loc/).

Por favor, envie um PR com essas alterações.