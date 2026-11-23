# Quadro

Quadro digital **local**. Tem tarefas com checkbox, post-its, desenho em pixel, links entre itens,
seleção em grupo, zoom e navegação. O tema claro mantém o visual pixel art 1-bit (só preto e branco).
Roda só na sua máquina: o servidor escuta apenas em `127.0.0.1` e não acessa a internet.
O quadro abre no tema escuro. **Shift+D** (ou o botão de sol/lua na barra) volta ao claro, que continua preto e branco.
A escolha fica neste navegador. A cor gravada de cada traço não muda: no escuro, um traço preto só é desenhado claro na tela.

- Sem npm, sem bibliotecas, sem CDN e sem fontes externas. Só `index.html` (HTML/CSS/JS puro) e `servidor.py` (biblioteca padrão do Python 3).
- Os dados ficam em `quadro.json`, nesta pasta. A cada gravação o arquivo anterior vira `quadro.bak.json`.
- Não instala nada, não cria serviço nem tarefa agendada.

## Arquivos

| Arquivo | Para quê |
|---|---|
| `index.html` | A página do quadro (ícones e fonte de título desenhados em pixel dentro do próprio arquivo) |
| `servidor.py` | Servidor local e API JSON (Python 3, sem dependências) |
| `iniciar.bat` | Liga o servidor e abre o navegador (Windows) |
| `parar.bat` | Fecha a janela do servidor |
| `quadro.json` | Os dados do quadro |
| `quadro.bak.json` | Cópia da versão anterior (criada automaticamente) |
| `exemplo.json` | Um quadro de exemplo (padrões, links, URL e desenho) |
| `anexos/` | Arquivos anexados às tarefas e aos post-its (criada automaticamente) |

## Ligar e desligar

**Windows:** dê dois cliques em `iniciar.bat`. Abre uma janela preta (o servidor) e o navegador em
<http://127.0.0.1:8765>. Para desligar, aperte **Ctrl+C** na janela ou feche-a. O `parar.bat` também fecha a janela.

**Linha de comando (qualquer sistema):**

```
python servidor.py            # porta 8765
python servidor.py 9000       # outra porta
python servidor.py --abrir    # também abre o navegador
```

Para ver o exemplo: com o servidor desligado, copie `exemplo.json` por cima de `quadro.json`.

## Como usar

### Ferramentas (paleta à esquerda)

| Tecla | Ferramenta |
|---|---|
| **V** | Mover / selecionar |
| **H** | Modo mover (navegar o quadro). Toque de novo, ou **Esc**, para voltar à ferramenta anterior. O botão da mão na paleta fica destacado e o rodapé mostra *MODO MOVER (H)* |
| **P** | Caneta (desenho em pixel). **1–4** escolhem o tamanho do pixel (2, 4, 6 ou 8) |
| **E** | Borracha (apaga o desenho) |
| **L** | Link: arraste de um item até outro, ou clique no primeiro e depois no segundo |
| **T** / **N** | Nova tarefa / novo post-it no centro da tela |

### Seleção e edição

