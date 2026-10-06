# spell

一小套拼写建议内核：编辑距离计算，以及按距离组织词条的 BK 树字典。
树支持存词、查词、列出全部词，按查询词给出阈值内的候选建议，并可对整个
词表一次性取建议。内核只用 Python 标准库，结果只取决于词与查询本身，
不做任何 I/O，也不依赖随机数。

## 目录

- spell/core.py 建议内核（edit_distance、BKTree、suggest）
- tests/test_core.py 行为测试

## 运行测试

在项目根目录（本文件所在目录）执行：

    python3 -m unittest discover -s tests -v

全部用例通过时进程退出码为 0。若系统里没有 `python3`，把命令里的 `python3` 换成
`python` 即可（Windows 上常见）。
