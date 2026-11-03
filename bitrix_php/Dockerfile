FROM php:8.2-apache

# 1. Устанавливаем системные зависимости для сборки расширений
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libonig-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Явно конфигурируем pgsql (помогает, если pg_config не находится автоматически)
RUN docker-php-ext-configure pgsql --with-pgsql=/usr

# 3. Устанавливаем нужные расширения.
# curl уже собран и подключён в официальном образе php:8.2-apache,
# повторная сборка curl через docker-php-ext-install требует libcurl4-openssl-dev и не нужна.
RUN docker-php-ext-install ftp pgsql pdo_pgsql mbstring

# 4. Включаем mod_rewrite (для Apache)
RUN a2enmod rewrite

# 5. Копируем код и даём права
COPY src/ /var/www/html/
RUN chown -R www-data:www-data /var/www/html
