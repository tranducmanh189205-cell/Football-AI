from django.db.backends.mysql.base import DatabaseWrapper, DatabaseFeatures

# Tắt tính năng RETURNING không hỗ trợ trên MariaDB cũ
DatabaseFeatures.can_return_rows_from_bulk_insert = False
DatabaseFeatures.uses_savepoints = True

# Ép Django bỏ qua kiểm tra phiên bản
DatabaseWrapper.check_database_version_supported = lambda self: None