| Ação | Como |
|---|---|
| Criar | **Duplo clique** no fundo e escolha *Tarefa*, *Post-it* ou *Colar aqui* |
| Selecionar | Clique no item. No modo Mover, **arraste no vazio** para desenhar um retângulo: ele seleciona tudo que tocar (tarefas, post-its e traços) |
| Somar ou tirar da seleção | **Shift+clique** (ou Shift+arrastar o retângulo para somar) |
| Selecionar tudo | **Ctrl+A** (no Mac, Cmd) |
| Mover | Arraste qualquer item selecionado: o grupo inteiro vai junto, e os links acompanham |
| Empurrar | **Setas** (4 px) e **Shift+setas** (32 px) |
| Apagar | **Delete** ou **Backspace**. Apagar um item também apaga os links dele |
| Duplicar | **Ctrl+D** |
| Copiar / recortar / colar | **Ctrl+C**, **Ctrl+X**, **Ctrl+V** (cola onde está o mouse). Funciona só dentro do quadro |
| Desfazer / refazer | **Ctrl+Z**, **Ctrl+Shift+Z** ou **Ctrl+Y**. Cobre criar, editar, mover, grupos, padrões, links e desenho |
| Limpar seleção | **Esc** (sai do modo mover, cancela um link pela metade, ou limpa a seleção) |
| Editar texto | Duplo clique no texto. **Enter** confirma o título, **Shift+Enter** quebra a linha e **Esc** sai |
| Detalhes e coluna da tarefa | Duplo clique no corpo do cartão edita os detalhes. Duplo clique na etiqueta da barra edita a coluna |
| Rótulo do link | Duplo clique na linha ou no rótulo. Para apagar o link, clique na linha e aperte Delete |
| Concluir | Clique no checkbox: a tarefa fica riscada e pontilhada |
| Padrão (preenchimento) | Passe o mouse no item e use os quadradinhos, ou use a seção *Padrão* da paleta (vale para a seleção, ou para os próximos post-its se nada estiver selecionado) |
| URL | Passe o mouse no item e clique no ícone ↗ da barrinha. Aparece um ícone ↗ no item que abre o link numa nova aba (só http/https) |
| Editar texto | **Duplo clique** no título, nos detalhes ou no post-it. Também há um lápis na barrinha que aparece ao passar o mouse |
| Anexar | Na barrinha, o clipe abre o seletor de arquivos. Você também pode **arrastar um arquivo** em cima do cartão, ou **Ctrl+V** com uma imagem (com o cartão selecionado). Imagens aparecem em miniatura; outros arquivos, como um chip com o nome. Clique abre numa nova aba; o **×** remove (pede confirmação). Até 20 anexos por cartão, 50 MB cada. Ficam na pasta `anexos/` |
| Registro | Nas tarefas, o campo *O que foi feito?* (caixa tracejada) dá pra preencher a qualquer momento. Ao **marcar como concluída**, o campo abre sozinho depois da animação, pra anotar o que foi feito |
| Andamento | **+ andamento** anota o progresso da tarefa antes de concluir (e também depois). **Enter** salva, **Shift+Enter** quebra a linha e **Esc** cancela. O cartão mostra os últimos, com data `dd/mm HH:mm`; **+N** abre os mais antigos e *recolher* volta. Duplo clique edita uma linha; **×** apaga. Desfazer cobre essas mudanças |
| Subtarefas | **+ subtarefa** abre um campo no cartão. **Enter** adiciona e o campo continua aberto para a próxima; **Esc** sai. Várias linhas coladas viram várias subtarefas. Cada uma tem checkbox próprio (risca o texto) e o cartão mostra `2/3`. Duplo clique edita; **×** remove. Marcar todas não conclui a tarefa: o contador só fica verde. O checkbox do título continua sendo o que conclui |
| Navegar | **H** liga e desliga o modo mover (arraste com o botão esquerdo; toque H de novo ou Esc para sair). **Espaço+arrastar** navega só enquanto a tecla estiver apertada. Também dá com o botão do meio do mouse. No touch, use dois dedos. Enquanto você digita num campo, essas teclas não navegam |
| Zoom | Roda do mouse, **+**/**−**, **0** volta a 100% e **F** enquadra tudo. Ao soltar a roda (e ao apertar **H**) o texto é redesenhado nítido |
| Tema | **Shift+D**, ou o sol/lua na barra, alterna claro e escuro. O padrão é o escuro. Não mexe nos dados do quadro |

Tudo salva sozinho (cerca de 0,6 s depois da última mudança). A página consulta o servidor a cada 3 s
e, se nada mudou, não baixa o quadro de novo. Com a aba escondida essa consulta pausa, e volta ao
focar. O que os bots mudarem aparece sozinho. O status fica no canto superior direito.

## API (JSON)

Base: `http://127.0.0.1:8765`. Envie `Content-Type: application/json`.

| Método e rota | Corpo | Resposta |
|---|---|---|
| `GET /api/board` | – | Quadro inteiro + `rev` |
| `PUT /api/board` | `{"rev": "...", "board": {tasks, notes, strokes, links}}` | Troca o quadro inteiro (usado pela página). Se `rev` estiver velho, responde **409** com o quadro atual. Sem `rev`, sobrescreve direto. Links com ponta inexistente são descartados |
| `GET /api/tasks` | – | Lista de tarefas |
| `POST /api/tasks` | `{title, notes?, log?, history?, subtasks?, x?, y?, color?, done?, column?, url?, attachments?}` | **201** + tarefa criada |
| `GET /api/tasks/<id>` | – | Uma tarefa |
| `PATCH /api/tasks/<id>` | qualquer um de `title, notes, log, history, subtasks, x, y, color, done, column, url, attachments` | Tarefa atualizada. `history` ou `subtasks`, se vier, **substitui** a lista inteira. Sem `subtasks`, a lista que já estava fica |
| `DELETE /api/tasks/<id>` | – | `{"ok": true, "links_removidos": n}` (apaga os links dela) |
| `GET/POST /api/notes`, `GET/PATCH/DELETE /api/notes/<id>` | `{text?, x?, y?, color?, url?, rotation?, attachments?}` | Igual às tarefas |
| `POST /api/attachments?item=<id>&name=<arquivo>` | corpo cru do arquivo (`Content-Type` do tipo, opcional `X-Filename`) | **201** + `{id, name, file, mime, size, created_at}` e o anexo entra no item. Máx. 50 MB e 20 por item |
| `GET /api/attachments/<file>` | – | Baixa o arquivo. Imagens (exceto SVG) e PDF abrem no navegador (`inline`); HTML, SVG e o resto vêm como download (`attachment`). Sempre envia `X-Content-Type-Options: nosniff` |
| `DELETE /api/attachments/<id>` | – | Tira o anexo do cartão e apaga o arquivo se ninguém mais o citar |
| `GET /api/strokes` | – | Lista de traços |
| `POST /api/strokes` | `{points: [[x,y],...], width?, mode?}` ou uma lista deles | **201** + traço(s) |
| `DELETE /api/strokes/<id>` | – | Apaga um traço (e os links dele) |
| `DELETE /api/strokes` | – | Apaga todo o desenho (e os links que apontavam para traços) |
| `GET /api/links` | – | Lista de links |
| `POST /api/links` | `{from, to, label?}` | **201** + link criado. `from`/`to` precisam ser ids existentes de tarefa, nota ou traço, e diferentes entre si |
| `GET /api/links/<id>` | – | Um link |
| `PATCH /api/links/<id>` | `{label?, from?, to?}` | Link atualizado |
| `DELETE /api/links/<id>` | – | `{"ok": true}` |

Erros: **400** para JSON inválido ou campo errado (`{"erro": "..."}`), **404** para id ou rota inexistente,
**403** se o `Host` não for `127.0.0.1`/`localhost` (proteção contra DNS rebinding) ou se o `Origin` for de outro site.

### Exemplos com curl

```bash
curl http://127.0.0.1:8765/api/board

curl -X POST http://127.0.0.1:8765/api/tasks -H "Content-Type: application/json" \
     -d '{"title":"Pagar boleto","notes":"vence dia 25","color":"listras","column":"a fazer","url":"https://exemplo.com/boleto"}'

curl -X PATCH http://127.0.0.1:8765/api/tasks/t_1a2b3c4d5e -H "Content-Type: application/json" \
     -d '{"done":true,"column":"feito"}'

curl -X POST http://127.0.0.1:8765/api/notes -H "Content-Type: application/json" \
     -d '{"text":"Lembrar da reunião","color":"denso","x":500,"y":200}'

curl -X POST http://127.0.0.1:8765/api/links -H "Content-Type: application/json" \
     -d '{"from":"t_1a2b3c4d5e","to":"n_9f8e7d6c5b","label":"depende"}'

curl -X DELETE http://127.0.0.1:8765/api/links/l_0a1b2c3d4e

curl -X POST http://127.0.0.1:8765/api/strokes -H "Content-Type: application/json" \
     -d '{"points":[[100,100],[200,148],[300,100]],"width":4}'

curl -X DELETE http://127.0.0.1:8765/api/tasks/t_1a2b3c4d5e

# anexar um arquivo a uma tarefa ou post-it
curl -X POST "http://127.0.0.1:8765/api/attachments?item=t_1a2b3c4d5e&name=foto.png" \
     -H "Content-Type: image/png" --data-binary @foto.png

curl -OJ http://127.0.0.1:8765/api/attachments/a0123456789abcdef_foto.png

curl -X DELETE http://127.0.0.1:8765/api/attachments/a_1a2b3c4d5e
```

### Exemplos com PowerShell

```powershell
$B = "http://127.0.0.1:8765"
Invoke-RestMethod "$B/api/board"

Invoke-RestMethod -Method Post "$B/api/tasks" -ContentType "application/json; charset=utf-8" `
  -Body (@{ title = "Pagar boleto"; color = "listras"; column = "a fazer" } | ConvertTo-Json)

Invoke-RestMethod -Method Patch "$B/api/tasks/t_1a2b3c4d5e" -ContentType "application/json" `
  -Body '{"done": true}'

Invoke-RestMethod -Method Post "$B/api/links" -ContentType "application/json; charset=utf-8" `
  -Body (@{ from = "t_1a2b3c4d5e"; to = "n_9f8e7d6c5b"; label = "depende" } | ConvertTo-Json)

Invoke-RestMethod -Method Delete "$B/api/links/l_0a1b2c3d4e"
```

> No Windows PowerShell 5.1, texto com acento pode chegar errado. Se acontecer, envie o corpo em bytes UTF-8:
> `-Body ([Text.Encoding]::UTF8.GetBytes($json))`.

## Formato do `quadro.json`

```json
{
  "version": 1,
  "updated_at": "2026-11-19T17:00:00Z",
  "tasks": [
    {
      "id": "t_1a2b3c4d5e",
      "title": "Revisar PR",
      "notes": "detalhes opcionais",
      "x": 60, "y": 60,
      "color": "listras",
      "done": false,
      "column": "fazendo",
      "url": "https://github.com",
      "log": "Revisei e pedi dois ajustes",
      "history": [
        {"at": "2026-11-19T16:10:00.000Z", "text": "Li o diff"}
      ],
      "subtasks": [
        {"id": "st_a1b2c3d4e5", "text": "Ler o diff", "done": true, "at": "2026-11-19T16:00:00.000Z"},
        {"id": "st_f6e5d4c3b2", "text": "Pedir os ajustes", "done": false, "at": "2026-11-19T16:05:00.000Z"}
      ],
      "attachments": [
        {"id":"a_1a2b3c4d5e","name":"print.png","file":"a0123456789abcdef_print.png","mime":"image/png","size":1200,"created_at":"2026-11-19T17:00:00Z"}
      ],
      "created_at": "2026-11-19T17:00:00Z",
      "updated_at": "2026-11-19T17:00:00Z"
    }
  ],
  "notes": [
    {
      "id": "n_9f8e7d6c5b",
      "text": "Texto do post-it\ncom quebra de linha",
      "x": 704, "y": 60,
      "color": "pontilhado",
      "rotation": 0,
      "url": "",
      "created_at": "...", "updated_at": "..."
    }
  ],
  "strokes": [
    {
      "id": "s_1a2b3c4d5e",
      "color": "preto",
      "width": 4,
      "mode": "pen",
      "points": [[100, 100], [104, 104], [108, 104]],
      "created_at": "..."
    }
  ],
  "links": [
    {
      "id": "l_0a1b2c3d4e",
      "from": "t_1a2b3c4d5e",
      "to": "n_9f8e7d6c5b",
      "label": "depende",
      "created_at": "...", "updated_at": "..."
    }
  ]
}
```

| Campo | Regras |
|---|---|
| `id` | Texto único de até 40 caracteres. A API gera sozinha (`t_`, `n_`, `s_` ou `l_` + 10 hex) |
| `x`, `y` | Posição em pixels do canto superior esquerdo, em coordenadas do quadro (podem ser negativas). Cartão: 240 px de largura. Post-it: 184×184 px. A página encaixa as posições numa grade de 4 px |
| `color` | É o **padrão de preenchimento**: `branco`, `pontilhado`, `denso`, `listras` ou `preto`. Nomes antigos continuam valendo e viram padrão: `amarelo`/`verde`/`cinza` → pontilhado, `azul`/`roxo` → listras, `rosa`/`laranja` → denso, `vermelho` → preto. `#rrggbb` vira o padrão mais próximo do brilho |
| `title` | Obrigatório, até 500 caracteres. `notes`, `text` e `log` vão até 5000 caracteres. `column` vai até 60 (é uma etiqueta livre, por exemplo `a fazer`, `fazendo`, `feito`) |
| `log` | Opcional. Texto livre do registro *o que foi feito* na tarefa. Quadros antigos sem esse campo continuam carregando |
| `history` | Opcional. Lista de `{at, text}` com o andamento ao longo do caminho. `at` é ISO 8601 em UTC (`...Z`, com ou sem milissegundos) e `text` vai até 5000 caracteres. Até 200 itens; duplicata de `at`+texto é descartada. Sem o campo, vale lista vazia. Num conflito **409**, a página junta as duas listas e não perde uma linha que só exista de um lado |
| `subtasks` | Opcional. Lista de `{id, text, done, at}` dentro da tarefa. `text` vai até 500 caracteres, `done` é `true`/`false` e `at` é a criação em ISO 8601 UTC. Até 100 itens. Sem o campo, vale lista vazia (tarefas antigas continuam válidas). No `PATCH`, omitir `subtasks` mantém a lista. Num conflito **409**, a página une pelo `id`: o que só existe de um lado fica, e se os dois lados têm o mesmo `id` valem o `text` e o `done` locais |
| `done` | `true` ou `false` |
| `attachments` | Lista opcional (até 20) de `{id, name, file, mime, size, created_at}`. `file` é o nome salvo em `anexos/` (id aleatório + nome limpo). Quadros antigos sem o campo continuam carregando |
| `url` | Opcional. Vazio ou um endereço `http://`/`https://` de até 2000 caracteres |
| `rotation` | Graus, de −15 a 15. É guardado por compatibilidade, mas o visual pixel não inclina os post-its |
| `width` (traço) | Tamanho do pixel do traço, de 0,5 a 100 (a página usa 2, 4, 6 ou 8, e a borracha usa o triplo). Os pontos de um traço ficam encaixados numa grade desse tamanho, contada a partir do 1º ponto |
| `mode` | `pen` (caneta) ou `erase` (borracha, apaga o que foi desenhado antes dela) |
| `points` | Lista `[[x, y], ...]` com 1 a 20000 pontos. A página liga os pontos com linhas de pixels |
| `links.from` / `links.to` | Ids de tarefa, nota ou traço. A seta aponta para o `to`. `label` é opcional (até 200 caracteres) |
| Datas | ISO 8601 em UTC (`...Z`) |

A ordem das listas é a ordem de desenho: o último item fica por cima ao abrir a página.
Campos fora desta lista são descartados quando a página salva.

## Como os bots editam

**1. Com o servidor ligado (preferido): use a API HTTP.**
Ela valida os dados, gera `id` e `updated_at`, grava de forma atômica, apaga os links órfãos e a página mostra a mudança em até 3 s.
Exemplos:
- criar tarefa: `POST /api/tasks {"title": "..."}`
- concluir: `PATCH /api/tasks/<id> {"done": true}`
- registrar o que foi feito: `PATCH /api/tasks/<id> {"log": "…"}`
- andamento: leia a tarefa, acrescente `{at, text}` em `history` e mande a lista inteira no `PATCH` (o campo substitui o anterior)
- subtarefas: leia a tarefa, monte a lista `{id, text, done, at}` e mande em `subtasks` no `PATCH` (substitui a lista). Sem esse campo, as subtarefas que já estavam continuam. Concluir a tarefa (`done: true`) é independente de marcar as subtarefas
- anexar: `POST /api/attachments?item=<id>&name=arquivo.pdf` com o corpo cru do arquivo
- mover: `PATCH /api/tasks/<id> {"x": 400, "y": 120}`
- nota: `POST /api/notes {"text": "...", "color": "pontilhado"}`
- ligar dois itens: `POST /api/links {"from": "<id>", "to": "<id>", "label": "depende"}`

Para achar o `id`, leia `GET /api/board` e procure pelo título.

**2. Com o servidor desligado: edite o `quadro.json` direto.**
- Mantenha o formato acima e o JSON válido (UTF-8).
- Para um item novo, invente um `id` único (por exemplo `t_` + 10 caracteres hex) e preencha `created_at`/`updated_at`.
- Ao apagar um item, apague também os `links` que citam o id dele. Se esquecer, o servidor descarta esses links na próxima gravação da página e a página simplesmente não os desenha.
- Grave num arquivo temporário e depois renomeie por cima de `quadro.json`, pra não deixar o arquivo pela metade.
- Se o `quadro.json` quebrar, o servidor tenta carregar o `quadro.bak.json`.

Editar o arquivo com o servidor ligado também funciona, porque o servidor relê o arquivo a cada pedido. Mas, se a página
estiver aberta e salvando ao mesmo tempo, uma das mudanças pode se perder. Com o servidor ligado, prefira a API.

## Segurança

- O servidor escuta só em `127.0.0.1`, então outros computadores da rede não alcançam o quadro.
- Ele recusa pedidos com `Host` diferente de `127.0.0.1`/`localhost`, o que barra o DNS rebinding, e recusa `Origin` de outros sites.
- A página não carrega nada de fora: a CSP só permite recursos da própria página (`connect-src 'self'`, `img-src 'self' data:`).
  Clicar no ícone de URL apenas abre o endereço numa nova aba (`rel="noopener noreferrer"`), e só aceita http/https.
- Texto vindo de bots é mostrado como texto puro, nunca como HTML.
- Anexos ficam só na pasta local `anexos/`, com nome gerado (sem path traversal). HTML e SVG sempre baixam como arquivo, nunca abrem como página, e a resposta leva `X-Content-Type-Options: nosniff`.
- Não guarde senhas nem dados bancários no quadro: o `quadro.json` é um arquivo de texto comum, e os anexos são arquivos comuns na pasta.
