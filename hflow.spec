# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

# Собираем все PySide6 модули
datas = []
binaries = []
hiddenimports = []

for package in ['PySide6']:
    datas_tmp, binaries_tmp, hiddenimports_tmp = collect_all(package)
    datas += datas_tmp
    binaries += binaries_tmp
    hiddenimports += hiddenimports_tmp

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=[
        ('resources/icons', 'resources/icons'),
        ('resources/sounds', 'resources/sounds'),
        ('resources/styles', 'resources/styles'),
    ] + datas,

    hiddenimports=hiddenimports + [
        # PySide6
        'PySide6.QtMultimedia',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',

        # Core
        'core',
        'core.di',
        'core.di.container',
        'core.app',
        'core.event_bus',
        'core.main_window',
        'core.navigation',

        # Database
        'datebase',
        'datebase.db_manager',
        'datebase.db_queries',
        'datebase.repositories',
        'datebase.repositories.flashcard_repo',
        'datebase.repositories.note_repo',
        'datebase.repositories.quick_note_repo',
        'datebase.repositories.review_repo',
        'datebase.repositories.session_repo',
        'datebase.repositories.session_state_log_repo',
        'datebase.repositories.settings_repo',
        'datebase.repositories.task_repo',
        'datebase.repositories.topic_repo',

        # Models
        'models',
        'models.flashcard',
        'models.note',
        'models.quick_note',
        'models.review_answer',
        'models.review_session',
        'models.session',
        'models.session_state_log',
        'models.settings',
        'models.task',
        'models.topic',

        # Modules
        'modules',

        # Analytics
        'modules.analytics',
        'modules.analytics.charts',
        'modules.analytics.controller',
        'modules.analytics.dialogs',
        'modules.analytics.insights',
        'modules.analytics.view',

        # Dashboard
        'modules.dashboard',
        'modules.dashboard.controller',
        'modules.dashboard.view',
        'modules.dashboard.widgets',

        # Flashcards
        'modules.flashcards',
        'modules.flashcards.controller',
        'modules.flashcards.dialogs',
        'modules.flashcards.global_view',
        'modules.flashcards.review_controller',
        'modules.flashcards.review_view',
        'modules.flashcards.view',

        # Music
        'modules.music',
        'modules.music.controller',
        'modules.music.widgets',

        # Notes
        'modules.notes',
        'modules.notes.controller',
        'modules.notes.editor',
        'modules.notes.reader',
        'modules.notes.widgets',

        # Search
        'modules.search',
        'modules.search.controller',
        'modules.search.view',
        'modules.search.widgets',

        # Sessions
        'modules.sessions',
        'modules.sessions.active_view',
        'modules.sessions.analytics_dialog',
        'modules.sessions.controller',
        'modules.sessions.history_view',
        'modules.sessions.quick_capture',
        'modules.sessions.setup_view',
        'modules.sessions.state_log_controller',
        'modules.sessions.widgets',

        # Tasks
        'modules.tasks',
        'modules.tasks.calendar_controller',
        'modules.tasks.calendar_view',
        'modules.tasks.controller',
        'modules.tasks.dialogs',
        'modules.tasks.filters',
        'modules.tasks.global_view',
        'modules.tasks.list_view',
        'modules.tasks.view',
        'modules.tasks.widgets',

        # Topics
        'modules.topics',
        'modules.topics.analytics_controller',
        'modules.topics.controller',
        'modules.topics.topic_view',
        'modules.topics.tree_view',
        'modules.topics.widgets',

        # Settings
        'modules.settings',
        'modules.settings.themes',
        'modules.settings.controller',
        'modules.settings.view',

        # Onboarding
        'onboarding',
        'onboarding.steps',
        'onboarding.wizard',

        # Services
        'services',
        'services.backup_service',
        'services.export_service',
        'services.hotkey_service',
        'services.import_service',
        'services.notification_service',
        'services.sound_service',
        'services.sync_service',
        'services.time_service',

        # Utils
        'utils',
        'utils.resource_paths',
        'utils.local_time',
        'utils.ping_manager',

        # Widgets
        'widgets',
        'widgets.silent_dialog',
        'widgets.styled_dialog',

        # ✅ ДОБАВЛЕНО: matplotlib и numpy для графиков аналитики
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.figure',
        'numpy',
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HarmonyFlowNotes',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # ← ВРЕМЕННО ВКЛЮЧИ ДЛЯ ОТЛАДКИ! Потом верни False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/app.ico',
)