# UE5-CLIANY 模块文档

## 项目概述和架构

### 项目目标
UE5-CLIANY 是一个为 Unreal Engine 5 设计的命令行接口工具集，旨在提供自动化、脚本化和批量操作 UE5 项目的能力。通过 Python API，开发者可以：

- 自动化构建、打包和部署流程
- 批量管理项目资产和蓝图
- 控制编辑器行为和执行命令
- 管理插件和项目配置
- 实现 CI/CD 流水线集成

### 技术栈
- **编程语言**: Python 3.8+
- **核心框架**: 原生 Python，无外部依赖
- **目标平台**: Windows, macOS, Linux
- **UE5 版本**: 5.0 - 5.5+
- **构建系统**: UBT (Unreal Build Tool), UAT (Unreal Automation Tool)

### 架构设计
模块采用分层架构设计：

```
UE5-CLIANY/
├── core/                    # 核心功能模块
│   ├── project.py          # 项目管理
│   ├── build.py           # 编译系统
│   ├── editor.py          # 编辑器控制
│   ├── asset.py           # 资源管理
│   ├── blueprint.py       # 蓝图操作
│   ├── plugin.py          # 插件管理
│   ├── cook.py            # 打包烘焙
│   └── packaging.py       # 发布配置
├── utils/                  # 工具和辅助功能
│   └── ue_backend.py      # UE引擎检测
└── tests/                  # 测试套件
```

## 模块详细说明

### 1. project.py - 项目管理

#### 功能概述
提供 UE5 项目的创建、配置、分析和迁移功能。

#### 主要类
- **ProjectManager**: 项目管理器，处理项目生命周期
- **ProjectInfo**: 项目信息数据类
- **ProjectTemplate**: 项目模板配置

#### 核心方法
```python
# 创建新项目
create_project(name: str, template: str, path: Path) -> ProjectInfo

# 打开现有项目
open_project(project_path: Path) -> ProjectInfo

# 分析项目依赖
analyze_dependencies(project_path: Path) -> Dict[str, Any]

# 迁移项目版本
migrate_project(source_path: Path, target_version: str) -> bool
```

### 2. build.py - 编译系统

#### 功能概述
处理 UBT (Unreal Build Tool) 和 UAT (Unreal Automation Tool) 命令，提供 Pythonic 接口进行构建、清理和编译操作。

#### 主要类
- **BuildSystem**: 构建系统接口
- **BuildOptions**: 构建选项配置
- **BuildConfiguration**: 构建配置枚举
- **BuildTarget**: 构建目标枚举
- **BuildPlatform**: 目标平台枚举

#### 核心方法
```python
# 构建项目
build_project(project_path: Path, options: BuildOptions) -> Dict[str, Any]

# 清理构建产物
clean_project(project_path: Path, options: BuildOptions) -> Dict[str, Any]

# 生成项目文件
generate_project_files(project_path: Path, ide: str) -> Dict[str, Any]

# 编译特定模块
compile_module(project_path: Path, module_name: str) -> bool
```

#### 使用示例
```python
from core.build import BuildSystem, BuildOptions, BuildConfiguration, BuildTarget

# 初始化构建系统
engine_path = Path("C:/Program Files/Epic Games/UE_5.4")
build_system = BuildSystem(engine_path)

# 配置构建选项
options = BuildOptions(
    configuration=BuildConfiguration.DEVELOPMENT,
    target=BuildTarget.EDITOR,
    platform=BuildPlatform.WIN64,
    verbose=True,
    parallel=8
)

# 执行构建
result = build_system.build_project(
    project_path=Path("D:/Projects/MyGame/MyGame.uproject"),
    options=options
)

if result["success"]:
    print("构建成功！")
else:
    print(f"构建失败: {result['stderr']}")
```

### 3. editor.py - 编辑器控制

#### 功能概述
提供 UE5 编辑器的启动、命令执行和自动化控制功能，支持无头模式运行。

#### 主要类
- **EditorManager**: 编辑器管理器
- **EditorOptions**: 编辑器启动选项
- **CommandletOptions**: 命令执行选项
- **EditorMode**: 编辑器模式枚举
- **GameMode**: 游戏模式枚举

#### 核心方法
```python
# 启动编辑器
launch(options: EditorOptions, wait: bool = False) -> subprocess.Popen

# 执行命令
run_commandlet(commandlet: str, args: List[str]) -> Dict[str, Any]

# 重新保存包
run_resave_packages(package_path: str) -> Dict[str, Any]

# 修复重定向
run_fixup_redirects(package_path: str) -> Dict[str, Any]
```

