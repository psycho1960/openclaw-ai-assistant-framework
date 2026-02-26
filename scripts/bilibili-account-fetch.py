#!/usr/bin/env python3
"""
B站个人账号数据获取脚本 - 修复版
用途: 获取老鱼账号的实时数据（粉丝、播放量、视频等）
特点: 完善的错误处理和日志记录
"""

import json
import requests
from datetime import datetime
import os
import sys
import traceback

# 设置日志文件
LOG_FILE = '/home/zzyuzhangxing/.openclaw/workspace/logs/bilibili_account.log'

def log(msg, level='INFO'):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] [{level}] {msg}"
    print(log_msg)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')
    except:
        pass

# B站Cookie配置
BILIBILI_COOKIES = {
    'SESSDATA': '',
    'bili_jct': '',
    'DedeUserID': '17919458',
}

def load_cookies():
    """从配置文件加载Cookie"""
    config_file = '/home/zzyuzhangxing/.openclaw/workspace/config/bilibili_cookies.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                cookies = json.load(f)
                log(f"已加载Cookie配置文件")
                # 检查Cookie是否为空
                if not cookies.get('SESSDATA') or not cookies.get('bili_jct'):
                    log("⚠️ Cookie为空，需要更新！", 'WARN')
                return cookies
        except Exception as e:
            log(f"加载Cookie失败: {e}", 'ERROR')
    else:
        log(f"Cookie配置文件不存在: {config_file}", 'ERROR')
    return BILIBILI_COOKIES

