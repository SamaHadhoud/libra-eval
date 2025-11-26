import json
import re

def clean_invalid_chars(df):
    return df.map(
        lambda x: x.encode("utf-8", "ignore").decode("utf-8") if isinstance(x, str) else x
    )

def is_valid_json(r):
    try:
        # 如果已经是字典格式，直接返回
        if isinstance(r, dict):
            return r

        # 如果是字符串，尝试多种解析方式
        if isinstance(r, str):
            # 方法1: 处理markdown代码块
            if r.startswith("```json") and r.endswith("```"):
                r = r[7:-3].strip()
            elif "```json" in r:
                # 提取markdown代码块中的内容
                match = re.search(r'```json\s*(.*?)\s*```', r, re.DOTALL)
                if match:
                    r = match.group(1).strip()

            # 方法2: 尝试直接解析
            try:
                json_r = json.loads(r)
                return json_r
            except json.JSONDecodeError:
                pass

            # 方法3: 提取第一个JSON对象或数组
            # 匹配 {...} 或 [...]
            json_pattern = r'(\{(?:[^{}]|(?:\{[^{}]*\}))*\}|\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\])'
            match = re.search(json_pattern, r, re.DOTALL)
            if match:
                json_str = match.group(1)
                json_r = json.loads(json_str)
                return json_r

        # 其他类型，尝试转换为字符串再解析
        json_r = json.loads(str(r))
        return json_r
    except Exception as e:
        print(f"Not valid JSON: {r}")
        print(f"Error: {e}")
        return False
