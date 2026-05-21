import subprocess
import sys

try:
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        required = {line.split('==')[0].strip().lower() for line in f if line.strip() and not line.startswith('#')}
except FileNotFoundError:
    print("Ошибка: Сначала создайте файл requirements.txt с помощью pipreqs!")
    sys.exit(1)

required.update({'pip', 'setuptools', 'wheel', 'pipreqs', 'pip-autoremove'})

result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=freeze'], capture_output=True, text=True)
installed = {line.split('==')[0].strip().lower() for line in result.stdout.splitlines() if line.strip()}

unused = installed - required

if not unused:
    print("Неиспользуемых библиотек не найдено. Окружение чистое!")
else:
    print(f"Найдено неиспользуемых пакетов: {len(unused)}")
    for pkg in unused:
        print(f"Удаление пакета и его зависимостей: {pkg}")
        subprocess.run([sys.executable, '-m', 'pip_autoremove', pkg, '-y'])

    print("Очистка успешно завершена!")
