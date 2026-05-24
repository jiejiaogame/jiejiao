# heroes.py
import os
import importlib.util

def load_all_heroes():
    heroes = {}
    heroes_dir = os.path.join(os.path.dirname(__file__), "data", "heroes")
    if not os.path.exists(heroes_dir):
        print(f"警告: heroes目录不存在: {heroes_dir}")
        return heroes
    for filename in os.listdir(heroes_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            name = filename[:-3]
            try:
                spec = importlib.util.spec_from_file_location(f"data.heroes.{name}", os.path.join(heroes_dir, filename))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'hero'):
                    heroes[name] = module.hero
                    print(f"成功加载武将: {name}")
                else:
                    print(f"警告: {filename} 没有 hero 字典")
            except Exception as e:
                print(f"加载武将 {filename} 失败: {e}")
    if not heroes:
        print("错误: 没有加载到任何武将！")
    return heroes

def get_hero(name):
    heroes = load_all_heroes()
    return heroes.get(name)

# 预加载一次
heroes = load_all_heroes()