#### 使用示例
```python
from core.editor import EditorManager, EditorOptions, EditorMode

# 初始化编辑器管理器
editor = EditorManager(
    engine_path=Path("C:/Program Files/Epic Games/UE_5.4"),
    project_path=Path("D:/Projects/MyGame/MyGame.uproject")
)

# 配置编辑器选项
options = EditorOptions(
    map="/Game/Maps/MainMenu",
    game_mode="Game",
    mode=EditorMode.HEADLESS,
    windowed=True,
    res_x=1920,
    res_y=1080,
    unattended=True
)

# 启动编辑器（无头模式）
process = editor.launch(options, wait=False)

# 执行命令
result = editor.run_commandlet("ResavePackages", ["-Package=/Game/Textures"])
```

### 4. asset.py - 资源管理

#### 功能概述
提供资产导入、导出、迁移、列表、引用查找和删除功能。

#### 主要类
- **AssetManager**: 资产管理器
- **AssetInfo**: 资产信息数据类
- **ImportOptions**: 导入选项配置
- **AssetType**: 资产类型枚举

#### 核心方法
```python
# 导入资产
import_asset(source_path: Path, destination_path: str, options: ImportOptions) -> str

# 导出资产
export_asset(asset_path: str, output_path: Path, format: str) -> Path

# 迁移资产
migrate_assets(asset_paths: List[str], target_project: Path) -> Dict[str, AssetImportStatus]

# 列出资产
list_assets(path: str, recursive: bool, filter_type: AssetType) -> List[AssetInfo]

# 查找引用
find_references(asset_path: str) -> List[str]

# 删除资产
delete_asset(asset_path: str, force: bool) -> bool
```

#### 使用示例
```python
from core.asset import AssetManager, ImportOptions, AssetType
from pathlib import Path

# 初始化资产管理器
project_path = Path("D:/Projects/MyGame/MyGame.uproject")
asset_manager = AssetManager(project_path)

# 导入 FBX 模型
import_options = ImportOptions(
    import_materials=True,
    import_textures=True,
    import_lods=True,
    auto_generate_collision=True
)

asset_path = asset_manager.import_asset(
    source_path=Path("D:/Models/Character.fbx"),
    destination_path="/Game/Characters/MainCharacter",
    options=import_options
)

print(f"资产导入成功: {asset_path}")

# 列出所有材质资产
materials = asset_manager.list_assets(
    path="/Game",
    recursive=True,
    filter_type=AssetType.MATERIAL
)

for material in materials:
    print(f"材质: {material.name}, 路径: {material.path}")
```

### 5. blueprint.py - 蓝图操作

#### 功能概述
提供蓝图创建、编译、列表和复制功能，支持各种蓝图类型。

#### 主要类
- **BlueprintManager**: 蓝图管理器
- **BlueprintInfo**: 蓝图信息数据类
- **CreateBlueprintOptions**: 蓝图创建选项
- **BlueprintType**: 蓝图类型枚举
- **BlueprintVariableType**: 蓝图变量类型枚举

#### 核心方法
```python
# 创建蓝图
create_blueprint(name: str, path: str, options: CreateBlueprintOptions) -> str

# 编译蓝图
compile_blueprint(blueprint_path: str) -> bool

# 列出蓝图
list_blueprints(path: str, recursive: bool, filter_type: BlueprintType) -> List[BlueprintInfo]

# 复制蓝图
duplicate_blueprint(source_path: str, new_name: str, target_path: str) -> str
```

#### 使用示例
```python
from core.blueprint import BlueprintManager, CreateBlueprintOptions, BlueprintType

# 初始化蓝图管理器
project_path = Path("D:/Projects/MyGame/MyGame.uproject")
blueprint_manager = BlueprintManager(project_path)

# 创建角色蓝图
options = CreateBlueprintOptions(
    parent_class="Character",
    add_default_components=True,
    add_default_variables=True,
    compile_after_create=True
)

blueprint_path = blueprint_manager.create_blueprint(
    name="BP_PlayerCharacter",
    path="/Game/Blueprints/Characters",
    options=options
)

print(f"蓝图创建成功: {blueprint_path}")

# 列出所有 Actor 蓝图
actor_blueprints = blueprint_manager.list_blueprints(
    path="/Game/Blueprints",
    recursive=True,
    filter_type=BlueprintType.ACTOR
)

for bp in actor_blueprints:
    print(f"蓝图: {bp.name}, 父类: {bp.parent_class}")
```

### 6. plugin.py - 插件管理

#### 功能概述
处理插件发现、安装、启用、禁用和创建，支持项目插件和引擎插件。

#### 主要类
- **PluginManager**: 插件管理器
- **PluginInfo**: 插件信息数据类
- **PluginType**: 插件类型枚举
- **PluginCategory**: 插件分类枚举
- **PluginSource**: 插件来源枚举

#### 核心方法
```python
# 列出插件
list_plugins(include_engine: bool) -> List[PluginInfo]

# 启用/禁用插件
enable_plugin(plugin_name: str, enable: bool) -> bool

# 安装插件
install_plugin(source: str, plugin_name: str, destination: Path) -> PluginInfo

# 创建插件
create_plugin(name: str, template: str, output_dir: Path) -> PluginInfo
```

