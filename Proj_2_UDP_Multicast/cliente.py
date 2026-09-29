import socket
import struct
import threading

# ─── Configuração ──────────────────────────────────────────────────────────────
MULTICAST_GROUP = "224.1.1.1"   # Mesmo grupo que o servidor
MCAST_PORT      = 5000          # Porta de recepção de atualizações
SERVER_HOST     = "127.0.0.1"   # IP do servidor (altere para rede real)
REG_PORT        = 5001          # Porta de registro no servidor
# ──────────────────────────────────────────────────────────────────────────────


def receber_mensagens(sock_rx):
    """Loop de recepção — roda em thread separada."""
    try:
        while True:
            dados, addr = sock_rx.recvfrom(1024)
            mensagem = dados.decode("utf-8")
            print(f"\n[RECEBIDO de {addr[0]}] {mensagem}")
            print(">> ", end="", flush=True)
    except OSError:
        pass   # socket fechado pelo main thread
    except Exception as e:
        print(f"\n[ERRO recepção] {e}")


def iniciar_cliente():
    nome = input("Digite o nome do dispositivo: ").strip()
    if not nome:
        nome = "dispositivo_sem_nome"

    # ── Socket multicast (receber atualizações) ──────────────────────────────
    sock_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock_rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_rx.bind(("", MCAST_PORT))

    group = socket.inet_aton(MULTICAST_GROUP)
    mreq  = struct.pack("4sL", group, socket.INADDR_ANY)
    sock_rx.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # ── Socket de registro (unicast → servidor) ──────────────────────────────
    sock_reg = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Anunciar entrada ao servidor
    sock_reg.sendto(
        f"REGISTRO:{nome}".encode("utf-8"),
        (SERVER_HOST, REG_PORT)
    )

    print(f"[CONECTADO] Dispositivo '{nome}' inscrito no grupo "
          f"{MULTICAST_GROUP}:{MCAST_PORT}")
    print(f"[INFO] Registro enviado para {SERVER_HOST}:{REG_PORT}")
    print("Aguardando atualizações... (digite 'sair' para encerrar)\n")

    thread_rx = threading.Thread(
        target=receber_mensagens, args=(sock_rx,), daemon=True
    )
    thread_rx.start()

    try:
        while True:
            print(">> ", end="", flush=True)
            comando = input().strip().lower()
            if comando == "sair":
                # Anunciar saída ao servidor antes de fechar
                sock_reg.sendto(
                    f"SAIDA:{nome}".encode("utf-8"),
                    (SERVER_HOST, REG_PORT)
                )
                print(f"[ENCERRANDO] Dispositivo '{nome}' saindo do grupo multicast.")
                break
    finally:
        try:
            sock_rx.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
        except Exception:
            pass
        sock_rx.close()
        sock_reg.close()


if __name__ == "__main__":
    iniciar_cliente()
