#!/usr/bin/env python3
"""
Gemini Image Flash 自动化测试脚本
一键执行所有测试并生成报告
"""

import requests
import time
import json
import os
from datetime import datetime
from pathlib import Path

# ========== 配置区域 ==========
# 从 https://aistudio.google.com/app/apikey 获取
GEMINI_API_KEY = "YOUR_API_KEY_HERE"

# 测试输出目录
OUTPUT_DIR = os.path.expanduser("~/.openclaw/workspace/gemini-test-output")
REPORT_FILE = os.path.join(OUTPUT_DIR, "test-report.json")

# 测试参数
TEST_PROMPTS = {
    "speed_single": "a cute cat sitting on a windowsill, sunny day, photorealistic",
    "chinese_001": "两个黄鹂鸣翠柳，一行白鹭上青天，中国画风格",
    "chinese_002": "画龙点睛，龙在墙上，画家正在点睛",
    "chinese_003": "火锅里涮毛肚，红油翻滚，中式餐厅",
    "character_base": "Han Li from A Record of a Mortal's Journey to Immortality, young man in cyan robe, black long hair, portrait, front view",
    "character_action": "Han Li in cyan robe, fighting with flying sword, action pose",
    "grid_3x3_angles": "character sheet, 9 panels, 3x3 grid, same character different angles, front side back",
    "grid_3x3_expressions": "9 emoji expressions, same character, 3x3 grid, happy sad angry surprised",
    "text_generation": "coffee shop sign with text 'Work-Fisher', realistic style",
}

# 测试次数（取平均）
TEST_RUNS = 3
# ==============================