#### 使用示例
```python
from core.plugin import PluginManager, PluginType, PluginCategory

# 初始化插件管理器
engine_path = Path("C:/Program Files/Epic Games/UE_5.4")
project_path = Path("D:/Projects/MyGame/MyGame.uproject")
plugin_manager = PluginManager(engine_path, project_path)

# 列出所有插件
all_plugins = plugin_manager.list_plugins(include_engine=True)

for plugin in all_plugins:
    status = "已启用" if plugin.enabled else "已禁用"
    print(f"插件: {plugin.friendly_name}, 状态: {status}, 类型: {plugin.plugin_type.value}")

# 启用插件
plugin_manager.enable_plugin("MyCustomPlugin", True)

# 创建新插件
new_plugin = plugin_manager.create_plugin(
    name="MyRuntimePlugin",
    template="Runtime",
    output_dir=project_path / "Plugins",
    plugin_type=PluginType.RUNTIME,
    category=PluginCategory.UTILITIES,
    description="My custom runtime plugin"
)
```

### 7. cook.py - 打包烘焙

#### 功能概述
处理内容烹饪、暂存和打包操作，使用 UAT 进行烹饪和打包操作。

#### 主要类
- **CookManager**: 烹饪管理器
- **CookOptions**: 烹饪选项配置
- **PackageOptions**: 打包选项配置
- **CookResult**: 烹饪结果数据类
- **CookTarget**: 烹饪目标枚举
- **CookFlavor**: 烹饪风味枚举

#### 核心方法
```python
# 烹饪内容
cook_content(options: CookOptions, project_path: Path) -> CookResult

# 烹饪并暂存
cook_and_stage(options: CookOptions, project_path: Path) -> CookResult

# 打包项目
package_project(options: PackageOptions, project_path: Path) -> CookResult

# 获取烹饪状态
get_cook_status(project_path: Path) -> Dict[str, Any]

# 清理烹饪内容
clean_cooked_content(project_path: Path, platform: str, config: str) -> bool
```

#### 使用示例
```python
from core.cook import CookManager, CookOptions, CookTarget, CookFlavor
from pathlib import Path

# 初始化烹饪管理器
engine_path = Path("C:/Program Files/Epic Games/UE_5.4")
project_path = Path("D:/Projects/MyGame/MyGame.uproject")
cook_manager = CookManager(engine_path, project_path)

# 配置烹饪选项
cook_options = CookOptions(
    target=CookTarget.WINDOWS,
    flavor=CookFlavor.SHIPPING,
    maps=["/Game/Maps/MainMenu", "/Game/Maps/Level1"],
    compressed=True,
    iterative=True,
    staging_directory=project_path.parent / "StagedBuilds"
)

# 执行烹饪
result = cook_manager.cook_content(cook_options)

if result.success:
    print(f"烹饪成功！耗时: {result.duration_seconds:.2f}秒")
    print(f"烹饪内容目录: {result.cooked_content_dir}")
else:
    print(f"烹饪失败: {result.errors}")
```

### 8. packaging.py - 发布配置

#### 功能概述
处理打包配置、部署选项和平台特定设置，支持多种打包格式和部署目标。

#### 主要类
- **PackagingManager**: 打包管理器
- **PackagingConfig**: 打包配置数据类
- **PackagingFormat**: 打包格式枚举
- **PackagingPlatform**: 打包平台枚举
- **DeploymentTarget**: 部署目标枚举

#### 核心方法
```python
# 创建打包配置
create_packaging_config(platform: PackagingPlatform, configuration: str) -> PackagingConfig

# 验证配置
validate_config(config: PackagingConfig) -> List[str]

# 打包项目
package_project(config: PackagingConfig) -> Path

# 创建安装程序
create_installer(config: PackagingConfig, installer_config: Dict[str, Any]) -> Path

# 部署包
deploy_package(config: PackagingConfig, target: DeploymentTarget) -> bool
```

#### 使用示例
```python
from core.packaging import PackagingManager, PackagingConfig, PackagingPlatform, DeploymentTarget
from pathlib import Path

# 初始化打包管理器
engine_path = Path("C:/Program Files/Epic Games/UE_5.4")
project_path = Path("D:/Projects/MyGame/MyGame.uproject")
packaging_manager = PackagingManager(engine_path, project_path)

# 创建打包配置
config = packaging_manager.create_packaging_config(
    platform=PackagingPlatform.WINDOWS,
    configuration="Shipping",
    output_dir=Path("./Packaged"),
    include_debug_symbols=False,
    deployment_targets=[DeploymentTarget.LOCAL, DeploymentTarget.STEAM]
)

# 验证配置
errors = packaging_manager.validate_config(config)
if errors:
    print(f"配置错误: {errors}")
else:
    # 执行打包
    output_path = packaging_manager.package_project(config)
    print(f"打包完成！输出目录: {output_path}")
    
    # 部署到 Steam
    packaging_manager.deploy_package(config, DeploymentTarget.STEAM)
```

