from PyQt5.QtCore import pyqtSignal, QObject
import subprocess
import re

process = None


class FlowHandler(QObject):
    liters_changed = pyqtSignal(float)

    def run_flow(self, volume_ml, pls):
        global process
        # Запускаем процесс
        process = subprocess.Popen(
            [f'/opt/kiosk/vodobox-pro/vendor/flowmeter/flow', str(volume_ml), str(pls)],
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
                    print(output)
                    nums = re.findall("\d+", output.strip())
                    if nums:
                        self.liters_changed.emit(float(nums[0]))

            stderr_output = process.stderr.read()
            if stderr_output:
                print(f"Ошибка: {stderr_output.strip()}")

        except KeyboardInterrupt:
            print("Остановка процесса с использованием ctrl+c...")
            self.stop_flow()

    def stop_flow(self):
        global process
        if process:
            process.terminate()
            process.wait()
            process = None
