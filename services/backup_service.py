# services/backup_service.py
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any


class BackupService:
    """Сервис для резервного копирования данных"""

    def __init__(self, db_path: str, backup_dir: Optional[str] = None):
        """
        Args:
            db_path: Путь к файлу БД
            backup_dir: Директория для бэкапов (по умолчанию ./backups)
        """
        self.db_path = Path(db_path)

        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            self.backup_dir = Path(__file__).parent.parent / "backups"

        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, name: str = None) -> Optional[Path]:
        """
        Создаёт резервную копию БД

        Args:
            name: Имя бэкапа (если None, генерируется автоматически)

        Returns:
            Путь к созданному бэкапу или None
        """
        if not self.db_path.exists():
            print(f"[BackupService] Файл БД не найден: {self.db_path}")
            return None

        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"hflow_backup_{timestamp}"

        backup_path = self.backup_dir / f"{name}.db"

        try:
            shutil.copy2(self.db_path, backup_path)
            print(f"[BackupService] Бэкап создан: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"[BackupService] Ошибка создания бэкапа: {e}")
            return None

    def create_full_backup(self, name: str = None) -> Optional[Path]:
        """
        Создаёт полный бэкап (БД + ресурсы)

        Args:
            name: Имя бэкапа

        Returns:
            Путь к ZIP архиву
        """
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"hflow_full_backup_{timestamp}"

        zip_path = self.backup_dir / f"{name}.zip"

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Добавляем БД
                zipf.write(self.db_path, self.db_path.name)

                # Добавляем папку с ресурсами (если есть)
                resources_dir = Path(__file__).parent.parent / "resources"
                if resources_dir.exists():
                    for file in resources_dir.rglob("*"):
                        if file.is_file():
                            arcname = file.relative_to(resources_dir.parent)
                            zipf.write(file, arcname)

            print(f"[BackupService] Полный бэкап создан: {zip_path}")
            return zip_path
        except Exception as e:
            print(f"[BackupService] Ошибка создания полного бэкапа: {e}")
            return None

    def restore_backup(self, backup_path: str) -> bool:
        """
        Восстанавливает БД из бэкапа

        Args:
            backup_path: Путь к файлу бэкапа

        Returns:
            True если успешно
        """
        backup_path = Path(backup_path)

        if not backup_path.exists():
            print(f"[BackupService] Файл бэкапа не найден: {backup_path}")
            return False

        # Создаём бэкап текущей БД перед восстановлением
        self.create_backup("before_restore")

        try:
            shutil.copy2(backup_path, self.db_path)
            print(f"[BackupService] БД восстановлена из: {backup_path}")
            return True
        except Exception as e:
            print(f"[BackupService] Ошибка восстановления: {e}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        Возвращает список доступных бэкапов

        Returns:
            Список словарей с информацией о бэкапах
        """
        backups = []

        for file in self.backup_dir.glob("*.db"):
            backups.append({
                'name': file.stem,
                'path': str(file),
                'size_kb': file.stat().st_size / 1024,
                'created_at': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })

        for file in self.backup_dir.glob("*.zip"):
            backups.append({
                'name': file.stem,
                'path': str(file),
                'size_kb': file.stat().st_size / 1024,
                'type': 'full',
                'created_at': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })

        # Сортируем по дате создания (новые сверху)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups

    def delete_backup(self, backup_path: str) -> bool:
        """
        Удаляет файл бэкапа

        Args:
            backup_path: Путь к файлу

        Returns:
            True если успешно
        """
        try:
            Path(backup_path).unlink()
            return True
        except Exception as e:
            print(f"[BackupService] Ошибка удаления бэкапа: {e}")
            return False

    def cleanup_old_backups(self, keep_count: int = 10):
        """
        Удаляет старые бэкапы, оставляя только keep_count последних

        Args:
            keep_count: Сколько бэкапов оставить
        """
        backups = self.list_backups()

        if len(backups) <= keep_count:
            return

        for backup in backups[keep_count:]:
            self.delete_backup(backup['path'])