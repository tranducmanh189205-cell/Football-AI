import pymysql
pymysql.install_as_MySQLdb()

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures

# 1. Bỏ qua bước kiểm tra phiên bản MariaDB tối thiểu
BaseDatabaseWrapper.check_database_version_supported = lambda self: None

# 2. Tắt tính năng RETURNING để tương thích cú pháp của MariaDB 10.4
DatabaseFeatures.can_return_rows_from_bulk_insert = False
DatabaseFeatures.has_returning_fields = False