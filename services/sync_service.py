# services/sync_service.py
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict


@dataclass
class SyncMetadata:
    """Метаданные для синхронизации"""
    version: int = 1
    last_sync: Optional[str] = None
    device_id: str = ""
    checksum: str = ""
    data_hash: str = ""


class SyncService:
    """
    Сервис для синхронизации данных (локальная, между устройствами через файл)
    В v1.0 поддерживается только экспорт/импорт для ручного переноса
    """

    def __init__(self, db_path: str, sync_dir: Optional[str] = None):
        """
        Args:
            db_path: Путь к файлу БД
            sync_dir: Директория для синхронизации
        """
        self.db_path = Path(db_path)

        if sync_dir:
            self.sync_dir = Path(sync_dir)
        else:
            self.sync_dir = Path(__file__).parent.parent / "sync"

        self.sync_dir.mkdir(exist_ok=True)
        self.metadata_file = self.sync_dir / "sync_metadata.json"

    def _calculate_hash(self, data: str) -> str:
        """Вычисляет хеш данных"""
        return hashlib.sha256(data.encode()).hexdigest()

    def _get_db_hash(self) -> str:
        """Вычисляет хеш текущей БД"""
        if not self.db_path.exists():
            return ""

        with open(self.db_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def export_sync_package(self, package_name: str = None) -> Optional[Path]:
        """
        Экспортирует пакет для синхронизации

        Args:
            package_name: Имя пакета (если None, генерируется)

        Returns:
            Путь к созданному пакету
        """
        if not self.db_path.exists():
            return None

        if package_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            package_name = f"hflow_sync_{timestamp}"

        package_path = self.sync_dir / f"{package_name}.json"

        try:
            # Читаем БД
            with open(self.db_path, 'rb') as f:
                db_data = f.read()

            # Создаём пакет
            package = {
                'metadata': {
                    'exported_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'db_hash': hashlib.sha256(db_data).hexdigest(),
                    'db_size': len(db_data)
                },
                'data': {
                    'db_base64': db_data.hex()  # hex для простоты
                }
            }

            with open(package_path, 'w', encoding='utf-8') as f:
                json.dump(package, f, ensure_ascii=False, indent=2)

            return package_path
        except Exception as e:
            print(f"[SyncService] Ошибка экспорта пакета: {e}")
            return None

    def import_sync_package(self, package_path: str) -> bool:
        """
        Импортирует пакет синхронизации

        Args:
            package_path: Путь к пакету

        Returns:
            True если успешно
        """
        package_path = Path(package_path)

        if not package_path.exists():
            print(f"[SyncService] Пакет не найден: {package_path}")
            return False

        try:
            with open(package_path, 'r', encoding='utf-8') as f:
                package = json.load(f)

            # Проверяем версию
            if package.get('metadata', {}).get('version') != '1.0':
                print("[SyncService] Неподдерживаемая версия пакета")
                return False

            # Получаем данные
            db_hex = package.get('data', {}).get('db_base64', '')
            if not db_hex:
                print("[SyncService] Пакет не содержит данных")
                return False

            # Создаём бэкап текущей БД
            backup_path = self.sync_dir / f"backup_before_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if self.db_path.exists():
                import shutil
                shutil.copy2(self.db_path, backup_path)

            # Записываем новые данные
            db_bytes = bytes.fromhex(db_hex)
            with open(self.db_path, 'wb') as f:
                f.write(db_bytes)

            print(f"[SyncService] Синхронизация завершена из: {package_path}")
            return True
        except Exception as e:
            print(f"[SyncService] Ошибка импорта пакета: {e}")
            return False

    def list_sync_packages(self) -> List[Dict[str, Any]]:
        """Возвращает список доступных пакетов синхронизации"""
        packages = []

        for file in self.sync_dir.glob("*.json"):
            packages.append({
                'name': file.stem,
                'path': str(file),
                'size_kb': file.stat().st_size / 1024,
                'created_at': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })

        packages.sort(key=lambda x: x['created_at'], reverse=True)
        return packages

    def get_sync_status(self) -> Dict[str, Any]:
        """
        Возвращает статус синхронизации

        Returns:
            Словарь с информацией о последней синхронизации
        """
        status = {
            'last_sync': None,
            'db_hash': self._get_db_hash(),
            'has_pending_changes': False,
            'available_packages': len(self.list_sync_packages())
        }

        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                status['last_sync'] = metadata.get('last_sync')
                status['last_sync_hash'] = metadata.get('data_hash')

                # Проверяем, изменилась ли БД с последней синхронизации
                if status['last_sync_hash'] and status['last_sync_hash'] != status['db_hash']:
                    status['has_pending_changes'] = True
            except Exception as e:
                print(f"[SyncService] Ошибка чтения метаданных: {e}")

        return status