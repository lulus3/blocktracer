# BlockTracer

O **BlockTracer** é uma aplicação de rastreabilidade e autenticação de produtos eletrônicos. Fabricantes autorizados registram produtos na blockchain local; distribuidores e lojas podem registrar a transferência de custódia; consumidores consultam o produto por ID ou QR Code.

Este é um projeto acadêmico da disciplina **Oficina de Desenvolvimento de Sistemas 3**, criado para aplicar blockchain, contratos inteligentes e integração de uma aplicação web com uma rede Ethereum local.

## Problema e justificativa

Carregadores, baterias e acessórios falsificados podem usar a aparência de uma marca legítima, sem possuir origem verificável. Registros guardados apenas por uma empresa podem ser alterados, perdidos ou contestados.

O BlockTracer usa blockchain para registrar uma fonte auditável de origem e movimentação. Cada ação relevante gera uma transação confirmada por uma rede local, com data, conta responsável e histórico verificável.

> A blockchain prova a existência do registro digital. Em um cenário real, o QR Code também deve ser protegido por selo inviolável, NFC ou serial gravado no item para reduzir cópias físicas.

## Funcionalidades e regras de negócio

- somente fabricantes autorizados registram produtos;
- o ID de produto é único e não pode ser cadastrado duas vezes;
- cada cadastro gera QR Code para consulta;
- cada QR Code pode ser salvo em bucket privado do MinIO e exibido na listagem por link temporário;
- a tela de consulta lista os produtos registrados e permite pesquisar por nome, lote, fabricante ou ID;
- a carteira ativa pode ser trocada pela interface para demonstrar os diferentes perfis locais;
- o administrador vincula cada carteira a um participante identificado por nome e organização;
- qualquer pessoa pode autenticar por ID/QR Code e consultar produto, status, origem e histórico de custódia na mesma tela;
- apenas o custodiante atual transfere o produto para outro custodiante autorizado;
- o administrador ou fabricante pode recolher um produto;
- um produto recolhido não pode ser transferido;
- a interface mostra blocos, hashes e transações da rede local.

## Dados on-chain

O contrato armazena o ID do produto, nome, lote, data/local de fabricação, fabricante, descrição, carteiras responsáveis, data de registro, status e histórico de custódia. Também armazena o nome e a organização vinculados a cada carteira participante. O QR Code contém somente o ID de consulta.

## Tecnologias

- Solidity;
- Python e Streamlit;
- Web3.py;
- Ganache em Docker como blockchain Ethereum local;
- Docker Compose para compilação e deploy;
- QR Code e Pyzbar para geração e leitura.

## Como executar

### 1. Inicie a blockchain local

Com Docker Desktop aberto, na raiz do projeto:

```powershell
docker compose up -d ganache
docker compose logs -f ganache
```

A rede ficará disponível em `http://127.0.0.1:8545`, com `chainId` `1337` e dez contas de teste. O volume `ganache-data` preserva os dados entre reinicializações normais.

### 2. Compile e publique o contrato pelo Docker (recomendado)

O projeto inclui dois serviços temporários: `compiler`, que usa a imagem oficial do Solidity, e `deployer`, que publica diretamente no Ganache e atualiza `CONTRACT_ADDRESS` no `.env`. Eles habilitam otimização e `viaIR`, necessários para este contrato. Não é necessário instalar Solidity, Python ou usar o Remix.

Antes da primeira publicação, crie o `.env` a partir do modelo e informe uma chave privada de uma das contas de teste do Ganache:

```powershell
Copy-Item .env.example .env
```

Depois execute, sempre na raiz do projeto:

```powershell
docker compose --profile tools run --rm compiler
docker compose --profile tools run --build --rm deployer
docker compose up -d --build app
docker compose up -d --build verifier
```

O `compiler` lê o caminho `CONTRACT_SOURCE_PATH` do `.env`. O padrão já aponta para `/sources/ProductOriginChain.sol`, que é o arquivo do contrato dentro do container. O `deployer` grava o endereço recém-publicado no `.env`, e a interface fica em `http://localhost:8501`.

### Verificação pelo celular

O serviço `verifier` é uma interface de consulta sem carteiras ou funções de escrita. Ele usa a câmera do navegador para ler o QR Code e fica disponível na porta `8502`. Com o celular e o computador na mesma rede Wi-Fi, abra no celular `http://IP-DO-COMPUTADOR:8502` — por exemplo, `http://192.168.0.15:8502`.

