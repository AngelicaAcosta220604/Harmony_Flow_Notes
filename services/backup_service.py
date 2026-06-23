# services/backup_service.py
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from utils.resource_paths import get_resource_path, get_db_path

# Настройка логирования
logger = logging.getLogger(__name__)


class BackupService:
    """Сервис для резервного копирования данных"""

    def __init__(self, db_path: str = None, backup_dir: Optional[str] = None):
        """
        Args:
            db_path: Путь к файлу БД (если None, используется get_db_path())
            backup_dir: Директория для бэкапов (по умолчанию рядом с БД)
        """
        try:
            # ✅ ИСПРАВЛЕНО: используем get_db_path() для корректного пути в EXE
            if db_path:
                self.db_path = Path(db_path)
            else:
                self.db_path = get_db_path()

            if backup_dir:
                self.backup_dir = Path(backup_dir)
            else:
                # ✅ ИСПРАВЛЕНО: бэкапы создаются рядом с БД (в EXE — рядом с EXE)
                self.backup_dir = self.db_path.parent / "backups"

            self.backup_dir.mkdir(exist_ok=True, parents=True)
            logger.debug(f"BackupService инициализирован: БД={self.db_path}, бэкапы={self.backup_dir}")
        except Exception as e:
            logger.error(f"Ошибка инициализации BackupService: {e}", exc_info=True)
            raise

    def create_backup(self, name: str = None) -> Optional[Path]:
        """
        Создаёт резервную копию БД

        Args:
            name: Имя бэкапа (если None, генерируется автоматически)

        Returns:
            Путь к созданному бэкапу или None
        """
        try:
            if not self.db_path.exists():
                logger.error(f"Файл БД не найден: {self.db_path}")
                return None

            if name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name = f"hflow_backup_{timestamp}"

            backup_path = self.backup_dir / f"{name}.db"

            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Бэкап создан: {backup_path}")
            return backup_path
        except PermissionError as e:
            logger.error(f"Нет прав для создания бэкапа: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Ошибка создания бэкапа: {e}", exc_info=True)
            return None

    def create_full_backup(self, name: str = None) -> Optional[Path]:
        """
        Создаёт полный бэкап (БД + ресурсы)

        Args:
            name: Имя бэкапа

        Returns:
            Путь к ZIP архиву
        """
        try:
            if name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name = f"hflow_full_backup_{timestamp}"

            zip_path = self.backup_dir / f"{name}.zip"

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Добавляем БД
                if self.db_path.exists():
                    zipf.write(self.db_path, self.db_path.name)

                # ✅ ИСПРАВЛЕНО: используем get_resource_path() для корректного пути в EXE
                resources_dir = get_resource_path("resources")
                if resources_dir.exists():
                    for file in resources_dir.rglob("*"):
                        if file.is_file():
                            try:
                                arcname = file.relative_to(resources_dir.parent)
                                zipf.write(file, arcname)
                            except Exception as e:
                                logger.warning(f"Не удалось добавить файл {file} в бэкап: {e}")

            logger.info(f"Полный бэкап создан: {zip_path}")
            return zip_path
        except PermissionError as e:
            logger.error(f"Нет прав для создания полного бэкапа: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Ошибка создания полного бэкапа: {e}", exc_info=True)
            return None

    def restore_backup(self, backup_path: str) -> bool:
        """
        Восстанавливает БД из бэкапа

        Args:
            backup_path: Путь к файлу бэкапа

        Returns:
            True если успешно
        """
        try:
            backup_path = Path(backup_path)

            if not backup_path.exists():
                logger.error(f"Файл бэкапа не найден: {backup_path}")
                return False

            # Создаём бэкап текущей БД перед восстановлением
            self.create_backup("before_restore")

            shutil.copy2(backup_path, self.db_path)
            logger.info(f"БД восстановлена из: {backup_path}")
            return True
        except PermissionError as e:
            logger.error(f"Нет прав для восстановления БД: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Ошибка восстановления: {e}", exc_info=True)
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        Возвращает список доступных бэкапов

        Returns:
            Список словарей с информацией о бэкапах
        """
        try:
            backups = []

            if not self.backup_dir.exists():
                logger.warning(f"Директория бэкапов не существует: {self.backup_dir}")
                return []

            for file in self.backup_dir.glob("*.db"):
                try:
                    backups.append({
                        'name': file.stem,
                        'path': str(file),
                        'size_kb': file.stat().st_size / 1024,
                        'type': 'db',
                        'created_at': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Не удалось прочитать информацию о бэкапе {file}: {e}")

            for file in self.backup_dir.glob("*.zip"):
                try:
                    backups.append({
                        'name': file.stem,
                        'path': str(file),
                        'size_kb': file.stat().st_size / 1024,
                        'type': 'full',
                        'created_at': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Не удалось прочитать информацию о бэкапе {file}: {e}")

            # Сортируем по дате создания (новые сверху)
            backups.sort(key=lambda x: x['created_at'], reverse=True)

            logger.debug(f"Найдено {len(backups)} бэкапов")
            return backups
        except Exception as e:
            logger.error(f"Ошибка получения списка бэкапов: {e}", exc_info=True)
            return []

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
            logger.info(f"Удален бэкап: {backup_path}")
            return True
        except PermissionError as e:
            logger.error(f"Нет прав для удаления бэкапа {backup_path}: {e}", exc_info=True)
            return False
        except FileNotFoundError:
            logger.warning(f"Файл бэкапа не найден: {backup_path}")
            return False
        except Exception as e:
            logger.error(f"Ошибка удаления бэкапа {backup_path}: {e}", exc_info=True)
            return False

    def cleanup_old_backups(self, keep_count: int = 10):
        """
        Удаляет старые бэкапы, оставляя только keep_count последних

        Args:
            keep_count: Сколько бэкапов оставить
        """
        try:
            backups = self.list_backups()

            if len(backups) <= keep_count:
                logger.debug(f"Бэкапов {len(backups)} <= {keep_count}, очистка не требуется")
                return

            deleted_count = 0
            for backup in backups[keep_count:]:
                if self.delete_backup(backup['path']):
                    deleted_count += 1

            logger.info(f"Удалено {deleted_count} старых бэкапов, оставлено {keep_count}")
        except Exception as e:
            logger.error(f"Ошибка очистки старых бэкапов: {e}", exc_info=True)