import os
import shutil
import json
import subprocess
from datetime import datetime
from pathlib import Path
import sys

# Кастомное исключение для ошибок сборочного скрипта
class BuildScriptError(Exception):
    pass

# Функция для логирования с текущей временной меткой
def log(message: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}")

# Функция для выполнения команд оболочки (shell)
# При ошибке выполнения вызывает исключение с описанием ошибки
def run_cmd(cmd, cwd=None):
    log(f"Запуск команды: {cmd} (директория: {cwd if cwd else 'текущая'})")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"Команда завершилась с ошибкой! Код: {result.returncode}")
        log(f"stderr: {result.stderr.strip()}")
        raise BuildScriptError(f"Ошибка выполнения команды: {cmd}")
    log(f"Команда выполнена успешно, вывод:\n{result.stdout.strip()}")
    return result.stdout.strip()

# Основная функция скрипта
def main(repo_url, source_rel_path, version):
    # Временная директория для клонирования репозитория
    tmp_dir = Path("tmp_repo")

    # Если временная папка уже существует, удаляем её (чистим старые данные)
    if tmp_dir.exists():
        log(f"Временная папка {tmp_dir} существует. Начинаем удаление...")
        shutil.rmtree(tmp_dir)
        log(f"Папка {tmp_dir} успешно удалена")
    else:
        log(f"Временная папка {tmp_dir} отсутствует, пропускаем удаление")

    # Клонируем репозиторий в tmp_dir
    log(f"Начинаем клонирование репозитория {repo_url} в {tmp_dir}...")
    run_cmd(f"git clone {repo_url} {tmp_dir}")
    log(f"Репозиторий клонирован успешно")

    # Полный путь к папке с исходным кодом внутри клонированного репозитория
    source_dir = tmp_dir / source_rel_path
    # Проверяем, что папка с исходниками существует
    if not source_dir.exists() or not source_dir.is_dir():
        raise BuildScriptError(f"Папка с исходным кодом не найдена: {source_dir}")
    log(f"Исходный код найден по пути: {source_dir}")

    # Удаляем все файлы и папки в корне tmp_dir, кроме папки с исходным кодом
    log(f"Удаляем все файлы и папки в {tmp_dir}, кроме {source_dir}...")
    for item in tmp_dir.iterdir():
        if item != source_dir:
            if item.is_dir():
                log(f"Удаляем директорию: {item}")
                shutil.rmtree(item)
                log(f"Директория {item} удалена")
            else:
                log(f"Удаляем файл: {item}")
                item.unlink()
                log(f"Файл {item} удалён")
    log(f"Удаление завершено")

    # Собираем список файлов с расширениями .py, .js, .sh внутри папки исходников
    log(f"Собираем список файлов с расширениями .py, .js, .sh в {source_dir}...")
    files_list = [f.name for f in source_dir.iterdir() if f.is_file() and f.suffix in ['.py', '.js', '.sh']]
    log(f"Найдено файлов: {len(files_list)} - {files_list}")

    # Формируем словарь для файла version.json
    version_data = {
        "name": "hello world",      # фиксированное имя, как указано в задании
        "version": version,         # версия продукта из параметров
        "files": files_list         # список файлов с нужными расширениями
    }

    # Путь для создания файла version.json внутри папки исходников
    version_json_path = source_dir / "version.json"
    log(f"Создаём служебный файл version.json по пути: {version_json_path}")
    with open(version_json_path, "w", encoding="utf-8") as f:
        json.dump(version_data, f, indent=4, ensure_ascii=False)
    log(f"Файл version.json успешно создан")

    # Определяем имя архива: имя последней папки из пути + текущая дата без разделителей
    last_dir_name = Path(source_rel_path).parts[-1]
    date_str = datetime.now().strftime("%Y%m%d")
    archive_name = f"{last_dir_name}{date_str}.zip"
    archive_path = Path.cwd() / archive_name

    # Архивируем папку с исходниками (вместе с файлом version.json)
    log(f"Создаём архив {archive_name} из директории {source_rel_path} внутри {tmp_dir}...")
    shutil.make_archive(base_name=last_dir_name + date_str, format='zip', root_dir=tmp_dir, base_dir=source_rel_path)
    log(f"Архив {archive_name} успешно создан в {archive_path}")

    # Удаляем временную папку с клонированным репозиторием
    log(f"Удаляем временную папку {tmp_dir} для очистки...")
    shutil.rmtree(tmp_dir)
    log(f"Временная папка {tmp_dir} удалена. Сборка завершена успешно.")

# Точка входа скрипта
if __name__ == "__main__":
    # Проверка количества аргументов: должно быть ровно 3 (плюс имя скрипта — всего 4)
    if len(sys.argv) != 4:
        print("Использование:")
        print("  python build_script.py <repo_url> <relative_path_to_source> <version>")
        sys.exit(0)

    repo_url = sys.argv[1]
    source_rel_path = sys.argv[2]
    version = sys.argv[3]

    # Запускаем основную функцию и ловим ошибки сборки, выводя их в лог
    try:
        main(repo_url, source_rel_path, version)
    except BuildScriptError as e:
        log(f"Ошибка сборки: {e}")
