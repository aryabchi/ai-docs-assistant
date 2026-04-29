import logging

# Форматтер
date_format = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
    datefmt=date_format,
)

# Основной логгер
logger = logging.getLogger("memory-agent")
logger.setLevel(logging.DEBUG)

# 3. Обработчик для консоли (все логи)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Добавляем все обработчики
logger.addHandler(console_handler)
