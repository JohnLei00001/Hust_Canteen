#!/usr/bin/env python3
"""
集成示例：如何在食堂系统中使用你的加密敏感词
"""

from safe_content_moderator import SafeContentModerator, check_text_safe, moderate_content

def demo_integration():
    """演示如何集成到你的食堂系统"""
    
    print("=== 食堂系统敏感词检测集成示例 ===")
    print("密钥: helloworld")
    print()
    
    # 方法1: 使用全局函数
    print("📍 方法1: 快速检查")
    test_comment = "这个食堂的菜很好吃，但是服务态度有点差"
    is_safe = check_text_safe(test_comment)
    print(f"评论: {test_comment}")
    print(f"安全: {'✅ 通过' if is_safe else '❌ 包含敏感词'}")
    print()
    
    # 方法2: 详细审核
    print("📍 方法2: 详细审核")
    result = moderate_content(test_comment)
    print(f"详细结果: {result}")
    print()
    
    # 方法3: 创建实例
    print("📍 方法3: 创建审核器实例")
    moderator = SafeContentModerator(password="helloworld")
    
    # 模拟食堂评论审核
    canteen_comments = [
        "今天的红烧肉真好吃！",
        "服务态度太差了，投诉！",
        "价格合理，环境不错",
        "菜里有头发，恶心死了",
        "推荐他们家的宫保鸡丁"
    ]
    
    print("🍽️ 食堂评论审核结果:")
    for i, comment in enumerate(canteen_comments, 1):
        result = moderator.check_text(comment)
        status = "✅ 通过" if result['is_safe'] else "❌ 屏蔽"
        masked = result['masked_text'] if result['masked_text'] != comment else comment
        
        print(f"{i}. {comment} -> {status}")
        if result['violation_words']:
            print(f"   敏感词: {result['violation_words']}")
            print(f"   屏蔽后: {masked}")
    
    print("\n🎉 集成完成！")
    print("现在你可以将这套系统应用到：")
    print("- 用户评论审核")
    print("- 食堂评价系统")
    print("- 菜品评价")
    print("- 论坛发帖")

if __name__ == "__main__":
    demo_integration()