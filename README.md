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

打开`iwh.conf`，填入正确的`username`和`password`，必要的话可以更改`daily_hours`参数。

## 如何使用

运行以下命令，从服务器拉取项目参数:

```python
python iwh.py init
```

生成`projects.json`文件包含如下信息，请打开`projects.json`文件，修改每个项目中`hours`字段，填入正确的小时数(默认8小时)。

当`projects.json`成功生成后，运行`python iwh.py run`可以提交当天的工作量。

## 还有？

该程序可以自动检测当前日期是否为工作日，所以，如果有一台24小时运行的linux，或者路由器，或者...等，就可以使用`crontab`来自动化运行了，比如:

```
PYTHONIOENCODING=UTF-8
LANG=en_US.UTF-8
LC_ALL=en_US.UTF-8
# execute iwh on 9am, every day
0 9 * * * python path-to-iwh.py run
```

别忘了添加前三行，很重要。