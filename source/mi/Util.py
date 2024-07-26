import re
def validate_title(title):
    rstr = r'[\/\\\:\*\?\"\<\>\|]'  # 把不能做文件名的字符处理下
    new_title = title
    try:
        new_title = re.sub(rstr, "_", title)  # 替换为下划线
    except Exception as e:
        print(title)
    return new_title
