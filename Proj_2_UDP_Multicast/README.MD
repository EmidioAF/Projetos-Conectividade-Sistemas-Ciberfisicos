# Projeto 2 - Conectividade de Aplicações

## Descrição
Este projeto simula um sistema de atualização de firmware para dispositivos IoT usando **UDP Multicast**.
Um servidor central transmite mensagens no formato `ATUALIZAÇÃO N` para um grupo multicast, e todos os clientes inscritos no grupo recebem a mensagem simultaneamente — sem que o servidor precise gerenciar conexões individuais.

## Requisitos
- Python 3 instalado
- Rede com suporte a multicast (funciona normalmente em loopback/localhost)

## Estrutura dos arquivos
- `servidor.py` — transmite atualizações para o grupo multicast
- `cliente.py` — dispositivo IoT que se inscreve no grupo e recebe as atualizações
- `README.md` — instruções do projeto
- `relatorio.md` — relatório em formato Markdown

## Configuração Multicast
| Parâmetro       | Valor       |
|-----------------|-------------|
| Grupo Multicast | `224.1.1.1` |
| Porta           | `5000`      |
| TTL             | `2`         |

## Como executar

### 1. Iniciar um ou mais clientes
Em terminais separados, execute o cliente em cada um:
```
python cliente.py
```
Informe o nome do dispositivo quando solicitado.

### 2. Iniciar o servidor
```
python servidor.py
```

### 3. Enviar atualizações
No terminal do servidor, pressione `Enter` para transmitir:
- `ATUALIZAÇÃO 1`
- `ATUALIZAÇÃO 2`
- `ATUALIZAÇÃO 3`
e assim por diante.

### 4. Encerrar
- No cliente, digite `sair`
- No servidor, digite `sair`

## Diferenças em relação à versão TCP

| Aspecto               | TCP (versão anterior)         | UDP Multicast (versão atual)           |
|-----------------------|-------------------------------|----------------------------------------|
| Tipo de socket        | `SOCK_STREAM`                 | `SOCK_DGRAM`                           |
| Conexão              | `connect()` / `accept()`      | Não há — clientes entram no grupo      |
| Envio                | `sendall()` para cada cliente | `sendto()` uma vez para o grupo        |
| Rastreamento clientes | Lista de sockets gerenciada   | Desnecessário — multicast é nativo     |
| Garantia de entrega   | Sim (TCP)                     | Não (UDP — melhor esforço)             |
| Escalabilidade        | Limitada por threads          | Alta — N clientes, 1 envio no servidor |

## Observações
- Múltiplos clientes podem entrar e sair do grupo sem qualquer alteração no servidor.
- O servidor não sabe quantos clientes estão escutando — ele simplesmente transmite.
- Para testes em máquinas diferentes na mesma rede, certifique-se de que o roteador/switch suporta IGMP (Internet Group Management Protocol).
