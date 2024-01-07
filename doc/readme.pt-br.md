# mupl - MangaDex Carregador em Massa
Carrega pastas e arquivos zipados (.zip/.cbz) para o MangaDex de maneira rápida e fácil.

Leia isso em outros idiomas:
[Português](doc/readme.pt-br.md)

## Sumário
- [Como usar](#uso)
  - [Argumentos de Linha de Comando](#argumentos-de-linha-de-comando)
- [Formato do Nome do Arquivo](#formato-do-nome-do-arquivo)
  - [Formato do Nome](#formato-do-nome)
  - [Parâmetros do Nome](#parâmetros-do-nome)
  - [Formatos de Imagem Aceitos](#formatos-de-imagem-aceitos)
- [Configuração](#configuracao)
  - [Opções do Usuário](#opcoes-do-usuario)
  - [Credenciais do MangaDex](#credenciais-do-mangadex)
  - [Caminhos do Programa](#caminhos-do-programa)
- [Mapeamento de Nome para ID](#mapeamento-de-nome-para-id)
  - [Exemplos de Arquivo de Mapeamento](#exemplo)
- [Contribuição](#contribuicao)
- [Tradução](#traducao)

## Uso
Em um terminal (bash, powershell, cmd), digite `python mupl.py` para executar o carregador.
Use `python` no Windows e `python3` no macOS e Linux.

### Argumentos de Linha de Comando
Existem argumentos de linha de comando que podem ser adicionados após o comando principal para alterar o comportamento do programa, por exemplo: `python mupl.py -u`.

##### Opções:
- `--update` `-u` Não verifica uma nova atualização no início do programa.
- `--verbose` `-v` Torna as mensagens e logs da linha de comando mais verbosos.

## Formato do Nome do Arquivo
#### Formato do Nome
`titulo_do_manga [idioma] - cXXX (vYY) (titulo_do_capitulo) {data_de_publicacao} [grupo]`

#### Parâmetros do Nome
- `titulo_do_manga` Título do manga (mesmo que a chave em `name_id_map.json`) ou ID do MangaDex.
- `[idioma]` Código de idioma no formato ISO. *Omitido para inglês.*
- `cXXX` Número do capítulo. *Omita o prefixo do capítulo se o capítulo for único, por exemplo, `cXXX` > `XXX`.*
- `(vYY)` Volume do capítulo. *Opcional.*
- `(titulo_do_capitulo)` Título do capítulo. Use `{ponto_de_interrogacao}` no lugar onde houver um `?`. *Opcional.*
- `{data_de_publicacao}` Data futura de lançamento do capítulo pelo lado do MangaDex. ***DEVE** estar no formato `AAAA-MM-DDTHH-MM-SS` se incluído.* *Opcional.*
- `[grupo]` Lista de nomes ou IDs de grupos. Se usar nomes de grupos, eles devem estar incluídos no `name_id_map.json` para os IDs. *Separe vários grupos usando `+`.* *Opcional.*

#### Formatos de Imagem Aceitos
- `png`
- `jpg`/`jpeg`
- `gif`
- `webp` *Será convertido para `png`, `jpg` ou `gif` durante o processo de upload.*

## Configuração
As configurações alteráveis pelo usuário estão disponíveis no arquivo `config.json`. É também onde você coloca suas credenciais do MangaDex.
Copie e remova o `.example` de `config.json.example` para começar a usar o arquivo de configuração.

*Nota: Os valores JSON não podem ser vazios, portanto, use (`null`) onde um valor deve estar vazio, uma string (`"username"`) para valores de string ou um dígito (`1`) para valores numéricos.*

#### Opções
- `number_of_images_upload` Número de imagens para carregar de uma vez. *Padrão: 10*
- `upload_retry` Tentativas de repetir o upload de imagem ou capítulo. *Padrão: 3*
- `ratelimit_time` Tempo (em segundos) para esperar após chamadas à API. *Padrão: 2*
- `max_log_days` Dias para manter os logs. *Padrão: 30*
- `group_fallback_id` ID do grupo a ser usado se não encontrado no arquivo ou mapeamento de ID, deixe em branco para não carregar para um grupo. *Padrão: null*
- `number_threads`: Número de threads para upload concorrente de imagens. **Isso pode limitar a taxa de upload.** As threads são limitadas ao intervalo de 1 a 3 (inclusive). *Padrão: 3*
- `language`: Idioma para mensagens na linha de comando. *Padrão: null*

#### Credenciais
***Esses valores não podem ser vazios, caso contrário, o carregador não será executado.***
- `mangadex_username` Nome de usuário do MangaDex.
- `mangadex_password` Senha do MangaDex.
- `client_id` ID do Cliente para o Cliente da API do MangaDex.
- `client_secret` Segredo do Cliente para o Cliente da API do MangaDex.

#### Caminhos
*Essas opções podem ser mantidas como estão, não precisam ser alteradas.*
- `name_id_map_file` Nome do arquivo para o mapeamento de nome para ID. *Padrão: name_id_map.json*
- `uploads_folder` Diretório para obter novos uploads. *Padrão: to_upload*
- `uploaded_files` Diretório para mover capítulos carregados. *Padrão: uploaded*
- `mangadex_api_url` URL da API do MangaDex. *Padrão: https://api.mangadex.org*
- `mangadex_auth_url` URL de Autenticação do MangaDex. *Padrão: https://auth.mangadex.org/realms/mangadex/protocol/openid-connect*
- `mdauth_path` Arquivo de salvamento local para o token de login do MangaDex. *Padrão: .mdauth*

<details>
  <summary>Como obter um ID de cliente e segredo.</summary>

  ![a screenshot of the mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_1.png?raw=true)
  ![a screenshot of the mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_2.png?raw=true)

angadex-mass-uploader/blob/main/assets/usage_2.png?raw=true)
</details>
<br />

## Mapeamento de Nome para ID
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
`manga` e `group` contêm o mapeamento de nome para ID para o manga a ser carregado e o grupo a ser carregado, respectivamente. O nome deve ser o mesmo do arquivo de upload. Para evitar problemas potenciais ao fazer upload, tente usar um nome em minúsculas e sem espaços.

Cada novo par nome-ID deve ser separado por uma vírgula no final da linha e dois pontos entre o nome e o ID. O último par de cada mapa não deve ter uma vírgula.

#### Exemplo

Suponha que eu queira carregar o capítulo `hyakkano - c025 (v04) [XuN].cbz`. No meu `name_id_map.json`, eu teria a chave `hyakkano` e o valor `efb4278c-a761-406b-9d69-19603c5e4c8b` para o ID do manga a ser carregado. Eu também teria `XuN` para o mapeamento de grupo com o valor `b6d57ade-cab7-4be7-b2b8-be68484b3ad3`.

O programa então procuraria por essa chave no arquivo para `hyakkano` e para a chave `XuN` para seus IDs atribuídos.

Se eu tiver um arquivo chamado `efb4278c-a761-406b-9d69-19603c5e4c8b [spa] - 000 (Momi-san) [XuN+00e03853-1b96-4f41-9542-c71b8692033b]`, o programa pegaria o ID do manga diretamente do arquivo, o idioma como espanhol com o código `es`, o número do capítulo como nulo (capítulo único) sem volume, o título do capítulo como `Momi-san` com os grupos `XuN` (ID retirado do `name_id_map.json`) e `00e03853-1b96-4f41-9542-c71b8692033b`. 

## Contribuição
- Certifique-se de que não há problemas duplicados abertos antes de abrir um novo
- Pull requests estão livres para serem abertos se você achar necessário, mas formate qualquer código com o Python Black (configurações padrão) antes de fazê-lo.

## Tradução
Existem dois arquivos para traduzir, este readme e o arquivo [/mupl/loc/en.json](/mupl/loc/en.json).

O readme traduzido deve ser colocado em [/doc/](/doc/) com o nome `readme.<>.md` e o código ISO do idioma entre os pontos, por exemplo: `readme.pt-br.md`.

O arquivo JSON traduzido deve ter o nome `<>.json` com o código ISO do idioma sendo usado e colocado dentro do diretório [/mupl/loc/](/mupl/loc/).

Por favor, envie um PR com essas alterações.