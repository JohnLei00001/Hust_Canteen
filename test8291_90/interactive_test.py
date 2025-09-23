#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式敏感词检测测试工具
使用密钥: your_key
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from safe_content_moderator import SafeContentModerator, check_text_safe, moderate_content
from encrypted_content_moderator import EncryptedContentModerator

class InteractiveTester:
    def __init__(self):
        """初始化测试器"""
        self.moderator = SafeContentModerator(password="helloworld")
        print("🎯 交互式敏感词检测测试工具")
        print("=" * 50)
        print("密钥: your_key")
        print("加密文件: encrypted_sensitive_words.json")
        print("=" * 50)
        print()
    
    def show_menu(self):
        """显示主菜单"""
        print("\n🔍 请选择测试模式:")
        print("1. 快速检测 (一行文本)")
        print("2. 详细审核 (查看敏感词详情)")
        print("3. 批量测试 (多条文本)")
        print("4. 查看当前敏感词数量")
        print("5. 测试联系方式检测")
        print("6. 退出")
        print()
    
    def quick_test(self):
        """快速检测模式"""
        print("\n⚡ 快速检测模式")
        print("-" * 30)
        text = input("请输入要检测的文本: ").strip()
        if not text:
            print("❌ 输入不能为空")
            return
        
        is_safe = check_text_safe(text)
        print(f"\n📊 结果:")
        print(f"文本: {text}")
        print(f"状态: {'✅ 安全' if is_safe else '❌ 包含敏感词'}")
    
    def detailed_test(self):
        """详细审核模式"""
        print("\n🔍 详细审核模式")
        print("-" * 30)
        text = input("请输入要检测的文本: ").strip()
        if not text:
            print("❌ 输入不能为空")
            return
        
        result = moderate_content(text)
        print(f"\n📊 详细结果:")
        print(f"文本: {text}")
        print(f"安全: {'✅ 是' if result['is_safe'] else '❌ 否'}")
        
        if result['violation_words']:
            print(f"敏感词: {', '.join(result['violation_words'])}")
        else:
            print("敏感词: 无")
            
        if result['violation_type']:
            print(f"违规类型: {result['violation_type']}")
        
        if result['masked_text'] != text:
            print(f"屏蔽文本: {result['masked_text']}")
    
    def batch_test(self):
        """批量测试模式"""
        print("\n📦 批量测试模式")
        print("-" * 30)
        print("请输入多条文本，每行一条，空行结束:")
        
        texts = []
        while True:
            line = input("> ").strip()
            if not line:
                break
            texts.append(line)
        
        if not texts:
            print("❌ 没有输入任何文本")
            return
        
        print(f"\n📊 批量检测结果 ({len(texts)} 条):")
        print("-" * 50)
        
        safe_count = 0
        for i, text in enumerate(texts, 1):
            result = moderate_content(text)
            status = "✅ 安全" if result['is_safe'] else "❌ 敏感"
            print(f"{i}. {text} -> {status}")
            
            if not result['is_safe']:
                print(f"   敏感词: {', '.join(result['violation_words'])}")
            else:
                safe_count += 1
        
        print(f"\n📈 统计: {safe_count}/{len(texts)} 条安全")
    
    def show_stats(self):
        """显示统计信息"""
        try:
            # 直接访问底层审核器获取统计
            stats = self.moderator.moderator.get_stats()
            print(f"\n📊 系统统计:")
            print(f"敏感词数量: {stats.get('word_count', '未知')}")
            print(f"加密方法: {stats.get('encryption_method', '未知')}")
            print(f"数据源: {stats.get('data_source', '未知')}")
        except:
            print("\n📊 系统统计:")
            print("✅ 加密敏感词系统已激活")
            print("密钥: helloworld")
    
    def test_contact_detection(self):
        """测试联系方式检测"""
        print("\n📞 联系方式检测测试")
        print("-" * 30)
        
        test_cases = [
            "我的电话是13800138000",
            "联系邮箱: user@example.com",
            "微信号: abc123456",
            "QQ群: 123456789",
            "网址: https://example.com"
        ]
        
        print("预设测试案例:")
        for i, text in enumerate(test_cases, 1):
            result = moderate_content(text)
            status = "✅ 安全" if result['is_safe'] else "❌ 检测到联系方式"
            print(f"{i}. {text} -> {status}")
            
            if not result['is_safe']:
                print(f"   检测到: {', '.join(result['violation_words'])}")
        
        # 自定义测试
        print("\n📝 自定义测试:")
        custom_text = input("请输入包含联系方式的文本: ").strip()
        if custom_text:
            result = moderate_content(custom_text)
            status = "✅ 安全" if result['is_safe'] else "❌ 检测到联系方式"
            print(f"结果: {custom_text} -> {status}")
    
    def run(self):
        """运行交互式测试"""
        try:
            while True:
                self.show_menu()
                choice = input("请选择 (1-6): ").strip()
                
                if choice == '1':
                    self.quick_test()
                elif choice == '2':
                    self.detailed_test()
                elif choice == '3':
                    self.batch_test()
                elif choice == '4':
                    self.show_stats()
                elif choice == '5':
                    self.test_contact_detection()
                elif choice == '6':
                    print("👋 感谢使用！再见！")
                    break
                else:
                    print("❌ 无效选择，请重新输入")
        
        except KeyboardInterrupt:
            print("\n\n👋 测试中断，再见！")
        except Exception as e:
            print(f"\n❌ 测试出错: {e}")

def main():
    """主函数"""
    tester = InteractiveTester()
    tester.run()

if __name__ == "__main__":
    main()
