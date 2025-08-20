# import os
from pathlib import Path

from fastapi import UploadFile


class CodeService:
    def __init__(self) -> None:
        self.valid_codes: set[str] = set()
        self.code_file = "valid_codes.txt"
        self.data_dir = Path("data")
        self.file_path = self.data_dir / self.code_file
        self.ensure_directory()
        self.load_codes()

    def ensure_directory(self) -> None:
        self.data_dir.mkdir(exist_ok=True, parents=True)

    def load_codes(self) -> None:
        try:
            if self.file_path.exists():
                with open(self.file_path, "r") as f:
                    self.valid_codes = {
                        line.strip() for line in f if line.strip()
                    }
                print(f"✅ Loaded {len(self.valid_codes)} valid codes")
            else:
                print("⚠️ Code file not found. Starting with empty codes")
                self.valid_codes = set()
        except Exception as e:
            print(f"❌ Error loading codes: {str(e)}")
            self.valid_codes = set()

    async def save_uploaded_file(self, file: UploadFile) -> bool:
        self.ensure_directory()
        try:
            # Сохраняем новый файл
            with open(self.file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            # Перезагружаем коды
            self.load_codes()
            return True
        except Exception as e:
            print(f"❌ Error saving file: {str(e)}")
            return False

    def is_valid_code(self, code: str) -> bool:
        return code in self.valid_codes

    def get_codes_count(self) -> int:
        return len(self.valid_codes)
