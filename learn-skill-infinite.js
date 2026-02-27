#!/usr/bin/env node
/**
 * 无限技能学习脚本 - 从ClawHub动态搜索并安装技能
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const WORKSPACE = path.join(process.env.HOME, '.openclaw/workspace');
const LOG_FILE = path.join(WORKSPACE, 'learn-cron.log');
const STATUS_FILE = path.join(WORKSPACE, '.skill-install-infinite.json');

// 搜索关键词列表（覆盖不同领域）
const SEARCH_KEYWORDS = [
  'agent', 'automation', 'ai', 'data', 'web', 'api', 'cloud',
  'github', 'slack', 'discord', 'twitter', 'email', 'calendar',
  'search', 'image', 'video', 'audio', 'document', 'file',
  'database', 'security', 'monitor', 'report', 'analysis',
  'workflow', 'integration', 'notification', 'schedule', 'task'
];

function log(msg) {
  const timestamp = new Date().toLocaleString('zh-CN');
  const logMsg = `[${timestamp}] ${msg}`;
  console.log(logMsg);
  fs.appendFileSync(LOG_FILE, logMsg + '\n');
}

function getInstalledSkills() {
  const skillsDir = path.join(WORKSPACE, 'skills');
  if (!fs.existsSync(skillsDir)) return new Set();

  const skills = fs.readdirSync(skillsDir, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);

  return new Set(skills);
}

function getStatus() {
  if (fs.existsSync(STATUS_FILE)) {
    try {
      return JSON.parse(fs.readFileSync(STATUS_FILE, 'utf8'));
    } catch (e) {
      return { tried: [], keywordIndex: 0 };
    }
  }
  return { tried: [], keywordIndex: 0 };
}

function saveStatus(status) {
  fs.writeFileSync(STATUS_FILE, JSON.stringify(status, null, 2));
}

function searchSkills(keyword) {
  try {
    const result = execSync(`clawhub search "${keyword}" --limit 50 2>&1`, {
      cwd: WORKSPACE,
      encoding: 'utf8',
      timeout: 30000
    });

    // 解析文本输出，提取技能名称
    const lines = result.split('\n');
    const skills = [];

    for (const line of lines) {
      // 匹配格式: "skill-name  Description  (score)"
      const match = line.match(/^([a-z0-9-]+)\s{2,}/);
      if (match && match[1] && !match[1].includes('Searching')) {
        skills.push(match[1]);
      }
    }

    return skills;
  } catch (e) {
    log(`⚠️ 搜索失败 (${keyword}): ${e.message}`);
    return [];
  }
}

function installSkill(skillName) {
  try {
    log(`📦 安装: ${skillName}`);

    const result = execSync(`clawhub install ${skillName} 2>&1`, {
      cwd: WORKSPACE,
      encoding: 'utf8',
      timeout: 60000
    });

    log(`✅ 安装成功: ${skillName}`);
    return { success: true };
  } catch (e) {
    const errorMsg = e.message || '';

    // 跳过已知问题
    if (errorMsg.includes('already installed') || errorMsg.includes('已存在')) {
      log(`⚠️ 已安装: ${skillName}`);
      return { success: true, alreadyInstalled: true };
    }

    if (errorMsg.includes('not found') || errorMsg.includes('Skill not found')) {
      log(`⚠️ 技能不存在: ${skillName}`);
      return { success: false, notFound: true };
    }

    if (errorMsg.includes('VirusTotal') || errorMsg.includes('suspicious')) {
      log(`⚠️ 安全标记跳过: ${skillName}`);
      return { success: false, securityFlag: true };
    }

    if (errorMsg.includes('Rate limit')) {
      log(`⏳ Rate limit，跳过: ${skillName}`);
      return { success: false, rateLimit: true };
    }

    log(`❌ 安装失败: ${skillName} - ${errorMsg.substring(0, 100)}`);
    return { success: false, error: errorMsg };
  }
}

async function main() {
  log('');
  log('============================================================');
  log('🚀 无限技能学习 - ClawHub动态搜索版');
  log('============================================================');

  const installed = getInstalledSkills();
  const status = getStatus();

  log(`📊 当前已安装: ${installed.size} 个技能`);

  // 轮询搜索关键词
  const keyword = SEARCH_KEYWORDS[status.keywordIndex % SEARCH_KEYWORDS.length];
  log(`🔍 搜索关键词: ${keyword}`);

  // 搜索技能
  const foundSkills = searchSkills(keyword);
  log(`📚 找到 ${foundSkills.length} 个技能`);

  if (foundSkills.length === 0) {
    log('⚠️ 未找到技能，尝试下一个关键词');
    status.keywordIndex++;
    saveStatus(status);
    return;
  }

  // 过滤未安装和未尝试的技能
  const toInstall = foundSkills.filter(s =>
    !installed.has(s) && !status.tried.includes(s)
  );

  if (toInstall.length === 0) {
    log('✅ 当前关键词下的技能已全部处理');
    status.keywordIndex++;
    saveStatus(status);
    return;
  }

  log(`🎯 待安装: ${toInstall.length} 个技能`);

  // 安装前3个技能
  const batch = toInstall.slice(0, 3);
  let successCount = 0;

  for (const skill of batch) {
    const result = installSkill(skill);
    if (result.success) {
      successCount++;
    }
    status.tried.push(skill);

    // 间隔5秒，避免rate limit
    await new Promise(r => setTimeout(r, 5000));
  }

  // 定期清理tried列表（保留最近1000个）
  if (status.tried.length > 1000) {
    status.tried = status.tried.slice(-500);
  }

  // 如果当前关键词安装成功，下次继续用这个关键词
  // 否则切换到下一个关键词
  if (successCount === 0) {
    status.keywordIndex++;
  }

  saveStatus(status);

  log('');
  log('============================================================');
  log(`✅ 完成! 成功安装: ${successCount}/${batch.length}`);
  log(`📊 总计: ${installed.size + successCount} 个技能`);
  log(`🔍 下次关键词: ${SEARCH_KEYWORDS[status.keywordIndex % SEARCH_KEYWORDS.length]}`);
  log('============================================================');
}

main().catch(e => {
  log(`❌ 错误: ${e.message}`);
  process.exit(1);
});
