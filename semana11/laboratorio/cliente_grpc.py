"""
Cliente gRPC del servicio de juegos, semana 11.

Uso
  python cliente_grpc.py tabla
  python cliente_grpc.py unir ana
  python cliente_grpc.py anotar felipe 15 --reintentos 2

Variables
  SERVIDOR_HOST    (servidor)   SERVIDOR_PUERTO (50051)
  TIMEOUT_CLIENTE  (2)          deadline de cada intento, en segundos
  REINTENTOS       (0)          intentos extra ante DEADLINE_EXCEEDED o UNAVAILABLE

Cada reintento manda el MISMO id_solicitud.
"""
import argparse
import os
import uuid

import grpc

import servicio_pb2 as pb
import servicio_pb2_grpc as pb_grpc

HOST = os.getenv("SERVIDOR_HOST", "servidor")
PUERTO = os.getenv("SERVIDOR_PUERTO", "50051")
REINTENTABLES = {grpc.StatusCode.DEADLINE_EXCEEDED, grpc.StatusCode.UNAVAILABLE}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metodo", choices=["tabla", "unir", "anotar"])
    ap.add_argument("jugador", nargs="?", default="")
    ap.add_argument("puntos", nargs="?", type=int, default=0)
    ap.add_argument("--reintentos", type=int, default=int(os.getenv("REINTENTOS", "0")))
    ap.add_argument("--timeout", type=float, default=float(os.getenv("TIMEOUT_CLIENTE", "2")))
    a = ap.parse_args()

    canal = grpc.insecure_channel(f"{HOST}:{PUERTO}")
    stub = pb_grpc.PartidaStub(canal)        # el stub, generado desde el .proto

    if a.metodo == "tabla":
        llamada, solicitud = stub.Tabla, pb.TablaSolicitud()
    else:
        id_solicitud = uuid.uuid4().hex[:8]      # UNA vez, antes del primer intento
        if a.metodo == "unir":
            llamada, solicitud = stub.Unir, pb.UnirSolicitud(id_solicitud=id_solicitud, jugador=a.jugador)
        else:
            llamada, solicitud = stub.Anotar, pb.AnotarSolicitud(
                id_solicitud=id_solicitud, jugador=a.jugador, puntos=a.puntos)

    for intento in range(1, a.reintentos + 2):
        ids = getattr(solicitud, "id_solicitud", "-")
        print(f"[cliente] intento {intento}, id_solicitud={ids}, deadline {a.timeout:.0f} s")
        try:
            resp = llamada(solicitud, timeout=a.timeout)
        except grpc.RpcError as e:
            print(f"[cliente]   {e.code().name}, {e.details()}")
            if e.code() in REINTENTABLES:
                continue
            return 1
        if a.metodo == "tabla":
            print("[cliente]   " + (", ".join(f"{j.jugador}={j.puntos}" for j in resp.jugadores) or "(vacío)"))
        else:
            print(f"[cliente]   OK {resp.jugador} puntos={resp.puntos}")
        return 0
    if a.metodo == "tabla":
        print("[cliente] me rendí, sin respuesta del servidor")
    else:
        print("[cliente] me rendí, la operación quedó en estado DESCONOCIDO")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
