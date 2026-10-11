test_scripts = [
    'test_check_emojis',
    'test_desktop',
    'test_hidden_games',
    'test_importer',
    'test_logs',
    'test_manual_games',
    'test_play_history',
    'test_saved_library',
    'test_settings',
    'test_silent_failures',
]

foreach name : test_scripts
    test(
        name,
        python,
        args: files(name + '.py'),
        env: {'CARTRIDGES_SCHEMA_DIR': meson.project_build_root() / 'data'},
        workdir: meson.project_source_root(),
    )
endforeach
