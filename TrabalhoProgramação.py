import threading
import time
import random
from queue import Queue


estado = {
    "via_ativa": "NS",       
    "fila_NS": 0,           
    "fila_LO": 0,            
    "ciclos": 0,            
    "carros_passaram": 0,    
}
lock_estado = threading.Lock()   

fila_sensores = Queue()         
fila_log      = Queue()          

rodando = True  


def sensor(via, intervalo):
    while rodando:
        novos_carros = random.randint(0, 4)
        if novos_carros > 0:
            fila_sensores.put({"via": via, "carros": novos_carros})
            fila_log.put(
                f"[SENSOR {via}]   +{novos_carros} carro(s) detectado(s)"
            )
        time.sleep(intervalo + random.uniform(0, 0.3))
        

def controlador(tempo_ciclo):
    while rodando:
        while not fila_sensores.empty():
            leitura = fila_sensores.get_nowait()
            with lock_estado:                    
                estado["fila_" + leitura["via"]] += leitura["carros"]

        with lock_estado:                        
            via_atual = estado["via_ativa"]
            fila_ns   = estado["fila_NS"]
            fila_lo   = estado["fila_LO"]

            outra_via  = "LO" if via_atual == "NS" else "NS"
            fila_atual = fila_ns if via_atual == "NS" else fila_lo
            fila_outra = fila_lo if via_atual == "NS" else fila_ns

            deve_trocar = fila_outra > fila_atual + 1 

            if deve_trocar:
                estado["via_ativa"] = outra_via
                estado["ciclos"]   += 1
                passaram = min(fila_atual, random.randint(2, 5))
                estado["fila_" + via_atual]  = max(0, fila_atual - passaram)
                estado["carros_passaram"]    += passaram
                fila_log.put(
                    f"[CTRL]   VERDE → {outra_via} "
                    f"(fila {outra_via}={fila_outra} > {via_atual}={fila_atual}) "
                    f"| {passaram} carro(s) passaram"
                )
            else:
                passaram = min(fila_atual, random.randint(1, 4))
                estado["fila_" + via_atual]  = max(0, fila_atual - passaram)
                estado["carros_passaram"]    += passaram
                fila_log.put(
                    f"[CTRL]   VERDE mantido {via_atual} "
                    f"| {passaram} carro(s) passaram"
                )

        time.sleep(tempo_ciclo)



def logger(duracao):
    fim = time.time() + duracao + 1
    while time.time() < fim or not fila_log.empty():
        try:
            msg = fila_log.get(timeout=0.5)
            print(msg)
        except Exception:
            pass



def mostrar_estado():
    with lock_estado:
        via    = estado["via_ativa"]
        ns     = estado["fila_NS"]
        lo     = estado["fila_LO"]
        ciclos = estado["ciclos"]
        total  = estado["carros_passaram"]

    ns_sinal = "🟢 VERDE" if via == "NS" else "🔴 VERMELHO"
    lo_sinal = "🟢 VERDE" if via == "LO" else "🔴 VERMELHO"
    print(f"\n  {'─'*45}")
    print(f"  Norte-Sul   : {ns_sinal}  | fila: {ns} carro(s)")
    print(f"  Leste-Oeste : {lo_sinal}  | fila: {lo} carro(s)")
    print(f"  Ciclos: {ciclos}  |  Total passaram: {total}")
    print(f"  {'─'*45}\n")



if __name__ == "__main__":
    DURACAO_SIM = 8  
    CICLO_CTRL  = 1.0 

    print("=" * 50)
    print("  SEMÁFORO INTELIGENTE — CONCORRENTE")
    print(f"  Simulação de {DURACAO_SIM}s | ciclo={CICLO_CTRL}s")
    print("=" * 50)

    threads = [
        threading.Thread(target=sensor,      args=("NS", 0.6),       name="Sensor-NS",    daemon=True),
        threading.Thread(target=sensor,      args=("LO", 0.8),       name="Sensor-LO",    daemon=True),
        threading.Thread(target=controlador, args=(CICLO_CTRL,),     name="Controlador",  daemon=True),
        threading.Thread(target=logger,      args=(DURACAO_SIM,),    name="Logger"),
    ]

    print("\n  Threads iniciadas:")
    for t in threads:
        t.start()
        print(f"    ▸ {t.name}")

    print()

    inicio = time.time()
    while time.time() - inicio < DURACAO_SIM:
        time.sleep(2)
        mostrar_estado()

    rodando = False  

    threads[-1].join(timeout=3)

    print("\n" + "=" * 50)
    with lock_estado:
        print(f"  Ciclos de troca  : {estado['ciclos']}")
        print(f"  Carros passaram  : {estado['carros_passaram']}")
        print(f"  Fila NS restante : {estado['fila_NS']}")
        print(f"  Fila LO restante : {estado['fila_LO']}")
    print("=" * 50)
    print("  Simulação encerrada.")
