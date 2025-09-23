#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
食堂系统性能监控工具
用于分析和监控API响应时间和数据库查询性能
"""

import time
import requests
import mysql.connector
from mysql.connector import Error
import json
import threading
from datetime import datetime

class PerformanceMonitor:
    def __init__(self, base_url="http://0.0.0.0:5000"):
        self.base_url = base_url
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'your_pswd',
            'database': 'hust_canteen'
        }
        self.results = []
        
    def test_api_response_time(self, endpoint, method="GET", params=None, data=None):
        """测试API响应时间"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params)
            else:
                response = requests.post(url, json=data)
            
            elapsed_time = (time.time() - start_time) * 1000
            
            return {
                'endpoint': endpoint,
                'method': method,
                'status_code': response.status_code,
                'response_time_ms': elapsed_time,
                'success': response.status_code == 200,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'endpoint': endpoint,
                'method': method,
                'status_code': 0,
                'response_time_ms': (time.time() - start_time) * 1000,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_database_queries(self):
        """测试数据库查询性能"""
        queries = [
            {
                'name': '推荐菜品查询',
                'sql': """
                    SELECT d.dish_id, d.name, d.avg_rating, d.image_url,
                           s.custom_name as stall_name, c.name as canteen_name
                    FROM dishes d
                    JOIN stall_dishes sd ON d.dish_id = sd.dish_id
                    JOIN canteen_stalls s ON sd.stall_id = s.stall_id
                    JOIN canteens c ON s.canteen_id = c.canteen_id
                    WHERE sd.is_available = 1
                    ORDER BY d.avg_rating DESC
                    LIMIT 10
                """
            },
            {
                'name': '食堂拥挤度查询',
                'sql': """
                    SELECT c.canteen_id, c.name, c.crowd_level
                    FROM canteens c
                    ORDER BY c.crowd_level ASC
                """
            },
            {
                'name': '搜索查询',
                'sql': """
                    SELECT d.dish_id, d.name, d.avg_rating,
                           s.custom_name as stall_name, c.name as canteen_name
                    FROM dishes d
                    JOIN stall_dishes sd ON d.dish_id = sd.dish_id
                    JOIN canteen_stalls s ON sd.stall_id = s.stall_id
                    JOIN canteens c ON s.canteen_id = c.canteen_id
                    WHERE d.name LIKE '%红烧肉%' AND sd.is_available = 1
                    ORDER BY d.avg_rating DESC
                    LIMIT 20
                """
            }
        ]
        
        results = []
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            for query in queries:
                start_time = time.time()
                
                try:
                    cursor.execute(query['sql'])
                    cursor.fetchall()
                    elapsed_time = (time.time() - start_time) * 1000
                    
                    # 获取执行计划
                    cursor.execute("EXPLAIN " + query['sql'])
                    explain_result = cursor.fetchall()
                    
                    results.append({
                        'name': query['name'],
                        'query_time_ms': elapsed_time,
                        'rows_examined': sum(row[8] for row in explain_result if len(row) > 8),
                        'using_index': any('Using index' in str(row) for row in explain_result),
                        'success': True,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Error as e:
                    results.append({
                        'name': query['name'],
                        'query_time_ms': (time.time() - start_time) * 1000,
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            cursor.close()
            conn.close()
            
        except Error as e:
            results.append({
                'name': '数据库连接',
                'query_time_ms': 0,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        return results
    
    def run_full_test(self):
        """运行完整性能测试"""
        print("=== 食堂系统性能测试报告 ===")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 测试API响应时间
        print("1. API响应时间测试")
        api_tests = [
            ('/api/recommendations/dishes', 'GET'),
            ('/api/recommendations/canteens', 'GET'),
            ('/api/recommendations/stalls', 'GET'),
            ('/api/rankings/popular_dishes', 'GET'),
            ('/api/search?q=红烧肉&type=all', 'GET'),
            ('/api/canteens', 'GET')
        ]
        
        api_results = []
        for endpoint, method in api_tests:
            result = self.test_api_response_time(endpoint, method)
            api_results.append(result)
            print(f"  {endpoint}: {result['response_time_ms']:.2f}ms {'✓' if result['success'] else '✗'}")
        
        print()
        
        # 测试数据库查询性能
        print("2. 数据库查询性能测试")
        db_results = self.test_database_queries()
        
        for result in db_results:
            if result['success']:
                print(f"  {result['name']}: {result['query_time_ms']:.2f}ms (检查 {result['rows_examined']} 行)")
            else:
                print(f"  {result['name']}: 失败 - {result['error']}")
        
        print()
        
        # 生成性能报告
        successful_api = [r for r in api_results if r['success']]
        slow_apis = [r for r in successful_api if r['response_time_ms'] > 1000]
        
        print("3. 性能问题总结")
        if slow_apis:
            print("  慢响应API (>1000ms):")
            for api in slow_apis:
                print(f"    {api['endpoint']}: {api['response_time_ms']:.2f}ms")
        else:
            print("  所有API响应正常")
        
        slow_queries = [r for r in db_results if r['success'] and r['query_time_ms'] > 500]
        if slow_queries:
            print("  慢查询 (>500ms):")
            for query in slow_queries:
                print(f"    {query['name']}: {query['query_time_ms']:.2f}ms")
        else:
            print("  所有查询响应正常")
        
        # 保存结果到文件
        all_results = {
            'api_tests': api_results,
            'db_tests': db_results,
            'summary': {
                'total_apis': len(api_results),
                'successful_apis': len(successful_api),
                'slow_apis': len(slow_apis),
                'slow_queries': len(slow_queries)
            }
        }
        
        with open('performance_report.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: performance_report.json")
        return all_results

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    monitor.run_full_test()
