import subprocess

process = None


def run_flow(volume_ml, pls):
    global process
    # Запускаем процесс
    process = subprocess.Popen(
        f'/opt/kiosk/vodobox-pro/vendor/flowmeter/flow {volume_ml} {pls}',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        close_fds=True
    )

    # Читаем вывод процесса построчно
    try:
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"Вывод: {output.strip()}")

        # Получаем ошибки, если есть
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"Ошибка: {stderr_output.strip()}")

    except KeyboardInterrupt:
        print("Остановка процесса с использованием ctrl+c...")
        stop_flow()  # Вызов функции остановки


# Функция для остановки процесса
def stop_flow():
    global process
    if process:
        process.terminate()
        process.wait()
        process = None