## API 参考文档

### 核心模块 API

#### BuildSystem 类
```python
class BuildSystem:
    """UE5 构建系统接口"""
    
    def __init__(self, engine_path: Union[str, Path]):
        """初始化构建系统"""
    
    def build_project(
        self,
        project_path: Union[str, Path],
        options: Optional[BuildOptions] = None,
        rebuild: bool = False
    ) -> Dict[str, Any]:
        """构建 UE5 项目"""
    
    def clean_project(
        self,
        project_path: Union[str, Path],
        options: Optional[BuildOptions] = None
    ) -> Dict[str, Any]:
        """清理构建产物"""
    
    def generate_project_files(
        self,
        project_path: Union[str, Path],
        ide: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成 IDE 项目文件"""
```

#### EditorManager 类
```python
class EditorManager:
    """UE5 编辑器管理器"""
    
    def __init__(
        self,
        engine_path: Union[str, Path],
        project_path: Optional[Union[str, Path]] = None
    ):
        """初始化编辑器管理器"""
    
    def launch(
        self,
        options: Optional[EditorOptions] = None,
        wait: bool = False
    ) -> Union[subprocess.Popen, subprocess.CompletedProcess]:
        """启动 UE5 编辑器"""
    
    def run_commandlet(
        self,
        commandlet: str,
        args: Optional[List[str]] = None,
        options: Optional[CommandletOptions] = None
    ) -> Dict[str, Any]:
        """运行编辑器命令"""
```

#### AssetManager 类
```python
class AssetManager:
    """UE5 资产管理器"""
    
    def __init__(self, project_path: Path, engine_path: Optional[Path] = None):
        """初始化资产管理器"""
    
    def import_asset(
        self,
        source_path: Path,
        destination_path: str,
        options: Optional[ImportOptions] = None
    ) -> str:
        """导入资产到项目"""
    
    def list_assets(
        self,
        path: str = "/Game",
        recursive: bool = True,
        filter_type: Optional[AssetType] = None
    ) -> List[AssetInfo]:
        """列出项目中的资产"""
```

#### BlueprintManager 类
```python
class BlueprintManager:
    """UE5 蓝图管理器"""
    
    def __init__(self, project_path: Path, engine_path: Optional[Path] = None):
        """初始化蓝图管理器"""
    
    def create_blueprint(
        self,
        name: str,
        path: str,
        options: Optional[CreateBlueprintOptions] = None
    ) -> str:
        """创建新蓝图"""
    
    def compile_blueprint(self, blueprint_path: str) -> bool:
        """编译蓝图"""
```

#### PluginManager 类
```python
class PluginManager:
    """UE5 插件管理器"""
    
    def __init__(
        self,
        engine_path: Optional[Path] = None,
        project_path: Optional[Path] = None,
        environment: Optional[UEEnvironment] = None
    ):
        """初始化插件管理器"""
    
    def list_plugins(self, include_engine: bool = True) -> List[PluginInfo]:
        """列出所有可用插件"""
    
    def enable_plugin(self, plugin_name: str, enable: bool = True) -> bool:
        """启用或禁用插件"""
```

#### CookManager 类
```python
class CookManager:
    """UE5 烹饪和打包管理器"""
    
    def __init__(
        self,
        engine_path: Union[str, Path],
        project_path: Optional[Union[str, Path]] = None
    ):
        """初始化烹饪管理器"""
    
    def cook_content(
        self,
        options: Optional[CookOptions] = None,
        project_path: Optional[Union[str, Path]] = None
    ) -> CookResult:
        """烹饪项目内容"""
    
    def package_project(
        self,
        options: Optional[PackageOptions] = None,
        project_path: Optional[Union[str, Path]] = None
    ) -> CookResult:
        """打包项目"""
```

#### PackagingManager 类
```python
class PackagingManager:
    """UE5 项目打包管理器"""
    
    def __init__(self, engine_path: Path, project_path: Path):
        """初始化打包管理器"""
    
    def create_packaging_config(
        self,
        platform: PackagingPlatform,
        configuration: str = "Development",
        **kwargs
    ) -> PackagingConfig:
        """创建打包配置"""
    
    def package_project(self, config: PackagingConfig) -> Path:
        """打包 UE5 项目"""
```

### 数据类参考

#### BuildOptions
```python
@dataclass
class BuildOptions:
    """构建选项配置"""
    configuration: BuildConfiguration = BuildConfiguration.DEVELOPMENT
    target: BuildTarget = BuildTarget.EDITOR
    platform: BuildPlatform = BuildPlatform.WIN64
    verbose: bool = False
    parallel: int = 0
    clean: bool = False
    rebuild: bool = False
    extra_args: List[str] = field(default_factory=list)
```