def get_user_stats(cookies):
    """获取用户统计数据"""
    url = f"https://api.bilibili.com/x/space/acc/info?mid={cookies['DedeUserID']}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://space.bilibili.com',
        'Cookie': f"SESSDATA={cookies.get('SESSDATA', '')}; bili_jct={cookies.get('bili_jct', '')}"
    }
    
    try:
        log(f"请求用户信息: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        log(f"用户信息响应: code={data.get('code')}, message={data.get('message', 'N/A')}")
        
        if data.get('code') == 0:
            info = data.get('data', {})
            return {
                'name': info.get('name', ''),
                'face': info.get('face', ''),
                'sign': info.get('sign', ''),
                'follower': info.get('follower', 0),
                'following': info.get('following', 0),
                'level': info.get('level', 0),
            }
        elif data.get('code') == -401:
            log("❌ Cookie已过期，需要重新登录获取！", 'ERROR')
            return None
        else:
            log(f"获取用户信息失败: {data.get('message', '未知错误')}", 'ERROR')
            return None
    except Exception as e:
        log(f"获取用户信息异常: {e}", 'ERROR')
        traceback.print_exc()
    return None

def get_user_videos(cookies, pn=1, ps=20):
    """获取用户视频列表"""
    url = "https://api.bilibili.com/x/space/wbi/arc/search"
    
    params = {
        'mid': cookies['DedeUserID'],
        'pn': pn,
        'ps': ps,
        'order': 'pubdate',
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://space.bilibili.com',
        'Cookie': f"SESSDATA={cookies.get('SESSDATA', '')}; bili_jct={cookies.get('bili_jct', '')}"
    }
    
    try:
        log(f"请求视频列表...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        data = response.json()
        log(f"视频列表响应: code={data.get('code')}")
        
        if data.get('code') == 0:
            videos = data.get('data', {}).get('list', {}).get('vlist', [])
            log(f"获取到 {len(videos)} 个视频")
            return videos
        elif data.get('code') == -401:
            log("❌ Cookie已过期，无法获取视频列表", 'ERROR')
            return []
        else:
            log(f"获取视频列表失败: {data.get('message', '未知错误')}", 'WARN')
    except Exception as e:
        log(f"获取视频列表异常: {e}", 'ERROR')
        traceback.print_exc()
    return []

def analyze_video_performance(videos):
    """分析视频表现"""
    if not videos:
        return {
            'total_play': 0,
            'total_like': 0,
            'total_comment': 0,
            'avg_play': 0,
            'best_video': None
        }
    
    total_play = sum(v.get('play', 0) for v in videos)
    total_like = sum(v.get('like', 0) for v in videos)
    total_comment = sum(v.get('comment', 0) for v in videos)
    avg_play = total_play // len(videos) if videos else 0
    
    best_video = max(videos, key=lambda x: x.get('play', 0)) if videos else None
    
    return {
        'total_play': total_play,
        'total_like': total_like,
        'total_comment': total_comment,
        'avg_play': avg_play,
        'best_video': best_video
    }

def generate_report(user_info, videos, stats):
    """生成报告"""
    today = datetime.now().strftime('%Y%m%d')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report_dir = '/home/zzyuzhangxing/.openclaw/workspace/data/bilibili/personal'
    os.makedirs(report_dir, exist_ok=True)
    
    report_path = os.path.join(report_dir, f'account_report_{today}.md')
    
    # 生成报告内容
    report = f"""# 📊 老鱼B站账号数据日报 - {datetime.now().strftime('%Y-%m-%d')}

## 👤 账号信息

| 项目 | 数据 |
|------|------|
| **昵称** | {user_info.get('name', 'N/A')} |
| **UID** | {user_info.get('uid', 'N/A')} |
| **等级** | LV{user_info.get('level', 0)} |
| **粉丝数** | {user_info.get('follower', 0):,} |
| **关注数** | {user_info.get('following', 0):,} |
| **签名** | {user_info.get('sign', 'N/A')} |

---

## 📹 视频数据概览

| 指标 | 数值 |
|------|------|
| **视频总数** | {len(videos)} |
| **总播放量** | {stats['total_play']:,} |
| **总点赞数** | {stats['total_like']:,} |
| **总评论数** | {stats['total_comment']:,} |
| **平均播放** | {stats['avg_play']:,} |

---

## 🔥 最佳表现视频

"""
    
    if stats['best_video']:
        best = stats['best_video']
        report += f"""**标题**: {best.get('title', 'N/A')}

**数据**:
- 播放量: {best.get('play', 0):,}
- 点赞数: {best.get('like', 0):,}
- 链接: https://www.bilibili.com/video/{best.get('bvid', '')}

**简介**: {best.get('description', 'N/A')[:100]}...

---

## 📈 最近视频列表 (Top 5)

"""
        for i, v in enumerate(videos[:5], 1):
            report += f"""### {i}. {v.get('title', 'N/A')}
- 👁️ {v.get('play', 0):,} | 👍 {v.get('like', 0):,} | 💬 {v.get('comment', 0):,}
- [视频链接](https://www.bilibili.com/video/{v.get('bvid', '')})

"""
    else:
        report += "暂无视频数据\n\n"
    
    report += f"""---

## 💡 数据洞察

1. **粉丝增长**: 待对比昨日数据
2. **视频表现**: 平均播放 {stats['avg_play']:,}
3. **互动情况**: 待分析

---

**数据采集时间**: {timestamp}  
**下次采集**: 明日 09:00
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    log(f"✅ 报告已保存: {report_path}")
    return report_path

def main():
    """主函数"""
    log("="*60)
    log("📊 老鱼B站账号数据监控")
    log("="*60)
    
    try:
        # 加载Cookie
        cookies = load_cookies()
        
        log(f"🕐 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log(f"🎯 目标账号: UID {cookies['DedeUserID']}")
        
        # 获取账号信息
        log("📥 获取账号信息...")
        user_info = get_user_stats(cookies)
        
        if not user_info:
            log("❌ 无法获取账号信息，可能是Cookie过期", 'ERROR')
            # 生成错误报告
            error_report()
            return 1
        
        log(f"✅ 账号: {user_info.get('name', 'Unknown')}")
        log(f"✅ 粉丝: {user_info.get('follower', 0):,}")
        
        # 获取视频列表
        log("📥 获取视频列表...")
        videos = get_user_videos(cookies)
        log(f"✅ 获取到 {len(videos)} 个视频")
        
        # 分析视频表现
        stats = analyze_video_performance(videos)
        log(f"✅ 总播放: {stats['total_play']:,}")
        
        # 生成报告
        log("📝 生成数据报告...")
        report_path = generate_report(user_info, videos, stats)
        
        log("="*60)
        log("📊 账号数据摘要")
        log("="*60)
        log(f"👤 昵称: {user_info.get('name', 'N/A')}")
        log(f"👥 粉丝: {user_info.get('follower', 0):,}")
        log(f"📹 视频: {len(videos)} 个")
        log(f"▶️  总播放: {stats['total_play']:,}")
        
        if stats['best_video']:
            best = stats['best_video']
            title = best.get('title', 'N/A')[:30]
            log(f"🔥 最佳视频: {title}... ({best.get('play', 0):,}播放)")
        
        log(f"\n✅ 数据报告: {report_path}")
        return 0
        
    except Exception as e:
        log(f"❌ 程序异常: {e}", 'ERROR')
        traceback.print_exc()
        error_report(str(e))
        return 1

def error_report(error_msg="Cookie可能过期"):
    """生成错误报告"""
    today = datetime.now().strftime('%Y%m%d')
    report_dir = '/home/zzyuzhangxing/.openclaw/workspace/data/bilibili/personal'
    os.makedirs(report_dir, exist_ok=True)
    
    report_path = os.path.join(report_dir, f'account_report_{today}.md')
    
    report = f"""# 📊 老鱼B站账号数据日报 - {datetime.now().strftime('%Y-%m-%d')}

## ⚠️ 数据获取异常

**错误信息**: {error_msg}

**可能原因**:
1. B站Cookie已过期
2. 网络连接问题
3. B站API限制

**建议操作**:
1. 登录B站网页版
2. 获取新的Cookie（SESSDATA和bili_jct）
3. 更新配置文件: `~/.openclaw/workspace/config/bilibili_cookies.json`

---

**数据采集时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**状态**: ❌ 失败
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    log(f"✅ 错误报告已保存: {report_path}")

if __name__ == '__main__':
    sys.exit(main())
