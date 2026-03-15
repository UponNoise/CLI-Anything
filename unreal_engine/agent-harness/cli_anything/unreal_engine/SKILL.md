# UE5-CLIANY 技能文档

## 概述
UE5-CLIANY 是一个为 Unreal Engine 5 设计的命令行接口工具集，提供自动化、脚本化和批量操作 UE5 项目的能力。

## 技能功能

### 1. 项目管理
- 创建新的 UE5 项目
- 打开和配置现有项目
- 管理项目模块和插件
- 项目迁移和版本升级

### 2. 构建系统
- 自动化构建流程
- 多平台构建支持
- 并行构建优化
- 构建配置管理

### 3. 编辑器控制
- 启动和关闭 UE5 编辑器
- 执行编辑器命令
- 无头模式运行
- 批量操作自动化

### 4. 资产管理
- 批量导入和导出资产
- 资产迁移和复制
- 引用关系管理
- 资产清理和优化

### 5. 蓝图操作
- 创建和编译蓝图
- 蓝图变量管理
- 蓝图继承和复制
- 蓝图批量操作

### 6. 插件管理
- 插件发现和安装
- 插件启用和禁用
- 自定义插件创建
- 插件依赖管理

### 7. 烹饪和打包
- 内容烹饪和优化
- 多平台打包支持
- 部署配置管理
- 发布流程自动化

## 使用示例

### 基本使用
```python
from core.project import create_project, open_project
from core.build import BuildSystem

# 创建新项目
project = create_project(
    name="MyGame",
    engine_version="5.4.0",
    description="My awesome game"
)

# 打开现有项目
project_info = open_project("MyGame.uproject")

# 构建项目
build_system = BuildSystem("C:/Program Files/Epic Games/UE_5.4")
result = build_system.build_project("MyGame.uproject")
```

### 资产管理示例
```python
from core.asset import AssetManager, ImportOptions

# 初始化资产管理器
asset_manager = AssetManager("MyGame.uproject")

# 配置导入选项
options = ImportOptions(
    import_materials=True,
    import_textures=True,
    auto_generate_collision=True
)

# 导入资产
asset_path = asset_manager.import_asset(
    source_path="Character.fbx",
    destination_path="/Game/Characters/Main",
    options=options
)
```

### 插件管理示例
```python
from core.plugin import PluginManager

# 初始化插件管理器
plugin_manager = PluginManager(
    engine_path="C:/Program Files/Epic Games/UE_5.4",
    project_path="MyGame.uproject"
)

# 列出所有插件
plugins = plugin_manager.list_plugins(include_engine=True)

# 启用插件
plugin_manager.enable_plugin("MyPlugin", True)
```

## 配置要求

### 系统要求
- **操作系统**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- **Python**: 3.8 或更高版本
- **Unreal Engine**: 5.0 或更高版本
- **磁盘空间**: 至少 10GB 可用空间

### 环境配置
1. 设置 UE5 引擎路径:
   ```bash
   export UE5_ENGINE_PATH="C:/Program Files/Epic Games/UE_5.4"
   ```

2. 安装 Python 依赖:
   ```bash
   pip install -e .
   ```

3. 验证安装:
   ```bash
   python -c "from core.build import BuildSystem; print('安装成功！')"
   ```

## 故障排除

### 常见问题

#### Q1: 引擎路径未找到
**解决方案**:
```python
import os
from utils.ue_backend import UEEngineLocator

# 自动检测引擎
locator = UEEngineLocator()
engines = locator.find_all_engines()
if engines:
    engine_path = engines[0].path
else:
    # 手动设置
    engine_path = Path(os.environ.get("UE5_ENGINE_PATH"))
```

#### Q2: 构建失败
**解决方案**:
1. 清理构建缓存:
   ```python
   build_system.clean_project(project_path)
   ```

2. 重新生成项目文件:
   ```python
   build_system.generate_project_files(project_path)
   ```

3. 检查依赖:
   ```python
   # 验证项目依赖
   from core.project import analyze_dependencies
   dependencies = analyze_dependencies(project_path)
   ```

#### Q3: 资产导入失败
**解决方案**:
1. 检查文件格式支持
2. 简化导入选项
3. 查看编辑器日志

## 最佳实践

### 1. 错误处理
```python
from core.build import BuildError
from core.editor import EditorError

try:
    result = build_system.build_project(project_path)
    if not result["success"]:
        # 处理构建错误
        handle_build_error(result)
except BuildError as e:
    # 记录并通知
    log_error(e)
    notify_team(e)
except Exception as e:
    # 通用错误处理
    handle_unexpected_error(e)
```

### 2. 性能优化
```python
# 使用并行构建
build_options = BuildOptions(parallel=8)

# 使用迭代式烹饪
cook_options = CookOptions(iterative=True)

# 批量操作优化
def batch_operation(items):
    """批量操作减少开销"""
    with Progress() as progress:
        task = progress.add_task("Processing...", total=len(items))
        for item in items:
            process_item(item)
            progress.update(task, advance=1)
```

### 3. 配置管理
```python
import json
from pathlib import Path

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return self.default_config()
    
    def save_config(self):
        """保存配置"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
```

## 扩展开发

### 添加新模块
1. 在 `core/` 目录创建新模块文件
2. 定义模块接口和功能
3. 添加单元测试
4. 更新文档

### 自定义插件
1. 使用插件模板创建
2. 实现插件功能
3. 测试插件集成
4. 发布插件

## 支持资源

### 文档
- [UNREAL_ENGINE.md](UNREAL_ENGINE.md) - 详细技术文档
- [API 参考](docs/api/) - 完整 API 文档
- [示例代码](examples/) - 使用示例

### 社区
- [GitHub Issues](https://github.com/oc-cliany/ue5-cliany/issues) - 问题报告
- [Discord](https://discord.gg/ue5cliany) - 社区讨论
- [Wiki](https://github.com/oc-cliany/ue5-cliany/wiki) - 知识库

### 更新日志
- **v1.0.0** (2026-03-15): 初始发布
- 查看 [CHANGELOG.md](CHANGELOG.md) 获取详细更新信息

## 许可证
本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---
*文档版本: 1.0.0*
*最后更新: 2026-03-15*
*UE5-CLIANY 项目团队*