#### EditorOptions
```python
@dataclass
class EditorOptions:
    """编辑器启动选项"""
    map: Optional[str] = None
    game_mode: Optional[str] = None
    mode: EditorMode = EditorMode.NORMAL
    log: bool = True
    log_window: bool = False
    fullscreen: bool = False
    windowed: bool = True
    res_x: Optional[int] = None
    res_y: Optional[int] = None
    dx11: bool = False
    dx12: bool = False
    vulkan: bool = False
    nosplash: bool = False
    no_slate: bool = False
    unattended: bool = False
    extra_args: List[str] = field(default_factory=list)
```

#### ImportOptions
```python
@dataclass
class ImportOptions:
    """资产导入选项"""
    replace_existing: bool = False
    automated: bool = True
    save: bool = True
    suppress_dialogs: bool = True
    import_materials: bool = True
    import_textures: bool = True
    import_skeleton: bool = True
    import_animations: bool = True
    import_physics: bool = True
    import_lods: bool = True
    import_vertex_colors: bool = True
    import_vertex_normals: bool = True
    import_tangents: bool = True
    import_morph_targets: bool = True
    import_cloth: bool = True
    create_physics_asset: bool = True
    import_as_skeletal: bool = False
    import_rigid_mesh: bool = False
    uniform_scale: float = 1.0
```

#### CookOptions
```python
@dataclass
class CookOptions:
    """烹饪选项"""
    target: CookTarget = CookTarget.WINDOWS
    flavor: CookFlavor = CookFlavor.DEVELOPMENT
    maps: List[str] = field(default_factory=list)
    cultures: List[str] = field(default_factory=list)
    compressed: bool = True
    iterative: bool = False
    skip_editor_content: bool = False
    unversioned_cooked_content: bool = False
    cook_all: bool = False
    cook_maps_only: bool = False
    staging_directory: Optional[Path] = None
    archive: bool = False
    pak: bool = True
    distribution: bool = False
    extra_args: List[str] = field(default_factory=list)
```

## 使用示例和教程

### 快速开始指南

#### 1. 环境设置
```python
# 导入 UE5-CLIANY 模块
from pathlib import Path
from core.build import BuildSystem
from core.editor import EditorManager
from core.asset import AssetManager

# 设置路径
engine_path = Path("C:/Program Files/Epic Games/UE_5.4")
project_path = Path("D:/Projects/MyGame/MyGame.uproject")
```

#### 2. 基本构建流程
```python
# 初始化构建系统
build_system = BuildSystem(engine_path)

# 生成项目文件
build_system.generate_project_files(project_path, "VisualStudio2022")

# 构建项目
result = build_system.build_project(project_path)
if result["success"]:
    print("项目构建成功！")
```

#### 3. 编辑器自动化
```python
# 初始化编辑器管理器
editor = EditorManager(engine_path, project_path)

# 启动无头编辑器
options = EditorOptions(
    mode=EditorMode.HEADLESS,
    unattended=True,
    no_slate=True
)
process = editor.launch(options)

# 执行命令
editor.run_commandlet("ResavePackages", ["-Package=/Game"])
```

### 常见用例示例

#### 用例 1: 批量导入资产
```python
from core.asset import AssetManager, ImportOptions

# 初始化资产管理器
asset_manager = AssetManager(project_path)

# 配置导入选项
import_options = ImportOptions(
    import_materials=True,
    import_textures=True,
    auto_generate_collision=True
)

# 批量导入 FBX 文件
fbx_files = [
    ("Character.fbx", "/Game/Characters/Main"),
    ("Weapon.fbx", "/Game/Weapons/Sword"),
    ("Environment.fbx", "/Game/Environment/Rocks")
]

for fbx_file, dest_path in fbx_files:
    source_path = Path(f"Assets/{fbx_file}")
    if source_path.exists():
        asset_path = asset_manager.import_asset(
            source_path, dest_path, import_options
        )
        print(f"导入成功: {asset_path}")
```

#### 用例 2: 自动化打包流程
```python
from core.cook import CookManager, CookOptions, CookTarget, CookFlavor
from core.packaging import PackagingManager, PackagingConfig, PackagingPlatform

# 初始化管理器
cook_manager = CookManager(engine_path, project_path)
packaging_manager = PackagingManager(engine_path, project_path)

# 烹饪内容
cook_options = CookOptions(
    target=CookTarget.WINDOWS,
    flavor=CookFlavor.SHIPPING,
    compressed=True,
    iterative=True
)
cook_result = cook_manager.cook_content(cook_options)

if cook_result.success:
    # 创建打包配置
    packaging_config = packaging_manager.create_packaging_config(
        platform=PackagingPlatform.WINDOWS,
        configuration="Shipping",
        output_dir=Path("./Packaged")
    )
    
    # 执行打包
    output_path = packaging_manager.package_project(packaging_config)
    print(f"打包完成: {output_path}")
```

