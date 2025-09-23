#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL外键约束修复工具
"""

import mysql.connector
from mysql.connector import Error

def fix_dish_reviews_foreign_key():
    """修复dish_reviews表的外键约束"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Ray123_123',
            database='hust_canteen'
        )
        
        cursor = conn.cursor()
        
        print("连接到数据库成功")
        
        # 1. 查看当前外键约束
        cursor.execute("""
            SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = 'hust_canteen' 
            AND TABLE_NAME = 'dish_reviews'
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        
        foreign_keys = cursor.fetchall()
        print("当前外键约束:")
        for fk in foreign_keys:
            print(f"约束: {fk[0]}, 列: {fk[1]} -> {fk[2]}.{fk[3]}")
        
        # 2. 删除错误约束
        for fk in foreign_keys:
            if fk[1] == 'stall_dish_id' and fk[2] == 'dishes':
                constraint_name = fk[0]
                print(f"正在删除错误的外键约束: {constraint_name}")
                cursor.execute(f"ALTER TABLE dish_reviews DROP FOREIGN KEY {constraint_name}")
                print("错误的外键约束已删除")
            elif fk[1] == 'stall_dish_id' and fk[2] == 'stall_dishes' and fk[0] != 'fk_dr_stall_dish':
                # 删除重复的正确约束（如果有）
                constraint_name = fk[0]
                print(f"正在删除重复的外键约束: {constraint_name}")
                cursor.execute(f"ALTER TABLE dish_reviews DROP FOREIGN KEY {constraint_name}")
                print("重复的外键约束已删除")
        
        # 3. 添加正确的外键约束
        try:
            cursor.execute("""
                ALTER TABLE dish_reviews 
                ADD CONSTRAINT fk_dish_reviews_stall_dish 
                FOREIGN KEY (stall_dish_id) REFERENCES stall_dishes(id) 
                ON DELETE CASCADE 
                ON UPDATE CASCADE
            """)
            print("正确的外键约束已添加")
        except Error as e:
            if "Duplicate key name" in str(e):
                print("外键约束已存在，跳过")
            else:
                raise e
        
        conn.commit()
        print("数据库修复完成")
        
        # 4. 验证修复结果
        cursor.execute("""
            SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = 'hust_canteen' 
            AND TABLE_NAME = 'dish_reviews'
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        
        updated_fks = cursor.fetchall()
        print("修复后的外键约束:")
        for fk in updated_fks:
            print(f"约束: {fk[0]}, 列: {fk[1]} -> {fk[2]}.{fk[3]}")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"数据库错误: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_dish_reviews_foreign_key()