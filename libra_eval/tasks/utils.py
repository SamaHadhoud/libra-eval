import json
import re

_OPTION_LINE = re.compile(r'^\s*([A-Z])\.\s', re.MULTILINE)


def option_letters(content):
    """Return the option letters (e.g. ['A','B','C','D']) present in a
    multiple-choice prompt, parsed from the 'A. ...' / 'B. ...' lines."""
    return _OPTION_LINE.findall(str(content))


def extract_choice_letter(response, choices=("A", "B")):
    """Extract the multiple-choice letter the model actually selected.

    A naive substring test (`"A" in response`) is unreliable: models echo all
    option letters (e.g. "A. ...  B. ...") or narrate, so every letter is almost
    always present. We look, in priority order, for (1) an explicit answer marker
    ("answer: A", "the correct option is B"), last match wins, (2) a line that is
    just the letter, (3) the last standalone letter token. The option letter is
    captured case-sensitively (uppercase, as shown in the prompt) so the English
    article "a" is never mistaken for choice "A". Returns the letter or None.
    """
    text = str(response).strip()
    if not text:
        return None
    pat = "|".join(choices)

    marks = re.findall(
        rf'(?i:answer|choice|option|select|pick|correct)\b[^A-Za-z0-9]{{0,12}}\b({pat})\b',
        text,
    )
    if marks:
        return marks[-1]

    for ln in reversed(text.splitlines()):
        m = re.fullmatch(rf'[^A-Za-z0-9]*({pat})[^A-Za-z0-9]*', ln.strip())
        if m:
            return m.group(1)

    toks = re.findall(rf'(?<![A-Za-z])({pat})(?![A-Za-z])', text)
    if toks:
        return toks[-1]

    return None


def parse_yes_no(response):
    """Extract a yes/no answer from a (possibly verbose) model response.

    Returns True for yes, False for no, or None if neither is found. Uses the
    last standalone 'yes'/'no' token, which is typically the final answer when a
    model reasons before answering.
    """
    text = str(response).lower()
    yes = list(re.finditer(r'\byes\b', text))
    no = list(re.finditer(r'\bno\b', text))
    if not yes and not no:
        return None
    last_yes = yes[-1].start() if yes else -1
    last_no = no[-1].start() if no else -1
    return last_yes > last_no

def clean_invalid_chars(df):
    return df.map(
        lambda x: x.encode("utf-8", "ignore").decode("utf-8") if isinstance(x, str) else x
    )

def is_valid_json(r):
    try:
        # 如果已经是字典格式，直接返回
        # If it is already a dict, return it directly
        if isinstance(r, dict):
            return r

        # 如果是字符串，尝试多种解析方式
        # If it is a string, try multiple parsing approaches
        if isinstance(r, str):
            # 方法1: 处理markdown代码块
            # Method 1: handle markdown code blocks
            if r.startswith("```json") and r.endswith("```"):
                r = r[7:-3].strip()
            elif "```json" in r:
                # 提取markdown代码块中的内容
                # Extract the content inside the markdown code block
                match = re.search(r'```json\s*(.*?)\s*```', r, re.DOTALL)
                if match:
                    r = match.group(1).strip()

            # 方法2: 尝试直接解析
            # Method 2: try parsing directly
            try:
                json_r = json.loads(r)
                return json_r
            except json.JSONDecodeError:
                pass

            # 方法3: 提取第一个JSON对象或数组
            # Method 3: extract the first JSON object or array
            # 匹配 {...} 或 [...]
            # Match {...} or [...]
            json_pattern = r'(\{(?:[^{}]|(?:\{[^{}]*\}))*\}|\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\])'
            match = re.search(json_pattern, r, re.DOTALL)
            if match:
                json_str = match.group(1)
                json_r = json.loads(json_str)
                return json_r

        # 其他类型，尝试转换为字符串再解析
        # Other types: try converting to a string and parsing
        json_r = json.loads(str(r))
        return json_r
    except Exception as e:
        print(f"Not valid JSON: {r}")
        print(f"Error: {e}")
        return False
