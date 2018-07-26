# 自动填写iEMS工作量脚本

## pre-requirements

* python 3.x
* pip

## 初始化

```python
pip install -r requirements.txt
```

## 关于`iwh.conf`

请复制`iwh.conf.example`并重命名为`iwh.conf`:

```
cp iwh.conf.example iwh.conf
```

打开`iwh.conf`，填入正确的`username`和`password`，必要的话可以更改`dailyHours`参数

## 如何使用

运行以下命令:

```python
python iwh.conf
```

首次执行，将生成`projects.json`文件：

1. 如果当前拥有的合同数超过**1**个，则程序在生成`projects.json`后退出，请打开`projects.json`文件，修改每个项目中`Hours`字段，填入正确的小时数
2. 如果当前拥有的合同数为1个，则程序在生成`projects.json`后立即开始提交工作量，默认的小时数为**8**小时，该配置也可以`projects.json`中更改

## 还有？

该程序可以自动检测当前日期是否为工作日，所以，如果有一台24小时运行的linux，或者路由器，或者...等，就可以使用`crontab`来自动化运行了，比如:

```
PYTHONIOENCODING=UTF-8
LANG=zh_CN.UTF-8
LC_ALL=zh_CN.UTF-8
# execute iwh on 9am, every day
0 9 * * * python path-to-iwh.py
```

别忘了添加前三行，很重要。