#### 用例 3: 插件管理自动化
```python
from core.plugin import PluginManager, PluginType

# 初始化插件管理器
plugin_manager = PluginManager(engine_path, project_path)

# 列出并启用所需插件
required_plugins = ["AdvancedSessions", "OnlineSubsystemSteam"]
for plugin_name in required_plugins:
    plugin_manager.enable_plugin(plugin_name, True)
    print(f"已启用插件: {plugin_name}")

# 创建自定义插件
new_plugin = plugin_manager.create_plugin(
    name="MyGameUtilities",
    template="Runtime",
    plugin_type=PluginType.RUNTIME,
    description="Utility functions for MyGame"
)
```

### 最佳实践

#### 1. 错误处理
```python
from core.build import BuildError
from core.editor import EditorError

try:
    # 尝试构建
    result = build_system.build_project(project_path)
    
    if not result["success"]:
        # 处理构建错误
        print(f"构建失败: {result['stderr']}")
        # 尝试清理后重新构建
        build_system.clean_project(project_path)
        result = build_system.build_project(project_path, rebuild=True)
        
except BuildError as e:
    print(f"构建系统错误: {e}")
    # 记录错误并通知
    log_error(e)
    notify_team(e)
    
except Exception as e:
    print(f"未知错误: {e}")
    # 回滚操作
    rollback_changes()
```

#### 2. 性能优化
```python
# 使用并行构建
build_options = BuildOptions(
    parallel=8,  # 使用 8 个并行进程
    verbose=False  # 减少日志输出
)

# 使用迭代式烹饪
cook_options = CookOptions(
    iterative=True,  # 只烹饪更改的内容
    compressed=True  # 压缩包文件
)

# 批量操作优化
def batch_import_assets(asset_list):
    """批量导入资产，减少编辑器启动次数"""
    # 启动一次编辑器
    editor = EditorManager(engine_path, project_path)
    
    # 批量执行导入
    for asset in asset_list:
        # 使用相同的编辑器实例
        editor.run_commandlet("ImportAssets", asset)
    
    # 关闭编辑器
    editor.terminate()
```

#### 3. 配置管理
```python
import json
from pathlib import Path

class UE5ConfigManager:
    """UE5 配置管理器"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {
            "engine_path": "C:/Program Files/Epic Games/UE_5.4",
            "default_project": None,
            "build_options": {
                "parallel": 4,
                "verbose": False
            },
            "cook_options": {
                "compressed": True,
                "iterative": True
            }
        }
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
```

## 配置和部署指南

### 安装说明

#### 1. 系统要求
- **操作系统**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- **Python**: 3.8 或更高版本
- **Unreal Engine**: 5.0 或更高版本
- **磁盘空间**: 至少 10GB 可用空间

#### 2. 安装步骤
```bash
# 克隆仓库
git clone https://github.com/your-org/ue5-cliany.git
cd ue5-cliany

# 安装依赖（无外部依赖）
# 模块使用纯 Python 实现

# 设置环境变量
export UE5_CLIANY_PATH=/path/to/ue5-cliany
export PATH=$PATH:$UE5_CLIANY_PATH/bin

# 验证安装
python -c "from core.build import BuildSystem; print('安装成功！')"
```

#### 3. 配置 UE5 引擎路径
```python
# 方法 1: 环境变量
import os
engine_path = Path(os.environ.get("UE5_ENGINE_PATH", "C:/Program Files/Epic Games/UE_5.4"))

# 方法 2: 配置文件
config_path = Path("~/.ue5cliany/config.json").expanduser()
if config_path.exists():
    with open(config_path, 'r') as f:
        config = json.load(f)
        engine_path = Path(config["engine_path"])
```

### 配置选项

#### 1. 全局配置
```json
{
  "engine_path": "C:/Program Files/Epic Games/UE_5.4",
  "default_project": "D:/Projects/MyGame/MyGame.uproject",
  "log_level": "INFO",
  "max_parallel_jobs": 8,
  "cache_directory": "~/.ue5cliany/cache",
  "temp_directory": "~/.ue5cliany/temp"
}
```

#### 2. 项目特定配置
```json
{
  "project_name": "MyGame",
  "build_configurations": {
    "development": {
      "configuration": "Development",
      "target": "Editor",
      "platform": "Win64"
    },
    "shipping": {
      "configuration": "Shipping",
      "target": "Game",
      "platform": "Win64"
    }
  },
  "cook_settings": {
    "default_platform": "Windows",
    "default_flavor": "Shipping",
    "always_compress": true
  },
  "deployment_targets": ["Local", "Steam"]
}
```

#### 3. 插件配置
```json
{
  "required_plugins": [
    "AdvancedSessions",
    "OnlineSubsystemSteam",
    "ProceduralMeshComponent"
  ],
  "optional_plugins": [
    "MovieRenderPipeline",
    "DatasmithContent"
  ],
  "plugin_sources": {
    "marketplace": true,
    "github": true,
    "local": true
  }
}
```

### 部署步骤

