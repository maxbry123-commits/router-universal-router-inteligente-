# INPUTS VERBATIM — SWE CODE (1:1, sin editar)

## INPUT A — sistema en cadena (motores/software)

> esto lo vamos a usar como un sistema en cadena
> | Motor | Qué hace | Con modelo local |
> |---|---|---|
> | **aider** | edita archivos + git commits vía chat | `--openai-api-base http://localhost:8080` ✅ |
> | **SWE-agent** (Princeton) | bash+editor loop para resolver issues | OpenAI-compatible ✅ |
> | **OpenHands micro** | sandbox completo: terminal, browser, editor | vía LiteLLM ✅ |
> | gpt-engineer | genera proyectos desde prompt | sí |
> | terminal-bench harness | ejecuta comandos reales en Docker | sí |
>
> Ve anotando
>
> tambien lo introduces de llama toll si se puede usar como ayuda solo si es necesario y que no baje el token por segundo
>
> luego metemos esto
> 1. Hace el code 📌
> Qwen2.5-Coder-0.5B @ ~36 t/s → $0.23/M ✅
> revisa cual de los 2 usar
> Qwen2.5-Coder-1.5B	40	$0.21	probado en tool-JSON 91%
>
> 2 revisa y refactoria 📌
> Qwen3.5-0.8B @ ~27 t/s → $0.31/M ✅
>
> 3. Reviss de nuevo y refactoriza si es necesario 📌
> DeepSeek-Coder-1.3B
>
> ejecuta modo agentico 📌
>
> 3. Ejecuta tool y modo agentico
> Qwen3-0.6B @ ~35-45 t/s → $0.19-0.24/M ✅
>
> quiero instalado también en huggueface
> liquid ai que tenga modo agentico tool los modelos más pequeños posible
>
> estos modelo deben tener posibilidades de sistemas mirror para que pueda reolicarse en los 3 servidores
>
> todo descragdo en huggueface almacenamiento permanente
>
> el software lo pones en Github como parte del sistema promt en la misma organización que tenemos para activar junto a system promt SOFTWARE/motores que el modelo agentico maneja (ejecutan código de verdad, no son agentes) solo para activar
> con esos modelos que vamos a usar local
> Usas los motores los descraga y cableas
> aladas uno de los selector donde está los selectores de los modelo le pones SWE CODE
>
> no puedes usar tu pc para code solo puedes usar tu pc para crear el fromtend y revisar visualmente 📌
>
> no puedes crear archivos ni raíz en main solo puede crear una extensión raíz del system promt para crear lo que falta 📌
>
> no tocas el router solo añade un api a los modelo y crees un mini router o fichas conectado a los plugins del modelo de manera organizada de la raíz debe ser algo mínimo de code solo para ejecutar la secuencia de los modelos en huggueface como un mini router todo de manera organizada en una sola raiz nueva en router MVP / SWE CODE / 📂📂📂📂 escribes directo el code Mvp mínimo posible eliminas cualquier sobre ingeniería o tarea no autorizado
>
> necesiro la idnformación de los modelo tokens por segundo y precio en HF 32 ram cpu definitivo
>
> el sisytema debe ser capaz de conectar un puente nuevo mini router mínimo mínimo
> Que llame las sdk o api de los modelo instalados en huggueface ➡️ banco de sdk o api local de nuestro modelo ➡️ mini ficha plugins ➡️ que recibe cómputo del router ➡️ hace mirror del system promt ➡️ los sofware sistema en cascada de software de code ➡️ HTTP plugins deepsek harnes ➡️ Plugins chat ➡️ selector del chat
>
> no puedes romoer la organización
>
> Para descragar en HF usas 3 job para descargar
>
> vamos a dividir el trabajo en partes tu haces el code mínimo en Github y grockbot hace lo de huggueface me das un DSL Dag promt para dividir el trabajo
>
> revisa estos modelo a nivel de code tool y agentico y costo por token no puede superar ninguno de los modelo 0.30$ por costo de millón de token
>
> tsmbien vamos a usar deeopsek por Api y otra cuenta SDK de qwen plan
>
> vamos a montar como el chat el en vercel Github y huggueface
> Opción oficial: DeepSeek Harness (DSH)
> Es la apuesta de DeepSeek para ejecutar agentes. No es un simple chat, sino un entorno de ejecución de agentes que gestiona el bucle de razonamiento, las llamadas a herramientas y el contexto.
> · Cómo usarlo: Si tienes Node.js instalado, puedes levantar su interfaz web local con un solo comando: npx @deepseek-ai/dsh web.
> · Modos de trabajo: Incluye un modo estándar con un conjunto completo de herramientas, y un modo PTC (Programmatic Tool Calling) que permite al modelo generar código para orquestar múltiples llamadas a herramientas en una sola ejecución.
> esto DSH me explicas cómo lo hacemos
>
> Paso 1 📌
> anotas 1 a 1 imput block verbartin
>
> paso 2 📌
> nexesito que me expliques la preguntas antes de avanzar
>
> Paso 3 📌 salida 2
> necesito una prueba en un job con los modelos para probar el token por según en code phyton ejecutable como prueba antes de creer todo puede ser un job
>
> inicia paso 1 y 2 salida 1

## INPUT B — constraints previos (sesión, verbatim relevante)

> revisa y calcula esto
> Qwen3.5-0.8B — Q4: ~27 tok/s — US$0,31/millón.
> GitHub
> Qwen2.5-Coder-0.5B — Q4: ~36 tok/s — US$0,23/millón.
> Qwen3-0.6B

> ok ve strata o fast2 hay más posibilidades de más token por segundo
> cuando dices escritor pero no tiene tool o agentico no puede escribir en Github?
> mw parece mejor Qwen3-0.6B más rápido
> Busca en la universidad de China proyectos tambien swe busca otros modelo deben estar a un costo de 0.40$ o menos en precio por millón de token en HF cpu
> los otros modelos son buenos pero el precio no lo justifica
> busca de nuevo en huggueface y en la comunidad de desarrolladores de programación de code de China y en proyectos de universidades en China y en huggueface realiza 3 listas

> que modelo pequeño chino o otros recomendarías tu para programar que podamos usar en HF 32 de ram que tenga modo agentico herramientas nativa que sea pequeño cuantificado pequeño que el costo por tokens justifique el servidor de 32 ram cpu
