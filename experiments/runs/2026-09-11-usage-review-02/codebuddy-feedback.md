独立验收失败：normalize_tags(" a，b,a ") 应返回 ["a","b"]，当前未拆中文逗号。请补齐原需求，只修改 tags.py；保留英文逗号、大小写敏感、去空白、去空项、按首次出现去重。运行原验收及该失败样例，报告实际结果。
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    from tags import normalize_tags; assert normalize_tags(" a，b,a ")==["a","b"]
                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
