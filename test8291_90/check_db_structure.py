#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查和修复数据库外键约束问题
"""

import mysql.connector
from mysql.connector import Error

def check_foreign_keys():
    """检查当前数据库的外键约束"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Ray123_123',
            database='hust_canteen'
        )
        
        cursor = conn.cursor(dictionary=True)
        
        # 检查 dish_reviews 表的外键约束
        cursor.execute("""
            SELECT 
                TABLE_NAME,
                COLUMN_NAME,
                CONSTRAINT_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = 'hust_canteen' 
            AND TABLE_NAME = 'dish_reviews'
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        
        foreign_keys = cursor.fetchall()
        
        print("当前 dish_reviews 表的外键约束:")
        for fk in foreign_keys:
            print(f"约束名: {fk['CONSTRAINT_NAME']}")
            print(f"列名: {fk['COLUMN_NAME']}")
            print(f"引用表: {fk['REFERENCED_TABLE_NAME']}")
            print(f"引用列: {fk['REFERENCED_COLUMN_NAME']}")
            print("-" * 40)
        
        # 检查 stall_dishes 表的结构
        cursor.execute("DESCRIBE stall_dishes")
        stall_dishes_structure = cursor.fetchall()
        
        print("stall_dishes 表结构:")
        for column in stall_dishes_structure:
            print(f"{column['Field']}: {column['Type']} {column['Key']}")
        
        # 检查 dishes 表的结构
        cursor.execute("DESCRIBE dishes")
        dishes_structure = cursor.fetchall()
        
        print("dishes 表结构:")
        for column in dishes_structure:
            print(f"{column['Field']}: {column['Type']} {column['Key']}")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"数据库错误: {e}")

def fix_foreign_key_constraint():
    """修复外键约束"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Ray123_123',
            database='hust_canteen'
        )
        
        cursor = conn.cursor()
        
        # 获取当前外键约束名称
        cursor.execute("""
            SELECT CONSTRAINT_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = 'hust_canteen' 
            AND TABLE_NAME = 'dish_reviews' 
            AND COLUMN_NAME = 'stall_dish_id'
            AND REFERENCED_TABLE_NAME = 'dishes'
        """)
        
        result = cursor.fetchone()
        if result:
            constraint_name = result[0]
            print(f"找到错误的外键约束: {constraint_name}")
            
            # 删除错误的外键约束
            cursor.execute(f"ALTER TABLE dish_reviews DROP FOREIGN KEY {constraint_name}")
            print("已删除错误的外键约束")
            
            # 添加正确的外键约束
            cursor.execute("""
                ALTER TABLE dish_reviews 
                ADD CONSTRAINT fk_dish_reviews_stall_dish 
                FOREIGN KEY (stall_dish_id) 
                REFERENCES stall_dishes(id) 
                ON DELETE CASCADE 
                ON UPDATE CASCADE
            """)
            print("已添加正确的外键约束")
            
            conn.commit()
        else:
            print("未找到错误的外键约束，可能已经被修复")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"修复时出错: {e}")

if __name__ == "__main__":
    print("=== 检查数据库外键约束 ===")
    check_foreign_keys()
    
    print("\n=== 修复外键约束 ===")
    fix_foreign_key_constraint()
    
    print("\n=== 再次检查 ===")
    check_foreign_keys()