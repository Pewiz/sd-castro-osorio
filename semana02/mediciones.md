# Mediciones — Laboratorio N°1 (Semana 2)

**Equipo:** sd-castro-osorio   **Integrantes:** David Osorio / Felipe Castro
**Fecha:** 28-08-2026   **Entorno:** Docker Desktop (Windows)

## Paso 1 — Línea base
| Métrica | Valor |
|---|---|
| RTT ping (promedio) | 0.061 ms |
| Throughput iperf3 | 23.3 Gbit/s |

## Pasos 2 y 3 — Latencia inyectada (100 llamadas)
| Latencia `tc` | Total (s) | Promedio (ms) | Máx (ms) | ¿Esperado? (sí/no, por qué) |
|---|---|---|---|---|
| 0 ms (base) | 0.010 | 0.1 | 0.6 | Sí: 100 × 0 ms = 0 s ≈ 0.010 s |
| 50 ms | 5.018 | 50.2 | 50.3 | Sí: 100 × 50 ms = 5 s ≈ 5.018 s |
| 200 ms | 20.025 | 200.3 | 200.5 | Sí: 100 × 200 ms = 20 s ≈ 20.025 s |
| 500 ms | 50.026 | 500.3 | 500.6 | Sí: 100 × 500 ms = 50 s ≈ 50.026 s |

## Paso 4 — Pérdida de paquetes
| Pérdida `tc` | Throughput iperf3 | Total cliente (s) | Observación |
|---|---|---|---|
| 1% | 9.07 Gbit/s | 0.011 | iperf3 cae (23.3 -> 9.07); el cliente casi no se entera (máx 0.3 ms) |
| 5% | 0.209 Gbit/s | 0.629 | Cliente sigue “funcionando”; máx 206.2 ms: TCP retransmite en silencio |
| 20% | 839 Kbit/s | 12.026 | Cliente termina igual; máx 6783 ms: TCP retransmite, iperf3 casi muerto |
| 100% (falla provocada) | — | — / 3.0 | Sin timeout: `[Errno 113] No route to host` (no se colgó). Con TIMEOUT_S=3: aborta a los 3 s, 0 llamadas. |

## Falacia que asumimos sin advertirlo
"La latencia es cero", ya que nosotros asumimos que al usar latencia (tc) 0 ms, iba a ser instantaneo = 0 s, pero se demoro 0.010 s.
