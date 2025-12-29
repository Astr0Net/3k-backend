from sqlalchemy import create_engine, inspect, text

# جایگزین کن با اطلاعات واقعی dbaas
DATABASE_URL = "postgresql://root:YNNTJYfbZ328YJg9VOfGb9oo@hotaka.liara.cloud:34363/postgres"

# اتصال به دیتابیس

# اتصال به دیتابیس
engine = create_engine(DATABASE_URL)

# بررسی اتصال و لیست جدول‌ها
with engine.connect() as conn:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Tables in database:", tables)

    # تست تعداد رکورد در جدول chats (اگر وجود دارد)
    if "chats" in tables:
        result = conn.execute(text("SELECT COUNT(*) FROM chats"))
        count = result.scalar()
        print("Number of records in 'chats':", count)
    else:
        print("'chats' table does not exist.")