#### 1. 本地部署
```python
from core.packaging import PackagingManager, PackagingConfig, PackagingPlatform

# 创建打包配置
config = PackagingConfig(
    project_path=project_path,
    platform=PackagingPlatform.WINDOWS,
    configuration="Shipping",
    output_dir=Path("./Dist")
)

# 执行打包
packaging_manager = PackagingManager(engine_path, project_path)
output_path = packaging_manager.package_project(config)

# 验证打包结果
if output_path.exists():
    print(f"本地部署完成: {output_path}")
```

#### 2. Steam 部署
```python
from core.packaging import DeploymentTarget

# 配置 Steam 部署
config.deployment_targets.append(DeploymentTarget.STEAM)

# 执行部署
if packaging_manager.deploy_package(config, DeploymentTarget.STEAM):
    print("Steam 部署成功！")
else:
    print("Steam 部署失败")
```

#### 3. CI/CD 集成
```yaml
# GitHub Actions 示例
name: UE5 Build and Package

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install UE5-CLIANY
      run: |
        git clone https://github.com/your-org/ue5-cliany.git
        cd ue5-cliany
        echo "UE5_CLIANY_PATH=$(pwd)" >> $GITHUB_ENV
    
    - name: Build Project
      run: |
        python -m ue5cliany build \
          --engine-path "C:/Program Files/Epic Games/UE_5.4" \
          --project "MyGame.uproject"
    
    - name: Package for Distribution
      run: |
        python -m ue5cliany package \
          --platform Windows \
          --configuration Shipping \
          --output-dir ./Dist
```

## 故障排除和 FAQ

### 常见问题解答

#### Q1: 如何解决 "Engine not found" 错误？
**A:** 确保正确设置了 UE5 引擎路径：
```python
# 方法 1: 设置环境变量
export UE5_ENGINE_PATH="C:/Program Files/Epic Games/UE_5.4"

# 方法 2: 在代码中指定
from utils.ue_backend import UEEngineLocator
locator = UEEngineLocator()
engines = locator.find_all_engines()
if engines:
    engine_path = engines[0].path
```

#### Q2: 构建失败，显示 "Missing module dependencies" 错误？
**A:** 确保所有依赖模块都已正确配置：
```python
# 重新生成项目文件
build_system.generate_project_files(project_path)

# 清理并重新构建
build_system.clean_project(project_path)
build_system.build_project(project_path, rebuild=True)
```

#### Q3: 编辑器启动失败，如何调试？
**A:** 启用详细日志并检查错误：
```python
# 启用详细日志
options = EditorOptions(
    log=True,
    log_window=True,
    unattended=False  # 禁用无头模式以查看错误
)

# 检查编辑器日志
log_path = project_path.parent / "Saved" / "Logs" / "Editor.log"
if log_path.exists():
    with open(log_path, 'r') as f:
        print(f.read())
```

#### Q4: 资产导入失败，如何处理？
**A:** 检查导入选项和文件格式：
```python
# 验证源文件
source_path = Path("Assets/Model.fbx")
if not source_path.exists():
    print("源文件不存在")
elif source_path.suffix.lower() not in ['.fbx', '.obj', '.dae']:
    print("不支持的格式")

# 尝试简化导入选项
simple_options = ImportOptions(
    import_materials=False,
    import_textures=False,
    auto_generate_collision=False
)
```

### 错误代码说明

#### 构建错误代码
- **B001**: 引擎路径无效
- **B002**: 项目文件不存在
- **B003**: 构建目标不支持
- **B004**: 编译失败
- **B005**: 链接失败

#### 编辑器错误代码
- **E001**: 编辑器启动失败
- **E002**: 命令执行超时
- **E003**: 无头模式不支持
- **E004**: 项目加载失败
- **E005**: 插件冲突

#### 资产错误代码
- **A001**: 资产导入失败
- **A002**: 资产导出失败
- **A003**: 资产迁移失败
- **A004**: 资产引用循环
- **A005**: 资产格式不支持

#### 打包错误代码
- **P001**: 烹饪失败
- **P002**: 暂存失败
- **P003**: 打包失败
- **P004**: 部署失败
- **P005**: 平台不支持

### 调试技巧

#### 1. 启用详细日志
```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ue5cliany.log'),
        logging.StreamHandler()
    ]
)

# 在代码中记录关键信息
logger = logging.getLogger(__name__)
logger.info("开始构建项目...")
```

#### 2. 使用调试模式
```python
from core.build import BuildSystem

# 启用调试模式
build_system = BuildSystem(engine_path, debug=True)

# 构建时捕获详细输出
result = build_system.build_project(
    project_path,
    options=BuildOptions(verbose=True)
)

# 分析输出
if result["stderr"]:
    print("错误输出:", result["stderr"])
```

