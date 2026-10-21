from unittest.mock import MagicMock, call

from bin import main as main_module


def test_main_wires_bot_and_background_threads(monkeypatch):
    bot = MagicMock()
    hub = MagicMock()
    logger = MagicMock()
    shutdown_event = MagicMock()
    polling_thread = MagicMock()
    cleanup_thread = MagicMock()

    validate = MagicMock()
    init_db = MagicMock()
    migrate_json_to_db = MagicMock()
    create_bot = MagicMock(return_value=bot)
    features_hub = MagicMock(return_value=hub)
    logger_class = MagicMock(return_value=logger)
    register_commands = MagicMock()
    register_handlers = MagicMock()
    register_signal = MagicMock()
    thread_class = MagicMock(side_effect=[polling_thread, cleanup_thread])

    monkeypatch.setattr(main_module.config, "BOT_TOKEN", "1:test")
    monkeypatch.setattr(main_module.config, "validate", validate)
    monkeypatch.setattr(main_module, "init_db", init_db)
    monkeypatch.setattr(main_module, "migrate_json_to_db", migrate_json_to_db)
    monkeypatch.setattr(main_module, "create_bot", create_bot)
    monkeypatch.setattr(main_module, "BotFeaturesHub", features_hub)
    monkeypatch.setattr(main_module.log, "Logger", logger_class)
    monkeypatch.setattr(main_module, "register_commands", register_commands)
    monkeypatch.setattr(main_module, "register_handlers", register_handlers)
    monkeypatch.setattr(main_module.signal, "signal", register_signal)
    monkeypatch.setattr(main_module.threading, "Event", MagicMock(return_value=shutdown_event))
    monkeypatch.setattr(main_module.threading, "Thread", thread_class)

    main_module.main()

    validate.assert_called_once_with()
    init_db.assert_called_once_with()
    migrate_json_to_db.assert_called_once_with()
    create_bot.assert_called_once_with("1:test")
    features_hub.assert_called_once_with(bot)
    logger_class.assert_called_once_with()
    register_commands.assert_called_once_with(bot)
    register_handlers.assert_called_once_with(bot, hub, logger)
    assert thread_class.call_args_list == [
        call(target=main_module.run_polling, args=(bot, logger), daemon=True),
        call(target=main_module.periodic_cleanup, args=(hub, logger), daemon=True),
    ]
    polling_thread.start.assert_called_once_with()
    cleanup_thread.start.assert_called_once_with()
    shutdown_event.wait.assert_called_once_with()

    assert register_signal.call_count == 2
    assert register_signal.call_args_list[0].args[0] == main_module.signal.SIGTERM
    assert register_signal.call_args_list[1].args[0] == main_module.signal.SIGINT
    assert register_signal.call_args_list[0].args[1] is register_signal.call_args_list[1].args[1]

    handle_shutdown = register_signal.call_args_list[0].args[1]
    handle_shutdown(main_module.signal.SIGTERM, None)

    logger.log_info.assert_called_once_with("Received shutdown signal, stopping...")
    bot.stop_polling.assert_called_once_with()
    shutdown_event.set.assert_called_once_with()
