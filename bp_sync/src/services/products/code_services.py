# import os
from pathlib import Path

from fastapi import UploadFile

from core.logger import logger


class CodeService:
    def __init__(self) -> None:
        self.valid_codes: set[str] = set()
        self.code_file = "valid_codes.txt"
        self.data_dir = Path("data")
        self.file_path = self.data_dir / self.code_file
        self.ensure_directory()
        self.load_codes()

    def ensure_directory(self) -> None:
        """
        Создает директорию для хранения файлов с кодами, если она не существует
        """
        try:
            self.data_dir.mkdir(exist_ok=True, parents=True)
            logger.debug(f"Директория {self.data_dir} проверена/создана")
        except Exception as e:
            logger.error(
                f"Ошибка при создании директории {self.data_dir}: {str(e)}"
            )
            raise

    def load_codes(self) -> None:
        """Загружает коды из файла в память"""
        try:
            if self.file_path.exists():
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.valid_codes = {
                        line.strip() for line in f if line.strip()
                    }
                logger.info(
                    f"Загружено {len(self.valid_codes)} валидных кодов из "
                    f"файла {self.file_path}"
                )
            else:
                logger.warning(
                    f"Файл с кодами не найден: {self.file_path}. Запуск с "
                    "пустым списком кодов"
                )
                self.valid_codes = set()
        except Exception as e:
            logger.error(
                "Ошибка при загрузке кодов из файла "
                f"{self.file_path}: {str(e)}"
            )
            self.valid_codes = set()

    async def save_uploaded_file(self, file: UploadFile) -> bool:
        """Сохраняет загруженный файл с кодами и перезагружает коды в память"""
        self.ensure_directory()
        try:
            # Сохраняем новый файл
            with open(self.file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            # Перезагружаем коды
            self.load_codes()
            logger.info(f"Файл {file.filename} успешно загружен и обработан")
            return True
        except Exception as e:
            logger.error(
                f"Ошибка при сохранении файла {file.filename}: {str(e)}"
            )
            return False

    def is_valid_code(self, code: str) -> bool:
        """Проверяет, существует ли код в списке валидных кодов"""
        is_valid = code in self.valid_codes
        if not is_valid:
            logger.debug(f"Код не найден в списке валидных: {code}")
        return is_valid

    def get_codes_count(self) -> int:
        """Возвращает количество загруженных валидных кодов"""
        count = len(self.valid_codes)
        logger.debug(f"Текущее количество валидных кодов: {count}")
        return count

    def reload_codes(self) -> None:
        """Принудительно перезагружает коды из файла"""
        logger.info("Принудительная перезагрузка кодов из файла")
        self.load_codes()
