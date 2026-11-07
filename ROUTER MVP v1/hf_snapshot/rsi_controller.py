class RSIController:
    def __init__(self, max_iterations=5):
        self.max_iterations = max_iterations

    async def run_loop(self, model_call_fn, initial_prompt):
        current_prompt = initial_prompt
        last_output = ""
        
        for i in range(self.max_iterations):
            print(f"🔄 RSI Iteración {i+1}...")
            # model_call_fn es una corrutina que llama al agente paralelo
            last_output = await model_call_fn(current_prompt)
            
            # Condición de parada: El modelo declara que terminó
            if "TERMINADO" in last_output or "<DONE>" in last_output:
                print("✅ El modelo declaró TERMINADO. Rompiendo bucle.")
                return last_output.replace("TERMINADO", "").replace("<DONE>", "").strip()

            # Si no ha terminado, lo obligamos a seguir iterando con su propio output
            current_prompt = f"""
            Tu respuesta anterior fue:
            {last_output}
            
            IMPORTANTE: Si la tarea ya está completa y verificada, escribe la palabra TERMINADO al final. 
            Si aún falta código, tests o correcciones, continúa trabajando ahora.
            """
            
        return last_output