#### 3. 验证环境
```python
def validate_environment():
    """验证 UE5 环境"""
    from utils.ue_backend import UEEngineLocator
    
    # 检查引擎
    locator = UEEngineLocator()
    engines = locator.find_all_engines()
    if not engines:
        raise EnvironmentError("未找到 UE5 引擎安装")
    
    # 检查项目
    if not project_path.exists():
        raise FileNotFoundError(f"项目文件不存在: {project_path}")
    
    # 检查依赖
    required_tools = ["UBT", "UAT", "UnrealEditor"]
    for tool in required_tools:
        if not check_tool_exists(tool):
            raise EnvironmentError(f"缺少必要工具: {tool}")
    
    return True
```

#### 4. 性能分析
```python
import time
import cProfile
import pstats

def profile_build_process():
    """分析构建过程性能"""
    pr = cProfile.Profile()
    pr.enable()
    
    # 执行构建
    build_system.build_project(project_path)
    
    pr.disable()
    
    # 保存分析结果
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # 显示前20个最耗时的函数
    
    # 保存到文件
    stats.dump_stats('build_profile.prof')
```

#### 5. 内存使用监控
```python
import psutil
import os

def monitor_memory_usage():
    """监控内存使用情况"""
    process = psutil.Process(os.getpid())
    
    # 记录初始内存
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # 执行操作
    result = build_system.build_project(project_path)
    
    # 记录最终内存
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"内存使用: {initial_memory:.2f}MB -> {final_memory:.2f}MB")
    print(f"内存增量: {final_memory - initial_memory:.2f}MB")
    
    # 检查内存泄漏
    if final_memory - initial_memory > 500:  # 500MB 阈值
        print("警告: 可能的内存泄漏")
```

### 高级调试工具

#### 1. 交互式调试器
```python
import pdb

def debug_build_issue():
    """使用交互式调试器"""
    try:
        result = build_system.build_project(project_path)
        if not result["success"]:
            # 设置断点
            pdb.set_trace()
            analyze_build_error(result)
    except Exception as e:
        print(f"异常: {e}")
        pdb.post_mortem()
```

#### 2. 远程调试
```python
import debugpy

def setup_remote_debugging(port=5678):
    """设置远程调试"""
    debugpy.listen(port)
    print(f"等待调试器连接，端口: {port}")
    debugpy.wait_for_client()
    
    # 现在可以设置断点
    debugpy.breakpoint()
    
    # 执行需要调试的代码
    build_system.build_project(project_path)
```

#### 3. 单元测试
```python
import unittest
from core.build import BuildSystem

class TestBuildSystem(unittest.TestCase):
    """构建系统单元测试"""
    
    def setUp(self):
        self.build_system = BuildSystem(engine_path)
    
    def test_build_success(self):
        """测试成功构建"""
        result = self.build_system.build_project(project_path)
        self.assertTrue(result["success"])
    
    def test_clean_project(self):
        """测试项目清理"""
        result = self.build_system.clean_project(project_path)
        self.assertTrue(result["success"])
    
    def test_invalid_project(self):
        """测试无效项目处理"""
        invalid_path = Path("InvalidProject.uproject")
        with self.assertRaises(FileNotFoundError):
            self.build_system.build_project(invalid_path)

if __name__ == '__main__':
    unittest.main()
```

#### 4. 集成测试
```python
class TestFullPipeline(unittest.TestCase):
    """完整流水线集成测试"""
    
    def test_build_cook_package_pipeline(self):
        """测试构建-烹饪-打包完整流水线"""
        # 1. 构建
        build_result = build_system.build_project(project_path)
        self.assertTrue(build_result["success"])
        
        # 2. 烹饪
        cook_result = cook_manager.cook_content(cook_options)
        self.assertTrue(cook_result.success)
        
        # 3. 打包
        packaging_config = packaging_manager.create_packaging_config(
            platform=PackagingPlatform.WINDOWS
        )
        output_path = packaging_manager.package_project(packaging_config)
        self.assertTrue(output_path.exists())
        
        # 4. 验证
        self.assertGreater(len(list(output_path.rglob("*"))), 0)
```

## 总结

UE5-CLIANY 模块为 Unreal Engine 5 提供了强大的命令行接口和自动化能力。通过本文档，您可以：

1. **快速上手**: 了解模块架构和基本用法
2. **深入开发**: 掌握所有 API 接口和配置选项
3. **解决问题**: 使用故障排除指南和调试技巧
4. **优化性能**: 应用最佳实践和性能优化建议

### 下一步
- 查看 `examples/` 目录中的完整示例
- 参与社区讨论和贡献代码
- 报告问题和功能请求

### 支持
- **文档**: [https://docs.ue5cliany.org](https://docs.ue5cliany.org)
- **GitHub**: [https://github.com/your-org/ue5-cliany](https://github.com/your-org/ue5-cliany)
- **Discord**: [https://discord.gg/ue5cliany](https://discord.gg/ue5cliany)

---
*文档版本: 1.0.0 | 最后更新: 2026-03-15 | UE5-CLIANY 项目团队*