No Windows, execute `ipconfig` para descobrir o IPv4 do computador e permita o acesso à rede privada caso o firewall solicite. A interface principal continua limitada a `localhost:8501`; não exponha as ações administrativas do Ganache para a rede local.

### Armazenamento dos QR Codes no MinIO

O envio ao MinIO é opcional: se as variáveis abaixo estiverem preenchidas, cada QR Code gerado após o registro será enviado ao bucket privado. A tela **Consultar produtos** gera uma URL assinada temporária para exibir a imagem, sem tornar o bucket público.

```env
MINIO_ENDPOINT=https://storage.thinktedlab.org
MINIO_ACCESS_KEY=blockchain-app
MINIO_SECRET_KEY=sua_chave_secreta
MINIO_BUCKET=blockchain
MINIO_REGION=us-east-1
MINIO_QR_PREFIX=qrcodes
```

Após atualizar o `.env`, reconstrua a interface principal:

```powershell
docker compose up -d --build app
```

O usuário precisa ter permissão `s3:PutObject` e `s3:GetObject` para o prefixo `qrcodes/` do bucket `blockchain`. QR Codes gerados antes dessa configuração permanecem apenas no download local e não terão imagem remota.

### Carteiras e perfis no Ganache

A barra lateral tem um seletor de carteira. Ele lista somente as dez contas locais desbloqueadas do Ganache e muda a conta usada na sessão atual do navegador. O contrato define se a carteira é Administrador, Fabricante, Custodiante ou Consultor; não existe uma permissão apenas visual na interface.

Esse modo dispensa chave privada na interface — o serviço `app` recebe apenas a URL da rede e o endereço do contrato. A `PRIVATE_KEY` no `.env` continua necessária exclusivamente para o serviço `deployer`. Contas desbloqueadas só são apropriadas para esta rede local, exposta em `127.0.0.1`; em uma blockchain real, a assinatura deve ser feita por uma carteira como MetaMask.

Quando o contrato mudar, rode novamente os dois primeiros comandos e reinicie a interface:

```powershell
docker compose restart app
```

### Alternativa: compile e publique pelo Remix

No Remix IDE:

1. Abra `ProductOriginChain.sol`.
2. Escolha o compilador `0.8.24`.
3. Em **Advanced Configurations**, selecione **EVM Version: Shanghai** e habilite **Optimization**. O contrato foi dividido em consultas menores e não exige `viaIR`.
4. Em **Deploy & Run**, conecte ao Ganache em `http://127.0.0.1:8545`.
5. Faça o deploy de `ProductsOriginChain`.
6. Copie o endereço em **Deployed Contracts**.

> Sempre que `ProductOriginChain.sol` for alterado, publique uma nova versão e atualize o endereço abaixo.

### 3. Configure as variáveis

Copie o modelo e preencha com uma chave de teste exibida no log do Ganache:

```powershell
Copy-Item .env.example .env
```

```env
PRIVATE_KEY=0xchave_privada_de_teste
PROVIDER_URL=http://127.0.0.1:8545
CONTRACT_ADDRESS=0xendereco_do_novo_contrato
CONTRACT_SOURCE_PATH=/sources/ProductOriginChain.sol
```

Não publique o arquivo `.env`.

### 4. Alternativa local para a interface

O fluxo recomendado já sobe a interface pelo serviço `app`. Caso queira executá-la fora do Docker, use:
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\streamlit.exe run app.py
```

Abra o endereço informado pelo Streamlit, normalmente `http://localhost:8501`.

## Testes

Depois do deploy e da configuração do `.env`, execute:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes cobrem consulta inexistente, registro válido, rejeição de ID duplicado e rejeição de cadastro por conta não autorizada.

## Roteiro de demonstração

1. Mostrar o container Ganache em execução e a tela Blockchain da aplicação.
2. Registrar um produto por uma carteira fabricante autorizada.
3. Mostrar hash, bloco e QR Code gerados.
4. Consultar o QR Code e exibir o produto registrado.
5. Mostrar histórico de custódia ou transferência para uma conta autorizada.
6. Tentar cadastrar o mesmo ID ou usar uma conta não autorizada e mostrar a transação rejeitada.
