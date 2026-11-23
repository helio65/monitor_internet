import os
import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# 1. Define o diretório base (funciona tanto como script .py quanto compilado em .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PASTA_PRINTS = os.path.join(BASE_DIR, "prints")
ARQUIVO_LOG = os.path.join(BASE_DIR, "log_velocidade.txt")

def garantir_diretorio():
    if not os.path.exists(PASTA_PRINTS):
        os.makedirs(PASTA_PRINTS)

def registrar_log(data_hora_str, download, upload, status="SUCESSO"):
    linha = f"[{data_hora_str}] Status: {status} | Download: {download} Mbps | Upload: {upload} Mbps\n"
    with open(ARQUIVO_LOG, "a", encoding="utf-8") as f:
        f.write(linha)
    print(linha.strip())

def executar_teste():
    garantir_diretorio()
    agora = datetime.now()
    data_hora_log = agora.strftime("%d/%m/%Y %H:%M:%S")
    data_hora_arquivo = agora.strftime("%Y-%m-%d_%H-%M-%S")

    print(f"[{data_hora_log}] Iniciando teste de velocidade...")

    with sync_playwright() as p:
        # headless=False abre a janela visualmente. Mude para True se quiser rodar oculto.
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        try:
            # 1. Acessar a página
            page.goto("https://speed.unifique.com.br/", timeout=60000)

            # 2. Clicar em INICIAR (o speedtest LibreSpeed/Unifique usa o id #startStopBtn)
            botao_iniciar = page.locator("#startStopBtn")
            botao_iniciar.wait_for(state="visible", timeout=15000)
            botao_iniciar.click()

            # Aguarda o teste concluir (o teste completo leva em média 30 a 45 segundos).
            # No LibreSpeed, o botão volta a ter a classe/estado inicial ou a URL de compartilhamento aparece.
            print("Aguardando conclusão do teste (aprox. 40s)...")
            page.wait_for_function(
                """() => {
                    const dl = document.querySelector('#dlText')?.innerText.trim();
                    const ul = document.querySelector('#ulText')?.innerText.trim();
                    const btn = document.querySelector('#startStopBtn');
                    // Verifica se ambos têm valores numéricos e o botão não está em modo 'running'
                    return dl && ul && dl !== '' && ul !== '' && !btn.classList.contains('running');
                }""",
                timeout=90000
            )
            
            # Pausa extra de 2 segundos para estabilização visual antes do print
            time.sleep(2)

            # 3. Ler os resultados
            download = page.locator("#dlText").inner_text().strip()
            upload = page.locator("#ulText").inner_text().strip()

            # 6. Retirar print da tela e salvar na pasta 'prints'
            caminho_print = os.path.join(PASTA_PRINTS, f"speedtest_{data_hora_arquivo}.png")
            page.screenshot(path=caminho_print)

            # 4. Gerar o log
            registrar_log(data_hora_log, download, upload, status="CONCLUÍDO")

        except Exception as e:
            registrar_log(data_hora_log, "N/A", "N/A", status=f"ERRO: {str(e)}")
        
        finally:
            # 7. Fechar a aba/navegador
            page.close()
            browser.close()

# 5. Loop para executar de 1 em 1 hora
if __name__ == "__main__":
    INTERVALO_SEGUNDOS = 3600  # 1 hora = 3600 segundos

    while True:
        executar_teste()
        print(f"Aguardando 1 hora para a próxima execução...\n")
        time.sleep(INTERVALO_SEGUNDOS)