class GeminiTester:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.results = []
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
    def log(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {msg}")
        
    def generate_image(self, prompt, width=1024, height=1024):
        """调用Gemini Image API生成图片"""
        url = f"{self.base_url}/models/gemini-2.0-flash-exp-image-generation:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Generate an image: {prompt}. Size: {width}x{height}"
                }]
            }],
            "generationConfig": {
                "responseModalities": ["Text", "Image"]
            }
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=120)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "time": round(elapsed, 2),
                    "data": data,
                    "prompt": prompt
                }
            else:
                return {
                    "success": False,
                    "time": round(elapsed, 2),
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "prompt": prompt
                }
        except Exception as e:
            return {
                "success": False,
                "time": 0,
                "error": str(e),
                "prompt": prompt
            }
    
    def test_speed_single(self):
        """测试单张生成速度"""
        self.log("🚀 测试1: 单张生成速度")
        
        times = []
        for i in range(TEST_RUNS):
            self.log(f"  运行 {i+1}/{TEST_RUNS}...")
            result = self.generate_image(TEST_PROMPTS["speed_single"])
            if result["success"]:
                times.append(result["time"])
            else:
                self.log(f"  ❌ 失败: {result.get('error', 'Unknown')}")
        
        avg_time = sum(times) / len(times) if times else 0
        
        return {
            "test": "speed_single",
            "avg_time": round(avg_time, 2),
            "min_time": round(min(times), 2) if times else 0,
            "max_time": round(max(times), 2) if times else 0,
            "success_rate": f"{len(times)}/{TEST_RUNS}",
            "prompt": TEST_PROMPTS["speed_single"]
        }
    
    def test_speed_batch(self, count=10):
        """测试批量生成速度"""
        self.log(f"🚀 测试2: 批量生成{count}张")
        
        start_time = time.time()
        results = []
        
        for i in range(count):
            self.log(f"  生成 {i+1}/{count}...")
            result = self.generate_image(f"{TEST_PROMPTS['speed_single']} variation {i+1}")
            results.append(result)
        
        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r["success"])
        
        return {
            "test": f"speed_batch_{count}",
            "total_time": round(total_time, 2),
            "avg_time_per_image": round(total_time / count, 2),
            "success_count": success_count,
            "failed_count": count - success_count,
            "success_rate": f"{success_count}/{count}"
        }
    
    def test_chinese(self):
        """测试中文理解"""
        self.log("🇨🇳 测试3: 中文理解能力")
        
        chinese_tests = [
            ("chinese_001", "古诗词", TEST_PROMPTS["chinese_001"]),
            ("chinese_002", "成语", TEST_PROMPTS["chinese_002"]),
            ("chinese_003", "中餐", TEST_PROMPTS["chinese_003"]),
        ]
        
        results = []
        for test_id, test_name, prompt in chinese_tests:
            self.log(f"  测试 {test_name}...")
            result = self.generate_image(prompt)
            results.append({
                "id": test_id,
                "name": test_name,
                "prompt": prompt,
                "success": result["success"],
                "time": result["time"],
                "error": result.get("error", None)
            })
        
        return {
            "test": "chinese_comprehension",
            "results": results,
            "success_count": sum(1 for r in results if r["success"]),
            "total_count": len(results)
        }
    
    def test_character_consistency(self):
        """测试人物一致性"""
        self.log("🎭 测试4: 人物一致性（韩立）")
        
        variations = [
            ("正面", TEST_PROMPTS["character_base"]),
            ("战斗", TEST_PROMPTS["character_action"]),
        ]
        
        results = []
        for var_name, prompt in variations:
            self.log(f"  生成 {var_name}...")
            result = self.generate_image(prompt)
            results.append({
                "variation": var_name,
                "prompt": prompt,
                "success": result["success"],
                "time": result["time"],
                "error": result.get("error", None)
            })
        
        return {
            "test": "character_consistency",
            "results": results,
            "success_count": sum(1 for r in results if r["success"]),
            "note": "人工评估: 需对比多张图的一致性"
        }
    
    def test_grid_generation(self):
        """测试九宫格生成"""
        self.log("🎨 测试5: 九宫格生成能力")
        
        grid_tests = [
            ("多角度", TEST_PROMPTS["grid_3x3_angles"]),
            ("表情包", TEST_PROMPTS["grid_3x3_expressions"]),
        ]
        
        results = []
        for test_name, prompt in grid_tests:
            self.log(f"  测试 {test_name}...")
            result = self.generate_image(prompt)
            results.append({
                "type": test_name,
                "prompt": prompt,
                "success": result["success"],
                "time": result["time"],
                "error": result.get("error", None),
                "note": "检查是否生成3x3网格或单张图"
            })
        
        return {
            "test": "grid_generation",
            "results": results,
            "success_count": sum(1 for r in results if r["success"]),
            "evaluation": "需人工检查: 是否真正理解'3x3 grid'指令"
        }
    
    def test_text_generation(self):
        """测试文字生成"""
        self.log("📝 测试6: 图片中文字生成")
        
        result = self.generate_image(TEST_PROMPTS["text_generation"])
        
        return {
            "test": "text_generation",
            "prompt": TEST_PROMPTS["text_generation"],
            "success": result["success"],
            "time": result["time"],
            "evaluation": "需人工检查: 图中文字是否为'Work-Fisher'"
        }
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("=" * 50)
        self.log("🎯 Gemini Image Flash 自动化测试")
        self.log("=" * 50)
        self.log("")
        
        all_results = {
            "test_time": datetime.now().isoformat(),
            "api_key_set": bool(GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_API_KEY_HERE"),
            "tests": []
        }
        
        # 检查API Key
        if not all_results["api_key_set"]:
            self.log("❌ 错误: 请先在脚本顶部设置 GEMINI_API_KEY")
            return all_results
        
        # 执行测试
        tests = [
            self.test_speed_single,
            lambda: self.test_speed_batch(5),  # 先测5张，避免额度用完
            self.test_chinese,
            self.test_character_consistency,
            self.test_grid_generation,
            self.test_text_generation,
        ]
        
        for test_func in tests:
            try:
                result = test_func()
                all_results["tests"].append(result)
            except Exception as e:
                self.log(f"❌ 测试失败: {e}")
                all_results["tests"].append({
                    "test": test_func.__name__,
                    "error": str(e)
                })
            self.log("")
        
        # 保存报告
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        self.log("=" * 50)
        self.log(f"✅ 测试完成！报告保存至: {REPORT_FILE}")
        self.log("=" * 50)
        
        # 打印摘要
        self.print_summary(all_results)
        
        return all_results
    
    def print_summary(self, results):
        """打印测试摘要"""
        self.log("")
        self.log("📊 测试摘要:")
        self.log("-" * 50)
        
        for test in results.get("tests", []):
            test_name = test.get("test", "Unknown")
            
            if "avg_time" in test:
                self.log(f"✓ {test_name}: {test['avg_time']}秒/张")
            elif "total_time" in test:
                self.log(f"✓ {test_name}: {test['total_time']}秒总计")
            elif "success_count" in test:
                self.log(f"✓ {test_name}: {test['success_count']}/{test.get('total_count', '?')} 成功")
            elif "success" in test:
                status = "成功" if test["success"] else "失败"
                self.log(f"✓ {test_name}: {status}")
            elif "error" in test:
                self.log(f"✗ {test_name}: 错误 - {test['error'][:50]}")
        
        self.log("-" * 50)
        self.log("💡 提示: 请检查生成的图片质量并人工评分")
        self.log("💡 人工评估项: 中文理解准确性、人物一致性、九宫格效果")


def main():
    """主函数"""
    tester = GeminiTester(GEMINI_API_KEY)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
