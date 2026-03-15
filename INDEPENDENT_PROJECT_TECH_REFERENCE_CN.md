# 独立项目发布与技术参考文档

## 1. 文档定位

本文件用于以下三类目的：

1. 记录项目目标与当前实现状态。
2. 作为独立发布时的合规与版权参考。
3. 作为后续版本迭代、功能验收与技术交接的基线文档。

建议每次发布前后都更新本文件。

---

## 2. 独立发布合规要求（MIT）

在 MIT License 下，你可以基于上游项目进行修改并独立发布，但应满足以下要求：

1. 保留上游 MIT 许可文本。
2. 保留上游版权声明。
3. 明确标注本项目来源与修改范围。
4. 不暗示上游官方背书。
5. 对新增代码可增加你自己的版权声明，与上游声明并存。

### 2.1 README 来源声明模板

可在 README 的开头或 License 章节中加入如下模板：

This project is derived from HKUDS/CLI-Anything and distributed under the MIT License.
Portions of this software are Copyright (c) 2024 cli-anything contributors.
Additional modifications are Copyright (c) 2026 <YourName/YourOrg>.

### 2.2 LICENSE 保留与补充模板

建议保留原 MIT License 全文，并在文件头部追加说明：

This project includes code derived from HKUDS/CLI-Anything.
Original license: MIT License.
Original copyright: (c) 2024 cli-anything contributors.
Additional modifications: (c) 2026 <YourName/YourOrg>.

---

## 3. 项目目标（可持续维护版）

### 3.1 总目标

将 cli-anything 插件及 UE5 扩展能力整理为可独立发布、可审计、可维护的工程交付件。

### 3.2 阶段目标

1. 发布合规化
- 元数据完整。
- 版本一致。
- 测试证据可追溯。

2. 工程规范化
- 单一事实来源目录（避免重复树）。
- 忽略规则稳定（不纳入生成产物）。
- 关键文档齐全。

3. 外部可用化
- 具备公开 Release。
- 具备安装与验证说明。
- 支持后续 Option 3（官方目录）提交。

---

## 4. 已实现功能台账（截至 v1.1.0）

### 4.1 插件层

1. 命令集
- /cli-anything
- /cli-anything:refine
- /cli-anything:test
- /cli-anything:validate
- /cli-anything:list

2. 发布要件
- plugin.json 元数据已补齐版本、许可证、仓库、支持信息。
- README 版本历史已更新到 1.1.0。
- setup 脚本版本已同步到 1.1.0。

3. 验证证据
- TESTING.md 记录了 Windows 下的等价验证流程与结果。

### 4.2 UE5 扩展层

1. 结构治理
- 已移除重复 source 树，仅保留单一路径实现。
- 已清理 coverage 与测试报告产物，避免污染版本库。

2. 文档治理
- UE harness README 已补充当前能力边界与限制说明。
- tests/TEST.md 已建立计划与验证记录框架。

3. 发布状态
- 已完成 GitHub Release：v1.1.0。

---

## 5. 技术架构参考

### 5.1 插件目录参考

- .claude-plugin/plugin.json
- commands/
- scripts/setup-cli-anything.sh
- verify-plugin.sh
- README.md
- TESTING.md
- PUBLISHING.md

### 5.2 关键设计点

1. 命令驱动工作流
- 通过 commands 下的标准化命令定义实现工具编排。

2. 方法论约束
- 通过 HARNESS.md 约束生成流程、测试策略和交付格式。

3. 验证策略
- 优先结构校验 + 元数据校验。
- 跨平台场景下提供等价验证命令与证据文档。

4. 版本治理
- 统一维护 plugin.json、README、脚本、tag/release 的版本一致性。

---

## 6. 发布检查清单（建议每次发布前执行）

1. 版本一致性
- plugin.json version
- README 版本记录
- setup 脚本版本
- git tag

2. 合规性
- LICENSE 存在且完整
- README 来源声明与修改声明完整
- 无凭据、无敏感信息

3. 质量与证据
- 验证脚本可执行（或有等价验证）
- TESTING.md 已更新并对应本次版本
- 仓库工作区干净

4. 分发完整性
- release notes 说明新增、限制、验证方式
- 安装与使用说明可复现

---

## 7. 变更记录模板（可复制）

### [Version x.y.z] - YYYY-MM-DD

新增
- 

修复
- 

改进
- 

兼容性说明
- 

验证
- 

已知限制
- 

---

## 8. 下一步建议（面向 Option 3）

1. 增加 SECURITY.md（漏洞提交流程）。
2. 增加 CHANGELOG.md（正式版本变更历史）。
3. 增加自动化 CI（至少做 plugin.json 校验、必需文件校验）。
4. 将发布验证结果自动写入可追溯产物。

---

文档维护责任人：<YourName>
最后更新：2026-03-16
