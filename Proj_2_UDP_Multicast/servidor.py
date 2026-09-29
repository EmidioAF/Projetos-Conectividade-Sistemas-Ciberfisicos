import socket
import struct
import threading

# ─── Configuração Multicast ────────────────────────────────────────────────────
MULTICAST_GROUP = "224.1.1.1"   # Endereço do grupo multicast
MCAST_PORT      = 5000          # Porta de envio de atualizações
REG_PORT        = 5001          # Porta de registro/saída dos clientes (unicast)
TTL             = 2             # Número de saltos (hops)
TRIGGER         = 5             # Nº de clientes para disparar atualização automática
# ──────────────────────────────────────────────────────────────────────────────

clientes_ativos = set()         # nomes dos dispositivos conectados
lock            = threading.Lock()
contador_atualizacao = 1


def enviar_atualizacao(sock_tx, origem="MANUAL"):
    """Transmite a próxima atualização para o grupo multicast."""
    global contador_atualizacao
    mensagem = f"ATUALIZAÇÃO {contador_atualizacao}"
    sock_tx.sendto(mensagem.encode("utf-8"), (MULTICAST_GROUP, MCAST_PORT))
    print(
        f"\n[ENVIO/{origem}] '{mensagem}' → grupo {MULTICAST_GROUP}:{MCAST_PORT} "
        f"({len(clientes_ativos)} cliente(s) ativo(s))"
    )
    contador_atualizacao += 1


def ouvir_registros(sock_reg, sock_tx):
    """
    Thread que escuta na REG_PORT por mensagens unicast dos clientes.
    Protocolos aceitos:
      REGISTRO:<nome>  → cliente entrou no grupo
      SAIDA:<nome>     → cliente saiu do grupo
    """
    while True:
        try:
            dados, addr = sock_reg.recvfrom(1024)
            msg = dados.decode("utf-8").strip()

            if msg.startswith("REGISTRO:"):
                nome = msg.split(":", 1)[1]
                with lock:
                    clientes_ativos.add(nome)
                    total = len(clientes_ativos)
                print(f"[+] '{nome}' conectou de {addr[0]}. "
                      f"Clientes ativos: {total}/{TRIGGER}")

                # Disparo automático a cada múltiplo de TRIGGER clientes
                if total % TRIGGER == 0:
                    print(f"[AUTO] {total} cliente(s) conectados — "
                          f"disparando atualização automática!")
                    with lock:
                        enviar_atualizacao(sock_tx, origem="AUTO")

            elif msg.startswith("SAIDA:"):
                nome = msg.split(":", 1)[1]
                with lock:
                    clientes_ativos.discard(nome)
                    total = len(clientes_ativos)
                print(f"[-] '{nome}' desconectou. Clientes ativos: {total}/{TRIGGER}")

        except OSError:
            break
        except Exception as e:
            print(f"[ERRO registro] {e}")


def iniciar_servidor():
    # Socket de transmissão multicast (envia atualizações)
    sock_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock_tx.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("b", TTL))

    # Socket de registro (recebe unicast dos clientes)
    sock_reg = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_reg.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_reg.bind(("0.0.0.0", REG_PORT))

    print("=" * 62)
    print("  SERVIDOR DE ATUALIZAÇÃO DE FIRMWARE (UDP Multicast)")
    print(f"  Grupo multicast  : {MULTICAST_GROUP}:{MCAST_PORT}  (TTL {TTL})")
    print(f"  Porta de registro: 0.0.0.0:{REG_PORT}")
    print(f"  Gatilho automático: a cada {TRIGGER} clientes conectados")
    print("  Pressione ENTER para enviar atualização manual.")
    print("  Digite 'sair' para encerrar.")
    print("=" * 62)

    # Thread de registro roda em paralelo ao loop principal
    thread_reg = threading.Thread(
        target=ouvir_registros, args=(sock_reg, sock_tx), daemon=True
    )
    thread_reg.start()

    try:
        while True:
            comando = input().strip().lower()

            if comando == "sair":
                print("[ENCERRANDO] Servidor finalizado.")
                break

            # Enter vazio ou qualquer outro texto → envio manual
            with lock:
                enviar_atualizacao(sock_tx, origem="MANUAL")

    finally:
        sock_reg.close()
        sock_tx.close()


if __name__ == "__main__":
    iniciar_servidor()
